import yfinance as yf
import pandas as pd
from datetime import datetime
import re
from typing import Optional, Dict
import requests

def find_stock_symbol(
    brokerage_symbol: str,
    exchange: Optional[str],
    company_description: str,
) -> Optional[str]:

    # Map common exchange codes to yfinance suffixes
    exchange_suffixes = {
        'TSE': '.TO',  # Toronto Stock Exchange
        'LSE': '.L',   # London Stock Exchange
        'ASX': '.AX',  # Australian Securities Exchange
        'HKEX': '.HK', # Hong Kong Stock Exchange
        'SSE': '.SS',  # Shanghai Stock Exchange
        'NSE': '.NS',  # National Stock Exchange of India
        # Add more exchanges as needed
    }

    # Construct possible symbols
    possible_symbols = []
    base_symbol = brokerage_symbol.replace('.', '').replace('-', '').upper()

    if exchange and exchange.upper() in exchange_suffixes:
        # Non-US exchange
        possible_symbols.append(f"{base_symbol}{exchange_suffixes[exchange.upper()]}")
    else:
        # US exchange or unspecified (try common US exchanges)
        possible_symbols.extend([
            base_symbol,              # NYSE/NASDAQ
            f"{base_symbol}.N",       # NYSE
            f"{base_symbol}.O"        # NASDAQ
        ])

    # Try to fetch data for each possible symbol
    candidates = []
    for symbol in possible_symbols:
        try:
            ticker = yf.Ticker(symbol)
            # Get historical data for the specific date
            hist = ticker.history(start=price_date, end=price_date + pd.Timedelta(days=1))
            
            if not hist.empty:
                # Get the closing price
                close_price = hist['Close'].iloc[0]
                
                # Convert price to USD if necessary
                if currency.upper() != 'USD':
                    try:
                        # Simple currency conversion using an external API (example: exchangerate-api)
                        response = requests.get(
                            f"https://api.exchangerate-api.com/v4/latest/{currency.upper()}"
                        )
                        rates = response.json()['rates']
                        usd_price = price / rates['USD']
                    except:
                        usd_price = price  # Fallback to original price if conversion fails
                else:
                    usd_price = price

                # Check if the price is reasonably close (within 5%)
                price_diff = abs(close_price - usd_price) / usd_price
                if price_diff <= 0.05:
                    # Verify company name
                    info = ticker.info
                    company_name = info.get('longName', '').upper()
                    if company_name and clean_description in company_name:
                        candidates.append((symbol, price_diff))
        except:
            continue

    # Return the best candidate (smallest price difference)
    if candidates:
        return min(candidates, key=lambda x: x[1])[0]
    
    return None

# Example usage
if __name__ == "__main__":
    # Example inputs
    test_cases = [
        {
            'brokerage_symbol': 'AAPL',
            'exchange': None,
            'company_description': 'APPLE INC',
            'price': 150.25,
            'currency': 'USD',
            'date': '2025-05-30'
        },
        {
            'brokerage_symbol': 'RY',
            'exchange': 'TSE',
            'company_description': 'ROYAL BANK OF CANADA',
            'price': 140.50,
            'currency': 'CAD',
            'date': '2025-05-30'
        },
        {
            'brokerage_symbol': 'INVALID',
            'exchange': None,
            'company_description': 'UNKNOWN COMPANY',
            'price': 100.00,
            'currency': 'USD',
            'date': '2025-05-30'
        }
    ]

    for case in test_cases:
        symbol = find_stock_symbol(
            case['brokerage_symbol'],
            case['exchange'],
            case['company_description'],
            case['price'],
            case['currency'],
            case['date']
        )
        print(f"Input: {case}")
        print(f"Found symbol: {symbol}\n")