import sys
import os

# Add the current directory to sys.path so we can import modules
sys.path.append(os.getcwd())

from modules import fundamentals

def test_ticker(ticker):
    print(f"Testing ticker: {ticker}")
    try:
        metrics, figs, profile = fundamentals.get_fundamentals(ticker)
        print("Metrics:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
        
        print("\nProfile:")
        for k, v in profile.items():
            print(f"  {k}: {v}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ticker("AAPL")
    test_ticker("RELIANCE.NS") # Test an Indian ticker as well since the app seems to support it
