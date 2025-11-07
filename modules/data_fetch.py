import yfinance as yf
import pandas as pd
from GoogleNews import GoogleNews
import requests
from bs4 import BeautifulSoup

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
            print("⚠️ No data returned from yfinance.")
            return pd.DataFrame()

        # Ensure DatetimeIndex
        hist.reset_index(inplace=True)
        hist['Date'] = pd.to_datetime(hist['Date'])
        hist.set_index('Date', inplace=True)

        # Keep relevant numeric columns
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        hist = hist[numeric_cols].dropna()

        # Remove duplicates & ensure numeric
        hist = hist.apply(pd.to_numeric, errors='coerce').dropna()

        print(f"✅ Successfully fetched {len(hist)} rows for {ticker}.")
        return hist

    except Exception as e:
        print(f"⚠️ Error fetching price history for {ticker}: {e}")
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
            print(f"✅ Financials fetched for {ticker}.")
            return fin
        else:
            print(f"⚠️ No financials found for {ticker}.")
            return None
    except Exception as e:
        print(f"⚠️ Error fetching financials: {e}")
        return None


# ------------------------------------------------------------
# ✅ NEWS HEADLINES FETCH
# ------------------------------------------------------------

def get_headlines(topic: str = None, limit: int = 20):
    """
    Fetch latest Google News headlines.
    Tries GoogleNews library → falls back to Google RSS.
    """
    headlines = []

    # --- Try GoogleNews package ---
    try:
        gn = GoogleNews(lang='en', region='IN')
        search_query = topic if topic else "Business"
        gn.search(search_query)
        results = gn.result()[:limit]

        if results:
            for item in results:
                headlines.append({
                    "title": item.get("title", "No Title"),
                    "link": item.get("link", "#")
                })
            print(f"✅ Found {len(headlines)} headlines using GoogleNews.")
            return headlines
        else:
            print("⚠️ GoogleNews returned no results.")
    except Exception as e:
        print(f"⚠️ GoogleNews failed: {e}")

    # --- Fallback: Google News RSS ---
    try:
        topic_url = (
            f"https://news.google.com/rss/headlines/section/topic/{topic.upper()}"
            if topic else "https://news.google.com/rss"
        )
        response = requests.get(topic_url)
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")
            for item in items[:limit]:
                title = item.title.text.strip()
                link = item.link.text.strip()
                headlines.append({"title": title, "link": link})
            print(f"✅ Fallback RSS fetched {len(headlines)} headlines.")
        else:
            print(f"⚠️ RSS fetch failed with status code {response.status_code}")
    except Exception as e:
        print(f"⚠️ RSS fallback failed: {e}")

    return headlines


# ------------------------------------------------------------
# ✅ WRAPPER FUNCTION FOR APP
# ------------------------------------------------------------

def get_stock_data(symbol: str):
    """
    Wrapper for app.py → fetches clean, ready-to-train stock data.
    """
    ticker = resolve_ticker(symbol)
    data = get_price_history(ticker)
    return data

def get_ticker_from_name(company_name):
    """
    Use Yahoo Finance search API to find the ticker for a given company name.
    Returns the first matching ticker.
    """
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={company_name}"
        response = requests.get(url)
        results = response.json().get("quotes", [])
        if results:
            return results[0]["symbol"]
    except Exception as e:
        print("Ticker lookup error:", e)
    return None

