from io import StringIO
import json
import os
import pandas as pd
from yahooquery import Ticker


#if a unknowned symbol is given to yahooquery, it just returns nothing. In this case, we need to store that nothing was returned in the cache.
NO_RESULTS = "No Results"

def download_stock_history(symbols, start_date, end_date, interval, cache_file, batch_size):
    """
    Download stock history for multiple stocks using yahooquery with caching and batch processing.

    Parameters:
    - symbols (list): List of stock ticker symbols (e.g., ['VCIG', 'MULN']).
    - start_date (str): Start date in 'YYYY-MM-DD' format. 
    - end_date (str): End date in 'YYYY-MM-DD' format.
    - interval (str): Time interval '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'
    - cache_file (str): Path to the JSON cache file.
    - batch_size (int): Number of stocks to fetch per batch.

    Returns:
    - dict: Dictionary mapping stock symbols to their historical data DataFrames.
    """
    # Load existing cache or initialize an empty one
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
        except Exception:
            cache = {}
    else:
        cache = {}

    # Dictionary to store results
    results = {}
    # List of symbols that need to be fetched
    symbols_to_fetch = []

    # Check cache for each symbol
    for symbol in symbols:
        # Create a unique key for this query
        key = f"{symbol}|{start_date}|{end_date}|{interval}"
        if key in cache:
            if(cache[key] == NO_RESULTS):
                results[symbol] = None
            else:
                # Use cached data if available
                results[symbol] = pd.read_json(StringIO(cache[key]))
        else:
            # Mark symbol for fetching
            symbols_to_fetch.append(symbol)

    # Process symbols that need fetching in batches
    for i in range(0, len(symbols_to_fetch), batch_size):
        batch = symbols_to_fetch[i:i + batch_size]
        # Fetch data asynchronously for the batch
        print(f"Fetching stocks for {batch}")
        stocks = Ticker(batch, timeout=120, asynchronous=True)
        print(f"Fetching stock histoy for {batch}")
        df = stocks.history(start=start_date, end=end_date, interval=interval)
        print(f"Done fetching stock histoy for {batch}")

        for symbol in batch:
            #if all the symbols failed to load, the df returned has no columns
            if(df.empty):
                cache_result = NO_RESULTS
                results[symbol] = None
            else:
                try:
                    symbol_rows = df.xs(symbol,level='symbol')
                    cache_result = symbol_rows.to_json()
                    results[symbol] = symbol_rows
                except KeyError:
                    cache_result = NO_RESULTS
                    results[symbol] = None

            key = f"{symbol}|{start_date}|{end_date}|{interval}"
            cache[key] = cache_result

    if(len(symbols_to_fetch) != 0):
        # Save updated cache
        with open(cache_file, 'w') as f:
            json.dump(cache, f)

    return results

# Example usage in a script with command-line argument for batch_size
if __name__ == "__main__":
    import argparse

    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Download stock history with caching.")
    parser.add_argument('--batch_size', type=int, default=2, help="Number of stocks to fetch per batch")
    args = parser.parse_args()

    # Example parameters
    symbols = ['VCIG', 'MULN','AMZN','INTC','TSLA','IBMC'] #note that IBMC doesn't exist
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    interval = '1wk'
    cache_file = 'stock_cache.json'

    # Call the function
    stock_data = download_stock_history(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        cache_file=cache_file,
        batch_size=args.batch_size
    )

    # Print results
    for symbol, df in stock_data.items():
        print(f"\nHistory for {symbol}:")
        print(df)