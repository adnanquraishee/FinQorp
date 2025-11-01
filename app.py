import streamlit as st
from modules import data_fetch, sentiment, forecast

st.set_page_config(page_title="FinQorp — Stock Market Insights", layout="wide")
st.title("📊 FinQorp — Stock Market Insights Dashboard")

# Sidebar input
st.sidebar.header("Enter Company Name or Ticker")
company_name = st.sidebar.text_input("Company Name or Ticker", value="AAPL")

if st.sidebar.button("Analyze"):
    try:
        # 1️⃣ Fetch Data
        st.info("Fetching stock data and news...")
        data = data_fetch.get_stock_data(company_name)
        headlines = data_fetch.get_headlines(company_name)

        if data is None or data.empty:
            st.error("No stock data found. Please check the company name or ticker.")
        else:
            st.success(f"✅ Data fetched successfully for {company_name}")

            st.subheader("📅 Recent Stock Data")
            st.dataframe(data.tail())

            # 2️⃣ Headlines
            st.subheader(f"📰 Latest News Headlines for {company_name}")
            if headlines:
                for i, h in enumerate(headlines, start=1):
                    st.write(f"{i}. {h}")
            else:
                st.warning("No headlines found.")

            # 3️⃣ Sentiment
            st.subheader("💭 Market Sentiment Overview")
            sentiment_summary, sentiment_fig = sentiment.analyze_sentiment(headlines)

            if sentiment_fig:
                st.pyplot(sentiment_fig, clear_figure=True)
            else:
                st.warning("No sentiment chart available.")
            st.markdown(sentiment_summary)

            # 4️⃣ Forecast
            st.subheader("📈 Stock Price Forecast (Next 30 Days)")
            forecast_fig = forecast.generate_forecast(data)
            if forecast_fig:
                st.pyplot(forecast_fig, clear_figure=True)
            else:
                st.warning("Forecast could not be generated.")

    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
