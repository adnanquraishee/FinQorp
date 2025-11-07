import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVR
import torch
import torch.nn as nn
import warnings
warnings.filterwarnings("ignore")

# Try importing heavy libs safely
try:
    from keras.models import Sequential
    from keras.layers import LSTM, Dense, Dropout
except Exception:
    Sequential = None

try:
    from xgboost import XGBRegressor
except Exception:
    XGBRegressor = None


# ---------------------------------------------------
# Transformer Model (PyTorch)
# ---------------------------------------------------
class TransformerModel(nn.Module):
    def __init__(self, feature_size=1, num_layers=3, nhead=2, hidden_dim=128):
        super(TransformerModel, self).__init__()
        self.transformer = nn.Transformer(
            d_model=feature_size,
            nhead=nhead,
            num_encoder_layers=num_layers,
            num_decoder_layers=num_layers,
            dim_feedforward=hidden_dim
        )
        self.fc = nn.Linear(feature_size, 1)

    def forward(self, src, tgt):
        out = self.transformer(src, tgt)
        return self.fc(out)


# ---------------------------------------------------
# Data Prep
# ---------------------------------------------------
def _prepare_data(df_or_symbol):
    if isinstance(df_or_symbol, pd.DataFrame):
        df = df_or_symbol.copy()
    else:
        df = yf.download(df_or_symbol, period="2y", interval="1d", progress=False)
        df = df.reset_index()

    if "Close" not in df.columns:
        for c in df.columns:
            if "close" in c.lower():
                df.rename(columns={c: "Close"}, inplace=True)

    df = df[["Date", "Close"]].dropna()
    df["Date"] = pd.to_datetime(df["Date"])
    return df


# ---------------------------------------------------
# Forecast Models
# ---------------------------------------------------
def _safe_run(func, label, y):
    try:
        return func(y)
    except Exception as e:
        print(f"⚠️ {label} failed: {e}")
        return np.repeat(y[-1], 30)


def _lstm(y, steps=30):
    if Sequential is None:
        print("⚠️ LSTM unavailable.")
        return np.repeat(y[-1], steps)

    scaler = MinMaxScaler()
    y_scaled = scaler.fit_transform(y.reshape(-1, 1))
    X, Y = [], []
    for i in range(60, len(y_scaled)):
        X.append(y_scaled[i - 60:i])
        Y.append(y_scaled[i])
    X, Y = np.array(X), np.array(Y)
    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(X.shape[1], 1)),
        Dropout(0.3),
        LSTM(64),
        Dense(1)
    ])
    model.compile(optimizer="adam", loss="mse")
    model.fit(X, Y, epochs=15, batch_size=32, verbose=0)
    seq = y_scaled[-60:]
    preds = []
    for _ in range(steps):
        p = model.predict(seq.reshape(1, 60, 1), verbose=0)
        preds.append(p[0, 0])
        seq = np.append(seq[1:], p[0, 0])
    return scaler.inverse_transform(np.array(preds).reshape(-1, 1)).flatten()


def _xgb(y, steps=30):
    if XGBRegressor is None:
        print("⚠️ XGBoost unavailable.")
        return np.repeat(y[-1], steps)

    scaler = MinMaxScaler()
    y_scaled = scaler.fit_transform(y.reshape(-1, 1)).flatten()
    X, Y = [], []
    for i in range(10, len(y_scaled)):
        X.append(y_scaled[i - 10:i])
        Y.append(y_scaled[i])
    X, Y = np.array(X), np.array(Y)
    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=500,
        learning_rate=0.03,
        max_depth=8,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        verbosity=0
    )
    model.fit(X, Y)
    seq = y_scaled[-10:]
    preds = []
    for _ in range(steps):
        p = model.predict(seq.reshape(1, -1))[0]
        preds.append(p)
        seq = np.append(seq[1:], p)
    return scaler.inverse_transform(np.array(preds).reshape(-1, 1)).flatten()


def _svr(y, steps=30):
    scaler = MinMaxScaler()
    y_scaled = scaler.fit_transform(y.reshape(-1, 1)).flatten()
    X, Y = [], []
    for i in range(10, len(y_scaled)):
        X.append(y_scaled[i - 10:i])
        Y.append(y_scaled[i])
    X, Y = np.array(X), np.array(Y)
    model = SVR(kernel="rbf", C=500, gamma=0.001, epsilon=0.01)
    model.fit(X, Y)
    seq = y_scaled[-10:]
    preds = []
    for _ in range(steps):
        p = model.predict(seq.reshape(1, -1))[0]
        preds.append(p)
        seq = np.append(seq[1:], p)
    return scaler.inverse_transform(np.array(preds).reshape(-1, 1)).flatten()


def _transformer(y, steps=30):
    try:
        scaler = MinMaxScaler()
        y_scaled = scaler.fit_transform(y.reshape(-1, 1))
        y_tensor = torch.tensor(y_scaled, dtype=torch.float32).unsqueeze(-1)
        model = TransformerModel()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.0005)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        loss_fn = nn.MSELoss()
        for _ in range(15):
            optimizer.zero_grad()
            out = model(y_tensor[:-1].unsqueeze(1), y_tensor[1:].unsqueeze(1))
            loss = loss_fn(out, y_tensor[1:].unsqueeze(1))
            loss.backward()
            optimizer.step()
        preds = [y_scaled[-1].item()]
        for _ in range(steps - 1):
            next_val = model(
                torch.tensor([[preds[-1]]]).unsqueeze(1),
                torch.tensor([[preds[-1]]]).unsqueeze(1)
            ).item()
            preds.append(next_val)
        preds = np.array(preds).reshape(-1, 1)
        return scaler.inverse_transform(preds).flatten()
    except Exception as e:
        print(f"⚠️ Transformer failed: {e}")
        return np.repeat(y[-1], steps)


# ---------------------------------------------------
# Generate + Plot
# ---------------------------------------------------
def generate_all_forecasts(data):
    df = _prepare_data(data)
    y = df["Close"].values
    last_date = df["Date"].iloc[-1]
    future_dates = pd.date_range(last_date, periods=31, freq="D")[1:]
    preds = {
        "LSTM": _safe_run(_lstm, "LSTM", y),
        "XGBoost": _safe_run(_xgb, "XGBoost", y),
        "SVR": _safe_run(_svr, "SVR", y),
        "Transformer": _safe_run(_transformer, "Transformer", y)
    }
    return df, preds, future_dates


def plot_forecasts_grid(df, preds, future_dates):
    models = list(preds.keys())
    fig, axes = plt.subplots(2, 2, figsize=(12, 6))
    axes = axes.flatten()

    for i, model in enumerate(models):
        ax = axes[i]
        y_pred = preds[model]
        ax.plot(df["Date"].tail(60), df["Close"].tail(60),
                color="#00FFFF", linewidth=2, label="Historical")
        ax.plot(future_dates, y_pred, "--", linewidth=2,
                label=f"{model} Forecast", color="#FF8800")
        ax.set_facecolor("#000000")
        for spine in ax.spines.values():
            spine.set_color("#CCCCCC")
        ax.tick_params(colors="white", rotation=15)
        ax.legend(facecolor="black", labelcolor="white")
        ax.set_title(model, color="#00FFFF", fontsize=10)
        ax.grid(True, color="#333333", alpha=0.5)

    fig.patch.set_facecolor("black")
    plt.tight_layout()
    return fig
