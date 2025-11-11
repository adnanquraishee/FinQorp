# modules/recommendation.py  — Phase 2.5  Upgrade
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from modules import fundamentals, forecast, sentiment
import pandas as pd

def _normalize(value, low, high):
    if value is None or np.isnan(value):
        return 0
    return max(-1, min(1, 2 * ((value - low) / (high - low)) - 1))

def get_recommendation(company_name: str):
    """
    Generates Buy/Hold/Sell recommendation with
    composite logic + interactive confidence gauge.
    """
    try:
        # ---------- Fundamentals ----------
        metrics, _ = fundamentals.get_fundamentals(company_name)
        def safe_num(v):
            try: return float(str(v).replace("%","").replace(",",""))
            except: return np.nan

        pe = safe_num(metrics.get("P/E Ratio"))
        roe = safe_num(metrics.get("ROE"))
        pm = safe_num(metrics.get("Profit Margin"))
        de = safe_num(metrics.get("Debt-to-Equity"))

        f_score = 0
        if not np.isnan(pe):  f_score += _normalize(40 - pe, -20, 40)
        if not np.isnan(roe): f_score += _normalize(roe, 0, 25)
        if not np.isnan(pm):  f_score += _normalize(pm, 0, 30)
        if not np.isnan(de):  f_score += _normalize(2 - de, -1, 2)
        fundamental_score = f_score / 4 if f_score else 0

        # ---------- Forecast ----------
        try:
            df, preds, _ = forecast.generate_all_forecasts(company_name)
            last = df["Close"].iloc[-1]
            avg_future = np.mean([np.mean(v) for v in preds.values()])
            forecast_score = _normalize(((avg_future - last) / last) * 100, -10, 10)
        except: forecast_score = 0

        # ---------- Sentiment ----------
        try:
            summ, _ = sentiment.analyze_sentiment(company_name)
            import re
            m = re.search(r"Average Sentiment:\s*([\-0-9.]+)", summ)
            s_val = float(m.group(1)) if m else 0
            sentiment_score = _normalize(s_val, -1, 1)
        except: sentiment_score = 0

        # ---------- Composite ----------
        comp = 0.4*forecast_score + 0.3*fundamental_score + 0.3*sentiment_score
        if comp > 0.6: label, color, emoji = "Strong Buy","#00FF6A","🚀"
        elif comp > 0.3: label, color, emoji = "Buy","#7FFF00","📈"
        elif comp > -0.3: label, color, emoji = "Hold","#FFD700","🤔"
        elif comp > -0.6: label, color, emoji = "Sell","#FF8C00","📉"
        else: label, color, emoji = "Strong Sell","#FF3030","⚠️"

        conf = abs(comp)
        text = (
            f"### 🤖 AI Recommendation — **{company_name}**\n\n"
            f"**Action:** {label} {emoji}\n\n"
            f"📊 **Composite Score:** {comp:.2f}\n"
            f"💡 **Confidence:** {conf:.2f}\n\n"
            f"**Breakdown:**\n"
            f"• Forecast trend: {forecast_score:.2f}\n"
            f"• Fundamentals: {fundamental_score:.2f}\n"
            f"• Sentiment: {sentiment_score:.2f}\n\n"
            "AI blends forecast momentum, fundamental health and market tone for this signal."
        )

        # ---------- Plotly Gauge ----------
        gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=comp*100,
            delta={"reference":0,"increasing":{"color":"lime"}},
            gauge={
                "axis":{"range":[-100,100],"tickwidth":1,"tickcolor":"#888"},
                "bar":{"color":color},
                "bgcolor":"black",
                "borderwidth":2,
                "bordercolor":"#444",
                "steps":[
                    {"range":[-100,-60],"color":"#D40000"},
                    {"range":[-60,-30],"color":"#FF6B00"},
                    {"range":[-30,30],"color":"#FFCB20"},
                    {"range":[30,60],"color":"#8CFF00"},
                    {"range":[60,100],"color":"#32D600"},
                ],
                "threshold":{"line":{"color":"white","width":3},"thickness":0.8,"value":comp*100}
            },
            title={"text":f"<b>{label}</b>", "font":{"color":"white","size":20}}
        ))
        gauge.update_layout(
            paper_bgcolor="black",
            font={"color":"white"},
            height=300,
            margin=dict(t=20,b=20,l=10,r=10)
        )

        return text, gauge

    except Exception as e:
        return f"⚠️ Error generating recommendation: {e}", None
