import streamlit as st
import yfinance as yf
import pandas as pd

# Map for Nifty 50 tickers to their names
NIFTY_50_MAP = {
    "RELIANCE.NS": "Reliance Industries", "TCS.NS": "Tata Consultancy", "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank", "INFY.NS": "Infosys", "BHARTIARTL.NS": "Bharti Airtel",
    "SBIN.NS": "State Bank of India", "HINDUNILVR.NS": "Hindustan Unilever", "LTIM.NS": "LTIMindtree",
    "BAJFINANCE.NS": "Bajaj Finance", "LT.NS": "Larsen & Toubro", "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "ITC.NS": "ITC Ltd.", "WIPRO.NS": "Wipro", "NTPC.NS": "NTPC", "HCLTECH.NS": "HCL Technologies",
    "ONGC.NS": "ONGC", "POWERGRID.NS": "Power Grid Corp.", "AXISBANK.NS": "Axis Bank",
    "TATAMOTORS.NS": "Tata Motors", "ADANIENT.NS": "Adani Enterprises", "TATASTEEL.NS": "Tata Steel",
    "MARUTI.NS": "Maruti Suzuki", "SUNPHARMA.NS": "Sun Pharma", "ULTRACEMCO.NS": "UltraTech Cement",
    "ADANIPORTS.NS": "Adani Ports", "COALINDIA.NS": "Coal India", "BAJAJFINSV.NS": "Bajaj Finserv",
    "NESTLEIND.NS": "Nestle India", "TECHM.NS": "Tech Mahindra", "GRASIM.NS": "Grasim Industries",
    "M&M.NS": "Mahindra & Mahindra", "ASIANPAINT.NS": "Asian Paints", "TITAN.NS": "Titan",
    "JSWSTEEL.NS": "JSW Steel", "INDUSINDBK.NS": "IndusInd Bank", "HINDALCO.NS": "Hindalco",
    "DRREDDY.NS": "Dr. Reddy's Labs", "CIPLA.NS": "Cipla", "SBILIFE.NS": "SBI Life Insurance",
    "BPCL.NS": "BPCL", "EICHERMOT.NS": "Eicher Motors", "DIVISLAB.NS": "Divi's Labs",
    "SHREECEM.NS": "Shree Cement", "TATACONSUM.NS": "Tata Consumer", "HDFCLIFE.NS": "HDFC Life",
    "BRITANNIA.NS": "Britannia", "HEROMOTOCO.NS": "Hero MotoCorp", "APOLLOHOSP.NS": "Apollo Hospitals"
}
NIFTY_50_TICKERS = list(NIFTY_50_MAP.keys())

# List of prominent US stocks to act as a proxy for US market movers
US_MOVERS_MAP = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet (Google)", "AMZN": "Amazon",
    "NVDA": "Nvidia", "TSLA": "Tesla", "META": "Meta Platforms", "BRK-B": "Berkshire Hathaway",
    "JPM": "JPMorgan Chase", "JNJ": "Johnson & Johnson", "XOM": "Exxon Mobil", "V": "Visa",
    "PG": "Procter & Gamble", "LLY": "Eli Lilly", "MA": "Mastercard", "UNH": "UnitedHealth Group",
    "HD": "Home Depot", "ORCL": "Oracle", "CRM": "Salesforce", "AMD": "AMD",
    "NFLX": "Netflix", "DIS": "Disney", "WMT": "Walmart", "BAC": "Bank of America",
    "PFE": "Pfizer", "KO": "Coca-Cola", "PEP": "PepsiCo", "MCD": "McDonald's", "COST": "Costco"
}
US_MOVERS_TICKERS = list(US_MOVERS_MAP.keys())


def _calculate_movers(ticker_list, name_map):
    """Helper function to download data and find top/bottom 5 movers."""
    try:
        data = yf.download(ticker_list, period="2d", interval="1d", progress=False)
        if data.empty:
            return [], []

        close_data = data['Close']
        if len(close_data) < 2:
            return [], []

        latest_price = close_data.iloc[-1]
        prev_price = close_data.iloc[-2]
        pct_change = ((latest_price - prev_price) / prev_price) * 100
        
        df = pd.DataFrame({'price': latest_price, 'change': pct_change}).dropna()
        df_sorted = df.sort_values(by='change', ascending=False)
        
        gainers_df = df_sorted.head(5)
        losers_df = df_sorted.tail(5).sort_values(by='change', ascending=True)
        
        gainers_list = [{"name": name_map.get(ticker, ticker), "price": row['price'], "change": row['change']} for ticker, row in gainers_df.iterrows()]
        losers_list = [{"name": name_map.get(ticker, ticker), "price": row['price'], "change": row['change']} for ticker, row in losers_df.iterrows()]
        
        return gainers_list, losers_list
    except Exception as e:
        print(f"Error in _calculate_movers: {e}")
        return [], []

@st.cache_data(ttl=900) # Cache for 15 minutes
def get_nifty50_movers():
    """Fetches top 5 Nifty 50 gainers and losers."""
    return _calculate_movers(NIFTY_50_TICKERS, NIFTY_50_MAP)

@st.cache_data(ttl=900) # Cache for 15 minutes
def get_us_movers():
    """Fetches top 5 US market gainers and losers from a proxy list."""
    return _calculate_movers(US_MOVERS_TICKERS, US_MOVERS_MAP)