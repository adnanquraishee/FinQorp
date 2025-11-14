import streamlit as st
import matplotlib.pyplot as plt
# All custom modules must be present in the project directory
from modules import data_fetch, sentiment, forecast, fundamentals, insights, compare, recommendation, ticker_resolver
import traceback, base64, os
import pandas as pd
import numpy as np
import plotly.graph_objects as go 

# --- CONFIGURATION AND STYLING ---
st.set_page_config(page_title="Financial Analysis Dashboard", layout="wide")

# Function to load custom CSS
def load_css(file_name):
    try:
        # Load CSS content from a separate file
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("CSS file not found. Styles may be missing. Ensure 'style.css' is in the main directory.")

# Load custom CSS
load_css('style.css') 

# Get Base64 Logo (Assuming finqorp_logo.png is in the same directory)
def get_base64_logo(path):
    # NOTE: Replace 'finqorp_logo.png' with your actual logo path or use a placeholder base64 string
    if not os.path.exists(path): return ""
    with open(path,"rb") as f: return base64.b64encode(f.read()).decode("utf-8")
    
# Using a placeholder image for demonstration since the file cannot be included
# Replace this string with the actual base64 logo if needed.
logo_placeholder_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
logo = get_base64_logo("finqorp_logo.png") or logo_placeholder_base64


# Initialize Session State
if 'ticker' not in st.session_state:
    st.session_state.ticker = None
if 'page' not in st.session_state:
    st.session_state.page = 'profile'
if 'analysis_ready' not in st.session_state:
    st.session_state.analysis_ready = False
if 'show_disambiguation' not in st.session_state:
    st.session_state.show_disambiguation = False 
if 'ticker_options' not in st.session_state:
    st.session_state.ticker_options = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""


# --- 1. CORE NAVIGATION FUNCTIONS ---

def set_page(page_name):
    st.session_state.page = page_name

def set_analysis_ticker(ticker_symbol):
    """
    Final step: Validates and sets the chosen ticker, then moves to the dashboard.
    """
    with st.spinner(f"Loading data for {ticker_symbol}..."):
        try:
            test_data = data_fetch.get_stock_data(ticker_symbol, period="1mo", interval="1d")
            if test_data.empty:
                 st.error(f"❌ No data found for symbol: **{ticker_symbol}**. Check symbol.")
                 return

            st.session_state.ticker = ticker_symbol
            st.session_state.analysis_ready = True 
            st.session_state.show_disambiguation = False 
            st.session_state.ticker_options = []
            st.session_state.page = 'profile'
        except Exception as e:
            st.error(f"❌ Critical Error during validation: {e}")
            print(f"Ticker validation error: {traceback.format_exc()}")

def navigate_to_analysis(input_company):
    """
    First step: User clicks "Analyze". This function finds options.
    """
    if not input_company:
        st.error("Please enter a company name or ticker to analyze.")
        return

    st.session_state.analysis_ready = False
    st.session_state.show_disambiguation = False
    st.session_state.last_query = input_company

    with st.spinner(f"Searching for '{input_company}'..."):
        try:
            options = ticker_resolver.find_ticker_options(input_company)
            
            if not options:
                st.error(f"❌ No stock market results found for: **{input_company}**. Please check the name.")
                return

            if len(options) == 1:
                set_analysis_ticker(options[0]['ticker'])
            
            else:
                st.session_state.ticker_options = options
                st.session_state.show_disambiguation = True

        except Exception as e:
            st.error(f"❌ Critical Error during search: {e}")
            print(f"Ticker search error: {traceback.format_exc()}")

# --- 2. HEADER AND GLOBAL INPUT ---

st.markdown(f"""
    <div class="header-container">
        <img src="data:image/png;base64,{logo}" class="header-logo" />
        <p class="header-subtitle">AI-DRIVEN MARKET INTELLIGENCE</p>
    </div>
    """, unsafe_allow_html=True)

# Global Ticker Input
col_input, col_button = st.columns([3, 1])
with col_input:
    initial_value = st.session_state.last_query if st.session_state.last_query else ""
    company_input = st.text_input("COMPANY/SYMBOL SEARCH", value=initial_value, 
                                  key="global_input", 
                                  placeholder="Enter Company Name or Ticker (e.g., Sony, BP, AAPL)...",
                                  label_visibility="collapsed")
with col_button:
    if st.button("Analyze", key="exec_scan", type="primary", use_container_width=True):
        navigate_to_analysis(company_input)


