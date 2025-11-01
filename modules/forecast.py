import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np

def generate_forecast(data):
    try:
        if data is None or data.empty:
            return None

        data = data.dropna(subset=['Close']).reset_index()
        data['Days'] = np.arange(len(data))

        X = data[['Days']]
        y = data['Close']
        model = LinearRegression()
        model.fit(X, y)

        future_days = np.arange(len(data), len(data) + 30).reshape(-1, 1)
        forecast = model.predict(future_days)

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(data['Date'], data['Close'], label='Historical', linewidth=2)
        ax.plot(pd.date_range(data['Date'].iloc[-1], periods=31, freq='D')[1:], forecast, label='Forecast', linestyle='--')
        ax.legend()
        ax.set_title("Stock Price Forecast", fontsize=10)
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        plt.tight_layout()

        return fig
    except Exception as e:
        print(f"Forecast error: {e}")
        return None
