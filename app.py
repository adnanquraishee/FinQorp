import streamlit as st
from modules import data_fetch, sentiment, forecast

st.set_page_config(page_title="FinQorp Stock Dashboard", layout="wide")
st.title("📊 FinQorp — Stock Market Insights Dashboard")

# Sidebar Input
st.sidebar.header("Enter Company Name or Ticker")
company_input = st.sidebar.text_input("Company Name or Ticker", value="AAPL")

if st.sidebar.button("Analyze"):
    with st.spinner("Fetching stock data and forecasts..."):
        try:
            result = data_fetch.get_stock_data(company_input)
            stock_data = result["data"] if isinstance(result, dict) else result

            if stock_data is None or stock_data.empty:
                st.error("❌ Could not fetch data.")
                st.stop()

            stock_data = stock_data.reset_index()
            if "Date" not in stock_data.columns:
                stock_data.rename(columns={stock_data.columns[0]: "Date"}, inplace=True)

            st.success(f"✅ Data fetched successfully for {company_input}")
            st.subheader("📅 Recent Stock Data")
            st.dataframe(stock_data.tail())

            # Headlines
            st.subheader("📰 Latest News Headlines")
            headlines = data_fetch.get_headlines(company_input)
            if headlines:
                for i, h in enumerate(headlines[:10], start=1):
                    if isinstance(h, dict):
                        st.markdown(f"**{i}.** [{h.get('title', '')}]({h.get('link', '#')})")
                    else:
                        st.markdown(f"**{i}.** {h}")
            else:
                st.warning("No headlines found.")

            # Sentiment
            st.subheader("💭 Market Sentiment Overview")
            summary, fig = sentiment.analyze_sentiment(company_input)
            if fig:
                st.pyplot(fig)
            elif summary:
                st.markdown(summary)
            else:
                st.warning("No sentiment data available.")

            # Forecast (Grid of 4)
            st.subheader("📈 Forecast Models (Next 30 Days)")
            df, preds, future_dates = forecast.generate_all_forecasts(stock_data)
            if preds:
                fig = forecast.plot_forecasts_grid(df, preds, future_dates)
                st.pyplot(fig)
            else:
                st.warning("⚠️ Forecast models returned no data.")
            

        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
