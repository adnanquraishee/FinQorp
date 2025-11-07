# app.py
import streamlit as st
import matplotlib.pyplot as plt
from modules import data_fetch, sentiment, forecast, fundamentals, insights
import traceback
import base64
import os

# ============================================================
# ✅ LOAD & EMBED FINQORP LOGO
# ============================================================
def get_base64_logo(image_path):
    """Safely load and encode logo file as base64 string."""
    if not os.path.exists(image_path):
        st.warning(f"⚠️ Logo file not found: {image_path}")
        return ""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        st.error(f"Error loading logo: {e}")
        return ""

logo_path = "finqorp_logo.png"  # ✅ Ensure this is placed beside app.py
logo_base64 = get_base64_logo(logo_path)

# ============================================================
# ✅ PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="FinQorp — Stock Market Insights Dashboard", layout="wide")

# ============================================================
# ✅ HEADER WITH LOGO + TITLE
# ============================================================
if logo_base64:
    st.markdown(
        f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            padding: 15px 0 5px 0;
        ">
            <img src="data:image/png;base64,{logo_base64}" 
                 alt="FinQorp Logo" 
                 style="width:140px; height:auto; filter: drop-shadow(0px 0px 6px rgba(50,214,0,0.5));"/>
            <h1 style="
                color: #32D600;
                font-family: 'Trebuchet MS', sans-serif;
                font-weight: 800;
                font-size: 38px;
                letter-spacing: 1px;
                margin: 0;
            ">
                FinQorp — AI-Powered Market Intelligence
            </h1>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.title("FinQorp — AI-Powered Market Intelligence")

# ============================================================
# ✅ COMPANY INPUT
# ============================================================
st.markdown("---")
st.markdown("### 🔍 Enter Company Name or Ticker")
company_input = st.text_input(
    "",
    value="AAPL",
    help="Enter a company name or ticker symbol (e.g., AAPL, MSFT, TSLA)",
    placeholder="Search any company..."
)

# ============================================================
# ✅ MAIN EXECUTION — RUN ON BUTTON CLICK
# ============================================================
if st.button("Analyze"):
    with st.spinner("🔄 Fetching and analyzing data... Please wait."):
        try:
            # ------------------- FETCH STOCK DATA -------------------
            data = data_fetch.get_stock_data(company_input)
            stock_data = data.get("data") if isinstance(data, dict) else data

            if stock_data is None or stock_data.empty:
                st.error("❌ No stock data found. Try another company name or ticker.")
                st.stop()

            stock_data = stock_data.reset_index()
            if "Date" not in stock_data.columns:
                stock_data.rename(columns={stock_data.columns[0]: "Date"}, inplace=True)

            st.success(f"✅ Data fetched successfully for {company_input}")

            # ------------------- STOCK DATA TABLE -------------------
            st.subheader(f"📅 Recent Stock Data — {company_input}")
            st.dataframe(stock_data.tail(), use_container_width=True)

            # ------------------- FUNDAMENTALS -------------------
            st.subheader("📘 Financial Fundamentals & Ratios")
            try:
                metrics, figs = fundamentals.get_fundamentals(company_input)
                if isinstance(metrics, dict):
                    cols = st.columns(3)
                    for i, (key, val) in enumerate(metrics.items()):
                        with cols[i % 3]:
                            st.metric(key, val)
                    if isinstance(figs, dict):
                        chart_cols = st.columns(3)
                        for i, (k, f) in enumerate(figs.items()):
                            with chart_cols[i % 3]:
                                if f:
                                    st.pyplot(f)
                else:
                    st.write(metrics)
            except Exception as e:
                st.warning(f"⚠️ Could not load fundamentals: {e}")

            # ------------------- INSIGHTS -------------------
            st.subheader("💡 AI Market Summary")
            ai_summary = insights.generate_ai_summary(company_input)
            st.markdown(ai_summary)

            # ------------------- HEADLINES -------------------
            st.subheader("📰 Latest News Headlines")
            headlines = data_fetch.get_headlines(company_input)
            if headlines:
                for i, h in enumerate(headlines[:10], start=1):
                    if isinstance(h, dict):
                        title = h.get("title", "").strip()
                        link = h.get("link", "#")
                        if title:
                            st.markdown(f"**{i}.** [{title}]({link})")
                    else:
                        st.markdown(f"**{i}.** {h}")
            else:
                st.warning("No recent headlines found for this company.")

            # ------------------- SENTIMENT -------------------
            st.subheader("💭 Market Sentiment Overview")
            summary, fig = sentiment.analyze_sentiment(company_input)
            if fig:
                st.pyplot(fig)
            elif summary:
                st.markdown(summary)
            else:
                st.warning("No sentiment data available.")

            # ------------------- FORECAST -------------------
            st.subheader("📈 Forecast Models (Next 30 Days)")
            df, preds, future_dates = forecast.generate_all_forecasts(stock_data)
            if preds:
                fig = forecast.plot_forecasts_grid(df, preds, future_dates)
                st.pyplot(fig)
            else:
                st.warning("⚠️ Forecast models returned no data.")

        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            st.text(traceback.format_exc())

# ============================================================
# ✅ FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; font-size:14px; color:gray;">
        © 2025 <b>FinQorp</b> — Built with ❤️ using AI & Data Science.
    </div>
    """,
    unsafe_allow_html=True
)
