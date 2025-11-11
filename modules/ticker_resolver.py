# modules/ticker_resolver.py
import requests
import json
import yfinance as yf

# =============================================================
# ✅ FINAL UNIVERSAL TICKER RESOLUTION (Smart Validation + Clean Query)
# =============================================================

def resolve_ticker_from_name(company_name: str) -> str | None:
    """
    Uses the Yahoo Finance search API to find the best matching ticker for a given
    company name. It validates the resolved ticker by checking if the company's
    full name contains the user's input, ensuring relevance across all markets.

    Returns:
        str: The resolved ticker symbol (e.g., 'AAPL', 'BP.L', 'SIE.DE'), or None if not found.
    """
    
    input_upper = company_name.upper().strip()
    
    # --- Internal Query Cleaner (NEW FIX) ---
    # Simplifies ambiguous long names into cleaner search terms to guide the API.
    
    # 1. Define a list of known ambiguous long names
    search_cleaner = {
        "BRITISH PETROLEUM": "BP",  # Fixes the current issue
        "BANK OF AMERICA": "BAC",
        "JP MORGAN": "JPM",
        "TATA STEEL": "TATASTEEL.NS",
        "RELIANCE INDUSTRIES": "RELIANCE.NS",
        "GUJARAT ALKALIES CHEMICALS": "GUJALKALI.NS",
        "COAL INDIA LIMITED": "COALINDIA.NS",
    }
    
    # 2. Check if the input contains a known problematic phrase and use the clean search term
    search_query = company_name 
    input_no_space = input_upper.replace(" ", "")
    
    for phrase, clean_term in search_cleaner.items():
        if phrase.replace(" ", "") in input_no_space:
            search_query = clean_term
            break
        

    # --- Start Global Network Search ---
    try:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        url = f"https://query2.finance.yahoo.com/v1/finance/search"
        
        # Use the cleaned query
        params = {"q": search_query, "quotes_count": 5} 
        
        response = requests.get(url, params=params, headers={'User-Agent': user_agent})
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        results = data.get("quotes", [])
        
        # --- Post-Search Validation and Prioritization ---
        if results:
            equity_quotes = [r for r in results if r.get("exchDisp") and r.get("symbol") and ("EQ" in r.get("quoteType", "") or "STK" in r.get("quoteType", ""))]
            
            # Define priority exchanges
            us_exchanges = ["NYQ", "NMS", "NAS"]
            uk_eu_exchanges = ["LON", "LSE", "ETR", "EPA", "AMS", "VIE", "MIL"]
            india_exchanges = ["NSE", "BSE"]
            
            # Sort quotes by exchange priority (US > UK/EU > India > Others)
            def get_priority(quote):
                exchange = quote.get("exchange", "")
                if exchange in us_exchanges: return 4
                if exchange in uk_eu_exchanges: return 3
                if exchange in india_exchanges: return 2
                return 1

            equity_quotes.sort(key=get_priority, reverse=True)


            for quote in equity_quotes:
                ticker = quote["symbol"]
                
                # Fetch full company info for validation (Necessary for accuracy)
                try:
                    t_info = yf.Ticker(ticker).info
                    full_name = t_info.get("longName", "").upper()
                    
                    # 1. SMART VALIDATION: Check if the user's core input is reasonably contained within the returned company's full name.
                    core_input = input_upper.replace(" ", "").replace(".", "")
                    core_full_name = full_name.replace(" ", "").replace(".", "")
                    
                    if core_input in core_full_name or core_full_name in core_input:
                        return ticker
                    
                    # Special Case: Accept the clean ticker if the search term matched it exactly (e.g., if we searched "BP" and got "BP")
                    if ticker.upper() == search_query.upper():
                        return ticker
                         
                except Exception:
                    continue

            # 3. Fallback: If no smart match found, return the top raw result's symbol
            if equity_quotes:
                return equity_quotes[0]["symbol"]
            
    except Exception:
        pass
        
    return None