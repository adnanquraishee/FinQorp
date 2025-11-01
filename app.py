# app.py
import streamlit as st
from modules import data_fetch, sentiment, forecast

st.set_page_config(page_title="FinQorp Stock Dashboard", layout="wide")

st.title("📊 FinQorp — Stock Market Insights Dashboard")

# --- Sidebar ---
st.sidebar.header("Enter Company Name or Ticker")
company_input = st.sidebar.text_input("Company Name or Ticker", value="AAPL")

if st.sidebar.button("Analyze"):
    with st.spinner("Fetching stock data and news..."):
        try:
            # 1️⃣ Fetch stock data (auto-resolves ticker from company name if needed)
            result = data_fetch.get_stock_data(company_input)

            # Handle if get_stock_data returns dict or dataframe
            if isinstance(result, dict):
                if 'data' not in result or result['data'] is None or result['data'].empty:
                    st.error(f"❌ Could not find stock data for '{company_input}'. Please check the name or ticker.")
                    st.stop()
                stock_data = result['data']
                ticker = result.get('ticker', company_input.upper())
                company_name = result.get('company_name', ticker)
            elif isinstance(result, type(None)) or result.empty:
                st.error(f"❌ No data found for '{company_input}'.")
                st.stop()
            else:
                stock_data = result
                ticker = company_input.upper()
                company_name = ticker

            st.success(f"✅ Data fetched successfully for {company_name} ({ticker})")

            # --- Recent Stock Data ---
            st.subheader(f"📅 Recent Stock Data — {ticker}")
            st.dataframe(stock_data.tail())

            # --- Headlines ---
            st.subheader(f"📰 Latest News Headlines for {company_name}")
            headlines = data_fetch.get_headlines(ticker)
            if headlines:
                for i, h in enumerate(headlines[:10], start=1):
                    st.markdown(f"**{i}.** {h}")
            else:
                st.warning("No recent headlines found for this company.")

            # --- Sentiment Analysis ---
            st.subheader("💭 Market Sentiment Overview")
            sentiment_summary, sentiment_fig = sentiment.analyze_sentiment(company_name)

            if sentiment_fig is not None:
                st.pyplot(sentiment_fig)
            elif sentiment_summary:
                st.markdown(sentiment_summary)
            else:
                st.warning("No sentiment data available for this company.")

            # --- Forecast Section ---
            st.subheader("📈 Stock Price Forecast (Next 30 Days)")
            forecast_fig = forecast.generate_forecast(stock_data)

            if forecast_fig is not None:
                st.pyplot(forecast_fig)
            else:
                st.warning("Forecast model could not be generated. Try again later.")

        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
