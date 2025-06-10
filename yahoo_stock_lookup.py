import yfinance as yf

#def fetch_historical_data(holdings_df, intervals, hist_data_cache_df):

def search_yahoo_symbols(query: str, limit: int = 10):
    """
    Search for Yahoo Finance symbols using yfinance's built-in search.

    Args:
        query (str): A ticker symbol, company name, etc.
        limit (int): Max number of results to return.

    Returns:
        List[dict]: List of matching symbols with metadata.
    """
    results = yf.Search(query).search()
    return results

if __name__ == "__main__":

    # Example usage
    for r in search_yahoo_symbols("apple"):
        print(f"{r['symbol']} - {r['shortname']} ({r.get('exchDisp', 'N/A')})")