st.markdown("<br>", unsafe_allow_html=True)

# --- 3. PAGE CONTENT RENDERING (MODIFIED FLOW) ---

# --- BLOCK 1: Initial Welcome Page ---
if not st.session_state.analysis_ready and not st.session_state.show_disambiguation:
    st.markdown("""
        <div class="data-panel" style="text-align: center; margin-top: 50px;">
            <h2 style="color: #00BFFF;">Welcome</h2>
            <p>Please enter a company name or ticker symbol to begin analysis.</p>
        </div>
    """, unsafe_allow_html=True)

# --- BLOCK 2: NEW Disambiguation / Selection Box ---
elif st.session_state.show_disambiguation:
    st.markdown('<div class="data-panel" style="margin-top: 50px;">', unsafe_allow_html=True)
    st.subheader(f"Multiple Results Found for '{st.session_state.last_query}'")
    st.write("Please select the correct company and exchange to analyze:")
    
    st.markdown("---")
    
    for option in st.session_state.ticker_options:
        name = option.get('name', 'Unknown Name')
        ticker = option.get('ticker', 'N/A')
        exchange = option.get('exchange', 'Unknown Exchange')
        
        button_text = f"**{name}** ({ticker}) — *Exchange: {exchange}*"
        
        if st.button(button_text, key=ticker, use_container_width=True):
            set_analysis_ticker(ticker)
            st.rerun() 
            
    st.markdown("</div>", unsafe_allow_html=True)

