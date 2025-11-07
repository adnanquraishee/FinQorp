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

                # ✅ Clean: remove blanks, weird URLs, or malformed titles
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

            print(f"✅ Found {len(clean_headlines)} clean headlines using GoogleNews.")
            return clean_headlines
        else:
            print("⚠️ GoogleNews returned no results.")
    except Exception as e:
        print(f"⚠️ GoogleNews failed: {e}")

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

            print(f"✅ Fallback RSS fetched {len(clean_headlines)} clean headlines.")
            return clean_headlines
        else:
            print(f"⚠️ RSS fetch failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️ RSS fallback failed: {e}")

    return []



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

