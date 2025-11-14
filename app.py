import streamlit as st
import matplotlib.pyplot as plt
# All custom modules must be present in the project directory
from modules import data_fetch, sentiment, forecast, fundamentals, insights, compare, recommendation, ticker_resolver
# --- MODIFICATION: Import new 'technicals' module ---
from modules import technicals 
try:
    from modules import market_data
except ImportError:
    market_data = None # Handle if file was deleted
    
import traceback, base64, os
import pandas as pd
import numpy as np
import plotly.graph_objects as go 
from plotly.subplots import make_subplots # Import for subplots

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
    if not os.path.exists(path): return ""
    with open(path,"rb") as f: return base64.b64encode(f.read()).decode("utf-8")
    
logo_placeholder_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
logo = get_base64_logo("finqorp_logo.png") or logo_placeholder_base64


# Initialize Session State
if 'ticker' not in st.session_state:
    st.session_state.ticker = None
if 'page' not in st.session_state:
    st.session_state.page = 'market'
if 'analysis_ready' not in st.session_state:
    st.session_state.analysis_ready = False
if 'show_disambiguation' not in st.session_state:
    st.session_state.show_disambiguation = False 
if 'ticker_options' not in st.session_state:
    st.session_state.ticker_options = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'key_metrics' not in st.session_state:
    st.session_state.key_metrics = {}
if 'figs' not in st.session_state:
    st.session_state.figs = {}
    
if 'rec_text' not in st.session_state:
    st.session_state.rec_text = ""
if 'rec_fig' not in st.session_state:
    st.session_state.rec_fig = None
if 'forecast_fig' not in st.session_state:
    st.session_state.forecast_fig = None
if 'forecast_failed' not in st.session_state:
    st.session_state.forecast_failed = False


# --- 1. CORE NAVIGATION FUNCTIONS ---

def set_page(page_name):
    st.session_state.page = page_name

def set_analysis_ticker(ticker_symbol):
    """
    Final step: Validates, sets ticker, and pre-computes all analysis.
    """
    with st.spinner(f"Loading data for {ticker_symbol}..."):
        try:
            metrics, figs, profile_info = fundamentals.get_fundamentals(ticker_symbol)
            if "Error" in metrics:
                 st.error(f"❌ No data found for symbol: **{ticker_symbol}**. Check symbol.")
                 return

            # Store primary data
            st.session_state.ticker = ticker_symbol
            st.session_state.key_metrics = metrics
            st.session_state.figs = figs
            st.session_state.profile_info = profile_info
            
            st.session_state.analysis_ready = True 
            st.session_state.show_disambiguation = False 
            st.session_state.ticker_options = []
            st.session_state.page = 'overview' 
            
        except Exception as e:
            st.error(f"❌ Critical Error during validation: {e}")
            print(f"Ticker validation error: {traceback.format_exc()}")
            return
            
    with st.spinner(f"Generating forecasts and ratings for {ticker_symbol}..."):
        try:
            # 1. Get sentiment score
            _, _, sentiment_score = sentiment.analyze_sentiment(ticker_symbol)
            
            # 2. Generate forecast (for 30 days for rating, 90 for plot)
            hist_df_30d, simulations_30d, _ = forecast.generate_forecast(ticker_symbol, period=30, num_simulations=100)
            
            # 3. Generate recommendation
            rec_text, rec_fig = recommendation.get_recommendation(ticker_symbol, hist_df_30d, simulations_30d, sentiment_score)
            
            # 4. Generate the 90-day forecast plot
            hist_df_90d, simulations_90d, future_dates_90d = forecast.generate_forecast(ticker_symbol, period=90, num_simulations=100)
            forecast_fig = forecast.plot_forecast(hist_df_90d, simulations_90d, future_dates_90d, sentiment_score)
            
            # 5. Store everything in session state
            st.session_state.rec_text = rec_text
            st.session_state.rec_fig = rec_fig
            st.session_state.forecast_fig = forecast_fig
            st.session_state.forecast_failed = False
            
        except Exception as e:
            print(f"!! FAILED TO PRE-COMPUTE FORECASTS: {e}")
            st.session_state.forecast_failed = True # Log failure

