from yahooquery import Ticker
from pprint import pprint

#symbols = ['SURG.V', 'MHPC.L', 'YPF', '1088.HK']
symbols = ['VCIG','MULN']

stocks = Ticker(symbols,asynchronous=True)
#not found example: 'FDA.CVX': 'Quote not found for symbol: FDA.CVX',

pprint(stocks.summary_detail)


print("Stock history")

# period	Length of time	str	ytd	optional	['1d', '5d', '7d', '60d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
# interval	Time between data points	str	1d	optional	['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
df = stocks.history(period="1y",interval="1wk")

#prices are in the stock markets currency, but we can get the currency type from summary_detail[<stock>]['currency']
print(df.to_csv())

print("Stock corporate events")

df = stocks.corporate_events
#note: corporate_events doesn't contain split information

print(df.to_csv())
