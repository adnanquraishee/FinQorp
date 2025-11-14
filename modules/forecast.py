import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

try:
    from prophet import Prophet
except Exception:
    Prophet = None

# ---------------------------------------------------
# Data Prep
# ---------------------------------------------------
def _prepare_data(ticker: str, period: str = "3y"):
    """
    Downloads data and renames columns for Prophet.
    Returns a DataFrame with ['ds', 'y']
    """
    df = yf.download(ticker, period=period, interval="1d", progress=False)
    if df.empty:
        raise ValueError(f"No data found for {ticker} in period {period}")
        
    df = df.reset_index()
    df.columns = [str(col).lower() for col in df.columns]

    date_col = 'date'
    if 'date' not in df.columns:
        if 'index' in df.columns: date_col = 'index'
        elif 'datetime' in df.columns: date_col = 'datetime'
        else: date_col = df.columns[0] 

    price_col = 'adj close' # Use Adj Close for accuracy
    if 'adj close' not in df.columns:
        if 'close' in df.columns: price_col = 'close'
        else:
            for col in df.columns:
                if 'close' in col:
                    price_col = col
                    break
    
    if price_col is None:
        raise ValueError("Could not find 'Close' or 'Adj Close' column in data.")
        
    df = df[[date_col, price_col]].dropna()
    df.columns = ["ds", "y"]
    df["ds"] = pd.to_datetime(df["ds"])
    return df

# ---------------------------------------------------
# Generate Forecast (Prophet + Monte Carlo)
# ---------------------------------------------------

def generate_forecast(ticker: str, period=90, num_simulations=100):
    """
    Runs a Prophet forecast and uses its trend as the
    drift for a Monte Carlo simulation.
    """
    if Prophet is None:
        raise ImportError("Prophet library not found. Please run 'pip install prophet'.")

    # 1. Get Historical Data
    hist_df = _prepare_data(ticker, period="3y")
    last_actual_date = hist_df['ds'].max()
    
    # 2. Get Prophet Trend (the "Drift")
    info = yf.Ticker(ticker).info
    beta = info.get("beta", 1.0)
    flexibility = 0.25 if (beta or 1.0) > 1.2 else 0.01 if (beta or 1.0) < 0.8 else 0.05
    
    model = Prophet(
        daily_seasonality=True, 
        weekly_seasonality=False, 
        yearly_seasonality=True,
        changepoint_prior_scale=flexibility
    )
    model.fit(hist_df)
    future = model.make_future_dataframe(periods=period)
    forecast_df = model.predict(future)
    
    # 3. Calculate Volatility (the "Randomness")
    hist_df['log_return'] = np.log(hist_df['y'] / hist_df['y'].shift(1))
    volatility = hist_df['log_return'].std()
    
    # 4. Run Monte Carlo Simulation
    last_price = hist_df['y'].iloc[-1]
    simulations = np.zeros((period, num_simulations))
    
    # Get the forecasted part of the trend
    forecast_part = forecast_df[forecast_df['ds'] > last_actual_date]
    prophet_trend = forecast_part['yhat'].pct_change().fillna(0).values
    
    for i in range(num_simulations):
        prices = [last_price]
        for day in range(period - 1):
            drift = prophet_trend[day]
            random_shock = np.random.normal(0, volatility)
            next_price = prices[-1] * (1 + drift + random_shock)
            prices.append(next_price)
        simulations[:, i] = prices
        
    # Get dates for the forecast
    future_dates = forecast_part['ds']
    
    return hist_df, simulations, future_dates

# ---------------------------------------------------
# Plot Forecast
# ---------------------------------------------------
def plot_forecast(hist_df, simulations, future_dates, sentiment_score=0.0):
    """
    Plots the Monte Carlo simulation with a 90% confidence interval
    and a sentiment-adjusted line.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # --- THEME COLORS (SLATE & SAPPHIRE) ---
    BG_COLOR = "#121A2A"
    TEXT_COLOR = "#FFFFFF"
    ACCENT_COLOR = "#0D6EFD"
    ACCENT_CYAN = "#00FFFF"
    BORDER_COLOR = "#30363D"

    # 1. Plot all 100 simulations with low opacity
    ax.plot(future_dates, simulations, color=ACCENT_COLOR, alpha=0.1, linewidth=1)
    
    # 2. Calculate percentiles and ensemble
    percentile_5 = np.percentile(simulations, 5, axis=1)
    percentile_50 = np.percentile(simulations, 50, axis=1) # The Median
    percentile_95 = np.percentile(simulations, 95, axis=1)
    
    # 3. Create Sentiment-Adjusted Line
    last_price = hist_df['y'].iloc[-1]
    sentiment_drift = np.linspace(0, (last_price * sentiment_score * 0.1), len(future_dates))
    y_pred_adjusted = percentile_50 + sentiment_drift # Adjust the MEDIAN line

    # 4. Plot historical data
    ax.plot(hist_df['ds'].tail(180), hist_df['y'].tail(180),
            color=TEXT_COLOR, linewidth=2, label="Historical Price")

    # 5. Plot the Median ("Price Only") forecast
    ax.plot(future_dates, percentile_50,
            "--", linewidth=2, label="Median Forecast (Price Only)", color=ACCENT_COLOR, alpha=0.7)
    
    # 6. Plot the "Sentiment-Adjusted" line
    ax.plot(future_dates, y_pred_adjusted,
            "-", linewidth=3, label="Sentiment-Adjusted Forecast", color=ACCENT_CYAN)

    # 7. Plot the 90% confidence cone
    ax.fill_between(future_dates, percentile_5, percentile_95,
                    color=ACCENT_COLOR, alpha=0.2, label="90% Confidence Range")

    # --- Theming ---
    ax.set_facecolor(BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)
    for spine in ax.spines.values():
        spine.set_color(BORDER_COLOR)
    ax.tick_params(colors=TEXT_COLOR, rotation=15)
    ax.legend(facecolor=BG_COLOR, labelcolor=TEXT_COLOR, loc="upper left")
    ax.set_title("Monte Carlo Forecast (100 Simulations)", color=TEXT_COLOR, fontsize=14)
    ax.grid(True, color=BORDER_COLOR, alpha=0.5, linestyle="--")
    
    plt.tight_layout()
    return fig