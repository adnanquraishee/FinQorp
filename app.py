# app.py  (Phase 2.4 — Recommendation Layer)
import streamlit as st
import matplotlib.pyplot as plt
from modules import data_fetch, sentiment, forecast, fundamentals, insights, compare, recommendation, ticker_resolver
import traceback, base64, os

st.set_page_config(page_title="FinQorp — Stock Insights", layout="wide")

# ---------- Logo ----------
def get_base64_logo(path):
    if not os.path.exists(path): return ""
    with open(path,"rb") as f: return base64.b64encode(f.read()).decode("utf-8")
logo = get_base64_logo("finqorp_logo.png")

if logo:
    st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:center;gap:12px;">
            <img src="data:image/png;base64,{logo}" style="width:140px;height:auto;"/>
            <h1 style="color:#32D600;font-family:'Trebuchet MS';font-weight:800;font-size:36px;">
                FinQorp — AI Powered Market Intelligence
            </h1>
        </div>""", unsafe_allow_html=True)
else:
    st.title("FinQorp")

st.markdown("---")

# ---------- Tabs ----------
tab1, tab2 = st.tabs(["🏢 Single Company Analysis", "🧩 Comparative Analysis"])

# ---------- Single Company Tab ----------
with tab1:
    st.markdown("### 🔍 Enter Company Name or Ticker")
    company_input = st.text_input("", value="AAPL", key="comp_input") 
    
    # Store the final ticker to be used for analysis
    company_ticker = company_input 

    if st.button("Analyze Company"):
        with st.spinner("Analyzing data..."):
            try:
                # 1️⃣ Ticker Resolution - PURE NETWORK SEARCH WITH VALIDATION
                
                input_upper = company_input.upper().strip()
                company_ticker = input_upper # Default is the direct user input
                
                resolved_ticker = ticker_resolver.resolve_ticker_from_name(company_input)
                
                if resolved_ticker:
                    company_ticker = resolved_ticker.upper().strip()
                
                # FALLBACK LOGIC: If the network search failed, and the input is a long name, stop.
                if not resolved_ticker and (len(input_upper.replace(" ", "")) > 15 or " " in input_upper):
                    st.error(f"❌ The universal search failed to resolve the ticker for: **{company_input}**. "
                             f"The external search API may not recognize this specific long company name. "
                             f"Please enter the ticker manually (e.g., 'GUJALKALI.NS').")
                    st.stop()
                
                # 2️⃣ Data Fetch
                data = data_fetch.get_stock_data(company_ticker)
                stock = data.get("data") if isinstance(data, dict) else data
                if stock is None or stock.empty:
                    # This error catches cases where the original input (or a bad network resolution) failed.
                    st.error(f"❌ No data found for ticker: **{company_ticker}**. Please check the company name or ticker symbol.")
                    st.stop()
                stock = stock.reset_index()
                st.success(f"✅ Data fetched for **{company_ticker}**")
                st.dataframe(stock.tail(), use_container_width=True)

                # 3️⃣ Fundamentals
                st.subheader("📘 Financial Fundamentals & Ratios")
                metrics, figs = fundamentals.get_fundamentals(company_ticker)
                if metrics:
                    cols = st.columns(3)
                    for i,(k,v) in enumerate(metrics.items()):
                        with cols[i%3]: st.metric(k,v)
                if figs:
                    ch = st.columns(3)
                    for i,(k,f) in enumerate(figs.items()):
                        with ch[i%3]:
                            if f: st.pyplot(f)

                # 4️⃣ AI Summary
                st.subheader("💡 AI Market Summary")
                st.markdown(insights.generate_ai_summary(company_ticker)) 

                # 5️⃣ Sentiment
                st.subheader("💭 Market Sentiment Overview")
                ssum, sfig = sentiment.analyze_sentiment(company_ticker)
                if sfig: st.pyplot(sfig)
                elif ssum: st.markdown(ssum)

                # 6️⃣ Forecast
                st.subheader("📈 Forecast Models (Next 30 Days)")
                df, preds, fdates = forecast.generate_all_forecasts(stock) 
                if preds:
                    fig = forecast.plot_forecasts_grid(df, preds, fdates)
                    st.pyplot(fig)
                else:
                    st.warning("⚠️ No forecast data returned.")

                # 7️⃣ Recommendation Layer
                st.subheader("🤖 AI Buy/Hold/Sell Recommendation")
                rec_text, rec_fig = recommendation.get_recommendation(company_ticker)
                st.markdown(rec_text)
                if rec_fig:
                    st.plotly_chart(rec_fig, use_container_width=True)


            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
                st.text(traceback.format_exc())

# ---------- Comparative Tab ----------
with tab2:
    st.markdown("### 🧩 Compare Multiple Companies")
    tickers = st.text_input("Enter tickers (e.g., AAPL, MSFT, GOOG):", "AAPL, MSFT, GOOG")
    symbols = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if st.button("Compare Companies"):
        with st.spinner("Comparing..."):
            try:
                summary, df, fig = compare.compare_companies(symbols)
                if df is not None:
                    st.dataframe(df, use_container_width=True)
                    st.pyplot(fig)
                    st.markdown(summary)
                else:
                    st.warning(summary)
            except Exception as e:
                st.error(f"❌ Comparison failed: {e}")
                st.text(traceback.format_exc())

st.markdown("---")
st.markdown("<div style='text-align:center;color:gray;'>© 2025 FinQorp — Built with ❤️ using AI & Data Science.</div>", unsafe_allow_html=True)