def navigate_to_analysis(input_company):
    """
    First step: User clicks "Analyze". This function finds options.
    """
    if not input_company:
        st.error("Please enter a company name or ticker to analyze.")
        return

    # Reset all states
    st.session_state.analysis_ready = False
    st.session_state.show_disambiguation = False
    st.session_state.last_query = input_company
    st.session_state.key_metrics = {}
    st.session_state.profile_info = {}
    st.session_state.figs = {}
    st.session_state.rec_text = ""
    st.session_state.rec_fig = None
    st.session_state.forecast_fig = None
    st.session_state.forecast_failed = False

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

# --- 2. SIDEBAR IMPLEMENTATION ---

with st.sidebar:
    st.markdown(f"""
        <div class="sidebar-header">
            <img src="data:image/png;base64,{logo}" class="sidebar-logo" />
            <p>FINANCIAL ANALYSIS</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

    st.markdown("##### NAVIGATION")
    if st.button("Market Overview", use_container_width=True, type="primary" if st.session_state.page == 'market' else "secondary"):
        set_page('market')
    
    if st.button("Overview", use_container_width=True, type="primary" if st.session_state.page == 'overview' else "secondary", disabled=not st.session_state.analysis_ready):
        set_page('overview')
        
    if st.button("Technical Analysis", use_container_width=True, type="primary" if st.session_state.page == 'technical' else "secondary", disabled=not st.session_state.analysis_ready):
        set_page('technical')
        
    if st.button("Forecast & Ratings", use_container_width=True, type="primary" if st.session_state.page == 'forecast' else "secondary", disabled=not st.session_state.analysis_ready):
        set_page('forecast')
    if st.button("Peer Comparison", use_container_width=True, type="primary" if st.session_state.page == 'comparison' else "secondary", disabled=not st.session_state.analysis_ready):
        set_page('comparison')
    
    st.markdown("---")

    if st.session_state.analysis_ready:
        st.markdown(f"### {st.session_state.profile_info.get('longName', st.session_state.ticker)}")
        
        st.markdown(f"""
        <div class="metric-card">
            <span class="metric-label">Current Price</span>
            <span class="metric-value">{st.session_state.key_metrics.get('Current Price', 'N/A')}</span>
        </div>
        <div class="metric-card">
            <span class="metric-label">Market Cap</span>
            <span class="metric-value">{st.session_state.key_metrics.get('Market Cap', 'N/A')}</span>
        </div>
        <div class="metric-card">
            <span class="metric-label">P/E Ratio</span>
            <span class="metric-value">{st.session_state.key_metrics.get('P/E Ratio', 'N/A')}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Search for a company to begin analysis.")


# --- 3. MAIN CONTENT AREA ---

main_container = st.container()

with main_container:
    # --- BLOCK 1: Global Search Bar ---
    with st.form(key="search_form"):
        col_input, col_button = st.columns([3, 1])
        with col_input:
            initial_value = st.session_state.last_query if st.session_state.last_query else ""
            company_input = st.text_input("COMPANY/SYMBOL SEARCH", value=initial_value, 
                                          key="global_input", 
                                          placeholder="Enter Company Name or Ticker (e.g., Sony, BP, AAPL)...",
                                          label_visibility="collapsed")
        with col_button:
            analyze_button = st.form_submit_button("Analyze", type="primary", use_container_width=True)
    
    if analyze_button:
        navigate_to_analysis(company_input)
        
    st.markdown("<br>", unsafe_allow_html=True)

    # --- BLOCK 2: Disambiguation / Selection Box ---
    if st.session_state.show_disambiguation:
        st.markdown('<div class="panel" style="margin-top: 50px;">', unsafe_allow_html=True)
        st.subheader(f"Multiple Results Found for '{st.session_state.last_query}'")
        st.write("Please select the correct company and exchange to analyze:")
        st.markdown("---")
        
        for option in st.session_state.ticker_options:
            name, ticker, exchange = option.get('name'), option.get('ticker'), option.get('exchange')
            button_text = f"**{name}** ({ticker}) — *Exchange: {exchange}*"
            if st.button(button_text, key=ticker, use_container_width=True, type="secondary"):
                set_analysis_ticker(ticker)
                st.rerun() 
        st.markdown("</div>", unsafe_allow_html=True)

    # --- BLOCK 3: Main Dashboard (Analysis Ready) ---
    elif st.session_state.analysis_ready:
        
        ticker = st.session_state.ticker
        metrics = st.session_state.key_metrics
        profile_info = st.session_state.profile_info
        figs = st.session_state.figs # Load figs from session state

        # --- PAGE 1: Overview (K-Layout Dashboard) ---
        if st.session_state.page == 'overview':
            st.markdown(f"## {profile_info.get('longName', ticker)} ({ticker})")
            
            col_main, col_metrics = st.columns([2, 1])
            
            with col_main:
                # --- SECTION 1: ENHANCED INTERACTIVE CHART ---
                st.subheader("Interactive Stock Chart")
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                with st.spinner("Loading chart data..."):
                    chart_data = data_fetch.get_stock_data(ticker, period="2y", interval="1d")
                    if not chart_data.empty:
                        chart_data['MA50'] = chart_data['Close'].rolling(50).mean()
                        chart_data['MA200'] = chart_data['Close'].rolling(200).mean()
                        
                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                            vertical_spacing=0.05, 
                                            row_heights=[0.7, 0.3]) 

                        fig.add_trace(go.Candlestick(x=chart_data.index,
                                        open=chart_data['Open'],
                                        high=chart_data['High'],
                                        low=chart_data['Low'],
                                        close=chart_data['Close'], 
                                        name="Price",
                                        increasing_line_color='#1ED760', 
                                        decreasing_line_color='#D40000'),
                                        row=1, col=1)

                        fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['MA50'], 
                                                 line=dict(color='#FFC107', width=2), name="50-Day MA"),
                                                 row=1, col=1)
                        fig.add_trace(go.Scatter(x=chart_data.index, y=chart_data['MA200'], 
                                                 line=dict(color='#00FFFF', width=2), name="200-Day MA"),
                                                 row=1, col=1)

                        fig.add_trace(go.Bar(x=chart_data.index, y=chart_data['Volume'], 
                                             name="Volume", 
                                             marker_color='#0D6EFD',
                                             opacity=0.6),
                                             row=2, col=1)

                        fig.update_layout(
                            title=f"<b>{ticker} Price and Volume Analysis</b>",
                            title_font_color='#FFFFFF',
                            height=600,
                            xaxis_rangeslider_visible=False,
                            plot_bgcolor='#121A2A', 
                            paper_bgcolor='#121A2A', 
                            font_color='#E0E0E0',
                            hovermode="x unified",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='#E0E0E0')),
                            
                            xaxis=dict(
                                rangeslider=dict(visible=False), 
                                type="date",
                                showgrid=True, gridcolor='#30363D',
                                rangeselector=dict(
                                    buttons=list([
                                        dict(count=1, label="1m", step="month", stepmode="backward"),
                                        dict(count=3, label="3m", step="month", stepmode="backward"),
                                        dict(count=6, label="6m", step="month", stepmode="backward"),
                                        dict(count=1, label="1y", step="year", stepmode="backward"),
                                        dict(count=2, label="2y", step="year", stepmode="backward"),
                                        dict(step="all")
                                    ]),
                                    bgcolor='#1A2430',
                                    font=dict(color='#E0E0E0'),
                                    activecolor='#0D6EFD'
                                )
                            ),
                            xaxis2=dict(
                                showgrid=True, gridcolor='#30363D'
                            ),
                            yaxis=dict(
                                title='Price', 
                                showgrid=True, gridcolor='#30363D'
                            ),
                            yaxis2=dict(
                                title='Volume', 
                                showgrid=True, gridcolor='#30363D'
                            )
                        )
                        fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Could not load chart data.")
                st.markdown('</div>', unsafe_allow_html=True)

                # --- SECTION 2: Company Profile ---
                st.subheader("Company Profile")
                st.markdown('<div class="panel">', unsafe_allow_html=True)
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

                # --- SECTION 3: Analyst Briefing ---
                st.subheader("Analyst Briefing")
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown(insights.generate_ai_summary(ticker))
                st.markdown('</div>', unsafe_allow_html=True)

            with col_metrics:
                # --- SECTION 4: Core Financials (Metrics) ---
                st.subheader("Core Financials")
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                
                for k, v in metrics.items():
                    if k not in ["Current Price", "Market Cap", "P/E Ratio"]:
                        st.metric(k, v)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # --- SECTION 5: 5-Day Price History ---
                st.subheader("Recent Price Action")
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                with st.spinner("Fetching recent price data..."):
                    hist_5d = data_fetch.get_stock_data(ticker, period="5d", interval="1d")
                    if not hist_5d.empty:
                        st.dataframe(hist_5d.style.format({
                            'Open': '{:,.2f}','High': '{:,.2f}','Low': '{:,.2f}',
                            'Close': '{:,.2f}','Volume': '{:,.0f}'
                        }), use_container_width=True)
                    else:
                        st.warning("Could not retrieve 5-day price history.")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # --- SECTION 6: Historical Performance (Full Width) ---
            st.subheader("Historical Performance")
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            col_figs = st.columns(3)
            if figs:
                for i,(k,f) in enumerate(figs.items()):
                    with col_figs[i%3]:
                        st.pyplot(f)
            else:
                st.write("No financial trend charts available.")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- PAGE 2: Forecast and Recommendation ---
        elif st.session_state.page == 'forecast':
            st.title(f"SYMBOL: {ticker} | Forecast & Ratings") 
            
            st.subheader("1. Analyst & AI Rating")
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            if st.session_state.forecast_failed:
                st.error("Forecast and rating models failed to run during initialization.")
            else:
                st.markdown(st.session_state.rec_text)
                if st.session_state.rec_fig:
                    st.plotly_chart(st.session_state.rec_fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.subheader("2. 90-Day Price Forecast (Monte Carlo)")
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            if st.session_state.forecast_failed:
                st.error("Forecast models failed to run.")
            else:
                st.pyplot(st.session_state.forecast_fig)
            
            st.markdown('</div>', unsafe_allow_html=True)

        # --- PAGE 3: Comparative Analysis ---
        elif st.session_state.page == 'comparison':
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
                    st.markdown('<div class="panel">', unsafe_allow_html=True)
                    st.dataframe(df, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.subheader("Performance Chart")
                    st.markdown('<div class="panel">', unsafe_allow_html=True)
                    st.pyplot(fig)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.subheader("AI Comparative Insight")
                    st.markdown('<div class="panel">', unsafe_allow_html=True)
                    st.markdown(summary)
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # --- MODIFICATION: New Technical Analysis Page ---
        elif st.session_state.page == 'technical':
            st.title(f"SYMBOL: {ticker} | Technical Analysis")
            
            # --- MODIFICATION: Removed pandas_ta import ---
            
            with st.spinner("Calculating technical indicators..."):
                # Fetch 1 year of data
                df = data_fetch.get_stock_data(ticker, period="1y", interval="1d")
                
                # --- MODIFICATION: Check for 'Close' column ---
                if df.empty or 'Close' not in df.columns:
                    st.error("Could not load historical data for technical analysis.")
                else:
                    # 1. Calculate Indicators
                    # --- MODIFICATION: Call new technicals module ---
                    technicals.calculate_bbands(df)
                    technicals.calculate_rsi(df)
                    technicals.calculate_macd(df)
                    df = df.dropna() # Drop rows with NaNs from indicator calculation

                    # 2. Chart 1: Bollinger Bands
                    st.subheader("Bollinger Bands (20-day)")
                    st.markdown('<div class="panel">', unsafe_allow_html=True)
                    fig_bb = go.Figure()
                    # Candlestick
                    fig_bb.add_trace(go.Candlestick(x=df.index,
                                    open=df['Open'], high=df['High'],
                                    low=df['Low'], close=df['Close'], 
                                    name="Price",
                                    increasing_line_color='#1ED760', 
                                    decreasing_line_color='#D40000'))
                    # Upper Band
                    fig_bb.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], 
                                                line=dict(color='#00FFFF', width=1, dash='dash'), name="Upper Band"))
                    # Middle Band
                    fig_bb.add_trace(go.Scatter(x=df.index, y=df['BBM_20_2.0'], 
                                                line=dict(color='#FFC107', width=1), name="Middle Band (SMA 20)"))
                    # Lower Band
                    fig_bb.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], 
                                                line=dict(color='#00FFFF', width=1, dash='dash'), name="Lower Band"))
                    
                    fig_bb.update_layout(
                        height=500, xaxis_rangeslider_visible=False,
                        plot_bgcolor='#121A2A', paper_bgcolor='#121A2A', font_color='#E0E0E0',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_bb, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # 3. Chart 2: MACD
                    st.subheader("MACD (12, 26, 9)")
                    st.markdown('<div class="panel">', unsafe_allow_html=True)
                    fig_macd = make_subplots(rows=1, cols=1)
                    colors = np.where(df['MACDh_12_26_9'] < 0, '#D40000', '#1ED760')
                    fig_macd.add_trace(go.Bar(x=df.index, y=df['MACDh_12_26_9'], 
                                              name="Histogram", marker_color=colors))
                    fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD_12_26_9'], 
                                                 line=dict(color='#0D6EFD', width=2), name="MACD"))
                    fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACDs_12_26_9'], 
                                                 line=dict(color='#FFC107', width=2), name="Signal"))
                    
                    fig_macd.update_layout(
                        height=300, plot_bgcolor='#121A2A', paper_bgcolor='#121A2A', font_color='#E0E0E0',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_macd, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # 4. Chart 3: RSI
                    st.subheader("Relative Strength Index (RSI-14)")
                    st.markdown('<div class="panel">', unsafe_allow_html=True)
                    fig_rsi = go.Figure()
                    fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI_14'], 
                                                 line=dict(color='#00FFFF', width=2), name="RSI"))
                    fig_rsi.add_hline(y=70, line_dash="dash", line_color="#D40000", annotation_text="Overbought (70)", 
                                      annotation_position="bottom right", annotation_font=dict(color="#D40000"))
                    fig_rsi.add_hline(y=30, line_dash="dash", line_color="#1ED760", annotation_text="Oversold (30)", 
                                      annotation_position="bottom right", annotation_font=dict(color="#1ED760"))
                    
                    fig_rsi.update_layout(
                        height=300, plot_bgcolor='#121A2A', paper_bgcolor='#121A2A', font_color='#E0E0E0',
                        yaxis_range=[0,100], legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_rsi, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- BLOCK 5: Default Page (Market Overview) ---
    else:
        st.title("Market Overview")
        
        st.subheader("Market Snapshot")
        st.markdown('<div id="market-snapshot">', unsafe_allow_html=True)
        with st.spinner("Loading market data..."):
            indices = ['^NSEI', '^BSESN', '^GSPC', '^IXIC', 'GC=F', 'CL=F', 'INR=X', 'EURUSD=X']
            index_data = data_fetch.get_market_data(indices)
            
            cols1 = st.columns(4)
            cols2 = st.columns(4)
            
            index_names = {
                '^NSEI': 'NIFTY 50', '^BSESN': 'SENSEX', 
                '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ',
                'GC=F': 'Gold', 'CL=F': 'Crude Oil',
                'INR=X': 'USD/INR', 'EURUSD=X': 'EUR/USD'
            }
            
            for i, ticker in enumerate(indices[:4]):
                name = index_names.get(ticker)
                data = index_data.get(ticker)
                if data:
                    cols1[i].metric(
                        label=name, 
                        value=f"{data['price']:,.2f}", 
                        delta=f"{data['change']:.2f}%"
                    )
                else:
                    cols1[i].metric(label=name, value="No data")
                    
            for i, ticker in enumerate(indices[4:]):
                name = index_names.get(ticker)
                data = index_data.get(ticker)
                if data:
                    cols2[i].metric(
                        label=name, 
                        value=f"{data['price']:,.2f}", 
                        delta=f"{data['change']:.2f}%"
                    )
                else:
                    cols2[i].metric(label=name, value="No data")
                    
        st.markdown('</div>', unsafe_allow_html=True) # Close ID wrapper
        
        # --- MODIFICATION: Removed News Feed and Market Movers ---


    # --- 5. FOOTER (Now outside the 'elif') ---
    st.markdown("---")
    st.markdown("<div style='text-align:center;color:#667; font-size: 0.9em;'>© 2025 Finqorp Analytics | All data is for informational purposes. Not financial advice.</div>", unsafe_allow_html=True)