# --- BLOCK 3: Main Dashboard (Analysis Ready) ---
elif st.session_state.analysis_ready:
    # --- Show Navigation Bar (Only after analysis is ready) ---
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    col_nav = st.columns(3)
    with col_nav[0]:
        if st.button("1. OVERVIEW & FUNDAMENTALS", use_container_width=True, key="nav_profile", type=('primary' if st.session_state.page == 'profile' else 'secondary')):
            set_page('profile')
    with col_nav[1]:
        if st.button("2. PEER COMPARISON", use_container_width=True, key="nav_compare", type=('primary' if st.session_state.page == 'compare' else 'secondary')):
            set_page('compare')
    with col_nav[2]:
        if st.button("3. FORECAST & RATINGS", use_container_width=True, key="nav_forecast", type=('primary' if st.session_state.page == 'forecast' else 'secondary')):
            set_page('forecast')
    st.markdown('</div>', unsafe_allow_html=True)


    # --- RENDER ANALYSIS PAGES (Wrapped in animated container) ---
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True) 

    # --- PAGE 1: Company Profile (MODIFIED ORDER & CONTENT) ---
    if st.session_state.page == 'profile':
        st.markdown('<div class="page-container">', unsafe_allow_html=True)
        
        ticker = st.session_state.ticker
        st.markdown(f"## SYMBOL: {ticker} | Overview & Fundamentals")
        
        with st.spinner(f"Loading data for {ticker}..."):
            # --- MODIFICATION: Unpack new profile_info dictionary ---
            metrics, figs, profile_info = fundamentals.get_fundamentals(ticker)
            
            if "Error" in metrics:
                st.error(f"Data Acquisition Failed: {metrics['Error']}")
                st.stop()

            # --- SECTION 1: Company Profile ---
            st.subheader("1. Company Profile")
            st.markdown('<div class="data-panel">', unsafe_allow_html=True)
            st.markdown(f"#### {profile_info.get('longName', ticker)}")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Sector:** `{profile_info.get('sector', 'N/A')}`")
                st.markdown(f"**Industry:** `{profile_info.get('industry', 'N/A')}`")
            with c2:
                st.markdown(f"**Website:** {profile_info.get('website', 'N/A')}")
                st.markdown(f"**Employees:** `{profile_info.get('employees', 'N/A')}`")
            st.markdown("---")
            st.markdown(f"**Business Summary:**\n> {profile_info.get('summary', 'N/A')}")
            st.markdown('</div>', unsafe_allow_html=True)

            # --- SECTION 2: Core Financials (MERGED) ---
            st.subheader("2. Core Financials")
            st.markdown('<div class="data-panel">', unsafe_allow_html=True)
            
            # --- LAYOUT FIX: Changed to 4 columns for a 4x3 grid ---
            cols_metrics = st.columns(4) 
            for i, (k, v) in enumerate(metrics.items()):
                with cols_metrics[i % 4]:
                    st.metric(k, v)
            st.markdown('</div>', unsafe_allow_html=True)

            # --- SECTION 3: Analyst Briefing (Header Changed) ---
            st.subheader("3. Analyst Briefing")
            st.markdown('<div class="data-panel">', unsafe_allow_html=True)
            # --- MODIFICATION: insights.py no longer passes metrics table ---
            st.markdown(insights.generate_ai_summary(ticker))
            st.markdown('</div>', unsafe_allow_html=True)

            # --- SECTION 4: Historical Performance ---
            st.subheader("4. Historical Performance")
            st.markdown('<div class="data-panel">', unsafe_allow_html=True)
            col_figs = st.columns(3)
            if figs:
                for i,(k,f) in enumerate(figs.items()):
                    with col_figs[i%3]:
                        st.pyplot(f)
            else:
                st.write("No financial trend charts available.")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # --- SECTION 5: 5-Day Price History ---
            st.subheader("5. Recent Price Action (Last 5 Days)")
            st.markdown('<div class="data-panel">', unsafe_allow_html=True)
            with st.spinner("Fetching recent price data..."):
                hist_5d = data_fetch.get_stock_data(ticker, period="5d", interval="1d")
                
                if not hist_5d.empty:
                    st.dataframe(hist_5d.style.format({
                        'Open': '{:,.2f}',
                        'High': '{:,.2f}',
                        'Low': '{:,.2f}',
                        'Close': '{:,.2f}',
                        'Volume': '{:,.0f}'
                    }), use_container_width=True)
                else:
                    st.warning("Could not retrieve 5-day price history.")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- PAGE 2: Comparative Analysis ---
    elif st.session_state.page == 'compare':
        st.markdown('<div class="page-container">', unsafe_allow_html=True)
        
        st.title("Peer Comparison Analysis")
        st.markdown("### Enter up to 5 Symbols (e.g., AAPL, MSFT, GOOG)")
        
        comp_input = st.text_input("COMPARISON LIST", 
                                   value=st.session_state.ticker + ", MSFT, GOOG" if st.session_state.ticker else "AAPL, MSFT, GOOG", 
                                   key="comp_list_input")
        
        symbols = [t.strip() for t in comp_input.split(",") if t.strip()]

        if st.button("Run Analysis", key="run_compare", type="primary"):
            with st.spinner("Executing comparative analysis..."):
                resolved_symbols = []
                for symbol in symbols:
                    options = ticker_resolver.find_ticker_options(symbol)
                    if options:
                        resolved_symbols.append(options[0]['ticker'])
                    else:
                        st.warning(f"Could not resolve '{symbol}', skipping.")
                    
                summary, df, fig = compare.compare_companies(resolved_symbols)
                
                st.subheader("Comparative Ratios")
                st.markdown('<div class="data-panel">', unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.subheader("Performance Chart")
                st.markdown('<div class="data-panel">', unsafe_allow_html=True)
                st.pyplot(fig)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.subheader("AI Comparative Insight")
                st.markdown('<div class="data-panel">', unsafe_allow_html=True)
                st.markdown(summary)
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
                
    # --- PAGE 3: Forecast and Recommendation ---
    elif st.session_state.page == 'forecast':
        st.markdown('<div class="page-container">', unsafe_allow_html=True)
        
        ticker = st.session_state.ticker
        st.title(f"SYMBOL: {ticker} | Forecast & Ratings") 
        
        with st.spinner("Generating predictive models and rating..."):
            stock = data_fetch.get_stock_data(ticker)

            st.subheader("1. Analyst & AI Rating")
            st.markdown('<div class="data-panel">', unsafe_allow_html=True)
            rec_text, rec_fig = recommendation.get_recommendation(ticker)
            st.markdown(rec_text)
            if rec_fig:
                st.plotly_chart(rec_fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.subheader("2. 30-Day Predictive Model")
            st.markdown('<div class="data-panel">', unsafe_allow_html=True)
            if stock is None or stock.empty:
                st.warning("⚠️ Cannot run forecast: Historical data acquisition failed.")
            else:
                df_hist, preds, fdates = forecast.generate_all_forecasts(stock)
                if preds:
                    fig = forecast.plot_forecasts_grid(df_hist, preds, fdates)
                    st.pyplot(fig)
                else:
                    st.warning("⚠️ Model generation failed.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # Close content-wrapper


# --- 5. FOOTER ---
st.markdown("---")
st.markdown("<div style='text_align:center;color:#667; font-size: 0.9em;'>© 2025 Finqorp Analytics | All data is for informational purposes. Not financial advice.</div>", unsafe_allow_html=True)