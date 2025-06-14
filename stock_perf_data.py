import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

from datetime import datetime, timedelta

import ftypes
import util

import history_stock_downloader

def calculate_start_date(duration_str, end_date):
    # Parse the duration string
    number = int(duration_str[:-1])
    unit = duration_str[-1].lower()
    
    # Convert end_date to datetime if it's a string
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calculate start date based on unit
    if unit == 'w':
        start_date = end_date - timedelta(weeks=number)
    elif unit == 'm':
        start_date = end_date - relativedelta(months=number)
    elif unit == 'y':
        start_date = end_date - relativedelta(years=number)
    else:
        raise ValueError("Invalid duration unit. Use 'w' for weeks, 'm' for months, or 'y' for years.")
    
    return start_date


def find_closest_date(index, target_date, max_days):
    """
    Find the date in the index closest to target_date within max_days.
    
    Parameters:
    - index: DatetimeIndex of dates to search.
    - target_date: Target date to find the closest match for.
    - max_days: Maximum allowed difference in days (default is 5).
    
    Returns:
    - Closest date if within max_days, otherwise None.
    """
    start = target_date - pd.Timedelta(days=max_days)
    end = target_date + pd.Timedelta(days=max_days)
    candidates = index[(index >= start) & (index <= end)]
    if candidates.empty:
        return None
    else:
        diff = abs(candidates - target_date)
        return candidates[diff.argmin()]

def add_stock_perf_data_to_holdings_df(holdings_df, stock_hist_df, end_date, periods, max_slippage_days):
    """
    Adds the following columns to holdings_df:
      - R:AdjCloseStartPrice<Period> the yahoo adjusted close start price, which is repriced for dividend gains  
      - R:PriceStartDate<Period> the date used for the start price (may be different from the period start date if
            the date falls on the weekend or yahoo has no data for that date)
      - R:AdjCloseEndPrice<Period> the yahoo adjusted close start price, which is repriced for dividend gains  
      - R:PriceEndDate<Period> the date used for the end price (same restrictions apply as PriceStartDate)
    
    Parameters:
    - end_date: End date for performance calculation (string or datetime).
    - periodMonths: Number of months to look back from end_date.
    - max_slippage_days: Max number of days difference the actual price date can be from the requested price
         date before the result is considered invalid

    Returns:
      updated df
    """

    res_df = pd.DataFrame()

    # Convert end_date to datetime
    end_date = pd.to_datetime(end_date)

    # Iterate over unique symbols in holdings_df
    def update_holdings_row(row):
        yahoo_symbol = row[ftypes.SpecialColumns.CYahooTicker.get_col_name()]
        for period in periods:
            
            # Calculate start date by subtracting periodMonths
            start_date = calculate_start_date(period, end_date)
            
            if yahoo_symbol in stock_hist_df:
                # Get time series data for the symbol
                ts = stock_hist_df[yahoo_symbol]
                
                # Find closest dates within slippage days
                closest_start_date = find_closest_date(ts.index, start_date, max_slippage_days)
                closest_end_date = find_closest_date(ts.index, end_date, max_slippage_days)
                
                if (closest_start_date is None or 
                    closest_end_date is None or 
                    closest_start_date >= closest_end_date):
                    continue

                # Retrieve adjusted close prices
                adjclose_start_price = ts.loc[closest_start_date, 'adjclose']
                adjclose_end_price = ts.loc[closest_end_date, 'adjclose']

                row[f'R:AdjCloseStartPrice{period}'] = adjclose_start_price
                row[f'R:AdjCloseEndPrice{period}'] = adjclose_end_price

                row[f'R:PriceStartDate{period}'] = closest_start_date
                row[f'R:PriceEndDate{period}'] = closest_end_date

    holdings_df = holdings_df.apply(update_holdings_row,axis=1)

    return holdings_df


def calc_stock_history(cache_file,config,sub_dir_date,holdings_df):
    """Updates holdings_df and returns the result"""
    if(not config.hist_perf_periods):
        print("Historical performance periods not defined, not calculating performance")
        return

    min_start_date = sub_dir_date
    for perf_period in config.hist_perf_periods:
        num_periods = int(perf_period[:-1])
        period_type = perf_period[-1]

        start_date = util.find_start_date_for_period(num_periods,period_type,sub_dir_date)
        if(start_date < min_start_date):
            min_start_date = start_date

    # get a unique set of tickers. Since there may be multiple brokerages, there could also be multiple holdings,
    # so we have to remove duplicates
    symbols = list(set(holdings_df[holdings_df[ftypes.SpecialColumns.CYahooTicker.get_col_name()].notna()]
                         [ftypes.SpecialColumns.CYahooTicker.get_col_name()].tolist()))

    stock_hist_df = history_stock_downloader.download_stock_history(symbols,min_start_date,sub_dir_date,'1w',
                                                                    cache_file,8)
    
    return add_stock_perf_data_to_holdings_df(holdings_df, stock_hist_df, sub_dir_date, config.hist_perf_periods, config.max_slippage_days)
