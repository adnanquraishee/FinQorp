import streamlit as st # Import Streamlit for caching
import yfinance as yf
import pandas as pd
from GoogleNews import GoogleNews
import requests
from bs4 import BeautifulSoup
# NOTE: The get_ticker_from_name function has been moved to ticker_resolver.py

# ------------------------------------------------------------
# ✅ STOCK DATA FETCH
# ------------------------------------------------------------

def resolve_ticker(query: str) -> str:
    """Resolve user query to a valid ticker symbol."""
    return query.strip().upper()


def get_price_history(ticker: str, period: str = "24mo", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch and clean historical stock price data using yfinance.

    Returns
    -------
    pd.DataFrame
        Clean DataFrame with DatetimeIndex and numeric columns.
    """
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval)

        if hist.empty:
            return pd.DataFrame()

        # Ensure DatetimeIndex
        hist.reset_index(inplace=True)
        hist['Date'] = pd.to_datetime(hist['Date']).dt.strftime('%Y-%m-%d')
        hist.set_index('Date', inplace=True)

        # Keep relevant numeric columns
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        cols_to_use = [col for col in numeric_cols if col in hist.columns]
        hist = hist[cols_to_use]

        # Remove duplicates & ensure numeric
        hist = hist.apply(pd.to_numeric, errors='coerce').dropna()

        return hist

    except Exception as e:
        print(f"Error in get_price_history: {e}")
        return pd.DataFrame()


# ------------------------------------------------------------
# ✅ COMPANY FINANCIALS FETCH
# ------------------------------------------------------------

def get_financials(ticker: str):
    """Fetch company financials using yfinance."""
    try:
        t = yf.Ticker(ticker)
        fin = t.financials
        if fin is not None and not fin.empty:
            return fin
        else:
            return None
    except Exception as e:
        return None


# ------------------------------------------------------------
# ✅ NEWS HEADLINES FETCH (MODIFIED)
# ------------------------------------------------------------

@st.cache_data(ttl=900) # --- MODIFICATION: Cache news for 15 minutes ---
def get_headlines(topic: str = None, limit: int = 20):
    """
    Fetch latest Google News headlines.
    Cleans up empty, duplicate, or invalid results.
    Tries GoogleNews → falls back to Google RSS feed.
    """
    headlines = []

    # --- Primary: GoogleNews package ---
    try:
        gn = GoogleNews(lang='en', region='IN')
        search_query = topic if topic else "Business"
        gn.search(search_query)
        results = gn.result()[:limit]

        if results:
            for item in results:
                title = item.get("title", "").strip()
                link = item.get("link", "#").strip()

                if (
                    not title
                    or title.lower().startswith("http")
                    or "..." in title
                    or len(title) < 5
                ):
                    continue

                headlines.append({"title": title, "link": link})

            # ✅ Remove duplicates safely
            unique_titles = set()
            clean_headlines = []
            for h in headlines:
                if h["title"] not in unique_titles:
                    unique_titles.add(h["title"])
                    clean_headlines.append(h)

            return clean_headlines
        else:
            pass # Continue to fallback
    except Exception as e:
        pass # Continue to fallback

    # --- Fallback: Google News RSS ---
    try:
        topic_query = topic.replace(" ", "+") if topic else "Business"
        topic_url = f"https://news.google.com/rss/search?q={topic_query}"
        response = requests.get(topic_url, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")
            for item in items[:limit]:
                title = item.title.text.strip()
                link = item.link.text.strip()

                if (
                    not title
                    or title.lower().startswith("http")
                    or "..." in title
                    or len(title) < 5
                ):
                    continue

                headlines.append({"title": title, "link": link})

            # Remove duplicates again (in case of overlap)
            unique_titles = set()
            clean_headlines = []
            for h in headlines:
                if h["title"] not in unique_titles:
                    unique_titles.add(h["title"])
                    clean_headlines.append(h)

            return clean_headlines
        else:
            pass
    except Exception as e:
        pass

    return []


# ------------------------------------------------------------
# ✅ WRAPPER FUNCTION FOR APP
# ------------------------------------------------------------

def get_stock_data(symbol: str, period: str = "2y", interval: str = "1d"):
    """
    Wrapper for app.py → fetches clean, ready-to-train stock data.
    """
    ticker = resolve_ticker(symbol)
    data = get_price_history(ticker, period=period, interval=interval)
    return data

# ------------------------------------------------------------
# ✅ MARKET DATA FUNCTION
# ------------------------------------------------------------

@st.cache_data(ttl=900) # Cache for 15 minutes
def get_market_data(tickers: list):
    """
    Fetches 2-day data for a list of tickers to get current price and % change.
    """
    try:
        data = yf.download(tickers, period="5d", interval="1d", auto_adjust=True)
        if data.empty:
            return {}
            
        close_data = data['Close']
        if len(close_data) < 2:
            return {} 
            
        latest_price = close_data.iloc[-1]
        prev_price = close_data.iloc[-2]
        
        pct_change = ((latest_price - prev_price) / prev_price) * 100
        
        market_data = {}
        if isinstance(latest_price, pd.Series):
            for ticker in tickers:
                if ticker in latest_price and ticker in pct_change:
                    market_data[ticker] = {
                        "price": latest_price[ticker],
                        "change": pct_change[ticker]
                    }
        else: 
            ticker = tickers[0]
            market_data[ticker] = {
                "price": latest_price,
                "change": pct_change
            }

        return market_data
    except Exception as e:
        print(f"Error in get_market_data: {e}")
        return {}