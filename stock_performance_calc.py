import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

from datetime import datetime, timedelta

import ftypes

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


def find_closest_date(index, target_date, max_days=5):
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

def calc_performance(holdings_df, stock_hist_df, end_date, periods):
    """
    Calculate stock performance over a specified period and store in holdings_df.
    
    Parameters:
    - end_date: End date for performance calculation (string or datetime).
    - periodMonths: Number of months to look back from end_date.
    
    Modifies:
    - holdings_df: Adds a new column 'R:Performance<X>m' with performance values.
    """

    for period in periods:
        # Convert end_date to datetime
        end_date = pd.to_datetime(end_date)
        
        # Calculate start date by subtracting periodMonths
        start_date = calculate_start_date(period, end_date)
        
        # Dictionary to store performance for each symbol
        performance_dict = {}
        
        # Iterate over unique symbols in holdings_df
        for symbol in holdings_df[ftypes.SpecialColumns.CYahooTicker.get_col_name()].unique():
            if symbol in stock_hist_df:
                # Get time series data for the symbol
                ts = stock_hist_df[symbol]
                
                # Find closest dates within ±5 days
                closest_start = find_closest_date(ts.index, start_date)
                closest_end = find_closest_date(ts.index, end_date)
                
                if (closest_start is None or 
                    closest_end is None or 
                    closest_start >= closest_end):
                    # Insufficient data or invalid date range
                    performance = np.nan
                else:
                    # Retrieve adjusted close prices
                    adjclose_start = ts.loc[closest_start, 'adjclose']
                    adjclose_end = ts.loc[closest_end, 'adjclose']
                    
                    # Calculate percentage performance, handle edge cases
                    if adjclose_start == 0:
                        performance = np.nan  # Avoid division by zero
                    else:
                        performance = (adjclose_end / adjclose_start - 1)
            else:
                # Symbol not in stock_hist_df
                performance = np.nan
            
            performance_dict[symbol] = performance
        
        # Create new column name and assign performance values
        col_name = f'R:Performance{period}'
        holdings_df[col_name] = holdings_df[ftypes.SpecialColumns.CYahooTicker.get_col_name()].map(performance_dict)
