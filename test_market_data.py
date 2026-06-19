import yfinance as yf
import pandas as pd

# Test the exact tickers used in the market overview
indices = ['^NSEI', '^BSESN', '^GSPC', '^IXIC', 'GC=F', 'CL=F', 'INR=X', 'EURUSD=X']

print("Testing market data fetch...")
print("=" * 60)

try:
    data = yf.download(indices, period="5d", interval="1d", auto_adjust=True, progress=False)
    print("\nRaw data shape:", data.shape)
    print("\nData columns:", data.columns.tolist())
    
    if not data.empty:
        close_data = data['Close']
        print("\nClose data shape:", close_data.shape)
        print("\nClose data head:")
        print(close_data.head())
        print("\nClose data tail:")
        print(close_data.tail())
        
        if len(close_data) >= 2:
            latest_price = close_data.iloc[-1]
            prev_price = close_data.iloc[-2]
            
            print("\n\nLatest prices:")
            print(latest_price)
            print("\nPrevious prices:")
            print(prev_price)
            
            pct_change = ((latest_price - prev_price) / prev_price) * 100
            print("\nPercentage change:")
            print(pct_change)
            
            # Check for NaN values
            print("\n\nNaN check:")
            print("Latest price NaNs:", latest_price.isna().sum())
            print("Previous price NaNs:", prev_price.isna().sum())
            print("Pct change NaNs:", pct_change.isna().sum())
            
            # Display market data as it would appear
            print("\n\nFinal market data:")
            for ticker in indices:
                if ticker in latest_price and ticker in pct_change:
                    print(f"{ticker}: Price={latest_price[ticker]:.2f}, Change={pct_change[ticker]:.2f}%")
        else:
            print("Not enough data rows")
    else:
        print("Data is empty!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
