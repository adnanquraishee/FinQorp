import yfinance as yf
import pandas as pd

# Test the exact tickers used in the market overview
indices = ['^NSEI', '^BSESN', '^GSPC', '^IXIC', 'GC=F', 'CL=F', 'INR=X', 'EURUSD=X']

print("Testing FIXED market data fetch...")
print("=" * 60)

try:
    # Download more days to handle market closures
    data = yf.download(indices, period="10d", interval="1d", auto_adjust=True, progress=False)
    if data.empty:
        print("Data is empty!")
    
    close_data = data['Close']
    if len(close_data) < 2:
        print("Not enough data rows")
    
    market_data = {}
    
    # Handle multiple tickers
    if isinstance(close_data, pd.DataFrame):
        for ticker in indices:
            if ticker not in close_data.columns:
                print(f"{ticker} not in columns")
                continue
                
            # Get the ticker's price series and drop NaN values
            ticker_prices = close_data[ticker].dropna()
            
            print(f"\n{ticker}:")
            print(f"  Valid prices: {len(ticker_prices)}")
            if len(ticker_prices) >= 2:
                latest_price = ticker_prices.iloc[-1]
                prev_price = ticker_prices.iloc[-2]
                pct_change = ((latest_price - prev_price) / prev_price) * 100
                
                market_data[ticker] = {
                    "price": latest_price,
                    "change": pct_change
                }
                print(f"  Latest: {latest_price:.2f}")
                print(f"  Previous: {prev_price:.2f}")
                print(f"  Change: {pct_change:.2f}%")
            else:
                print(f"  Not enough valid prices")
    
    print("\n" + "=" * 60)
    print("FINAL MARKET DATA:")
    print("=" * 60)
    
    index_names = {
        '^NSEI': 'NIFTY 50', '^BSESN': 'SENSEX', 
        '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ',
        'GC=F': 'Gold', 'CL=F': 'Crude Oil',
        'INR=X': 'USD/INR', 'EURUSD=X': 'EUR/USD'
    }
    
    for ticker in indices:
        name = index_names.get(ticker, ticker)
        data = market_data.get(ticker)
        if data:
            print(f"{name:15s}: ${data['price']:>10,.2f}  ({data['change']:>6.2f}%)")
        else:
            print(f"{name:15s}: No data")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
