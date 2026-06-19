import yfinance as yf

t = yf.Ticker("AAPL")
info = t.info
print(f"Profit Margin: {info.get('profitMargins')}")
print(f"ROE: {info.get('returnOnEquity')}")
