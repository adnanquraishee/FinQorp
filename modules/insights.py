import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from textblob import TextBlob # Keep import but remove usage
from modules import data_fetch, fundamentals


# =========================================================
# 🔹 AI SUMMARY GENERATOR — News/Sentiment Logic Removed
# =========================================================
def generate_ai_summary(company_name: str):
    """
    Generate an advanced, AI-style financial summary containing:
    - Stock trend, volatility, and momentum
    - Core financial metrics and ratios from fundamentals
    (News and Sentiment sections are removed as requested)
    """
    try:
        # --- Fetch market data ---
        data = yf.download(company_name, period="6mo", interval="1d", progress=False)
        if data is None or not isinstance(data, pd.DataFrame) or data.empty:
            data = yf.download(company_name, period="1mo", interval="1d", progress=False)

        # Normalize column names
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [c[0] if isinstance(c, tuple) else c for c in data.columns]
        else:
            data.columns = [str(c).strip().title() for c in data.columns]

        if "Close" not in data.columns:
            for alt in ["Adj Close", "Close Price", "close", "adj close"]:
                if alt in data.columns:
                    data.rename(columns={alt: "Close"}, inplace=True)
                    break

        # --- If no price data available ---
        if data.empty or "Close" not in data.columns:
            return f"⚠️ Could not retrieve sufficient price data for **{company_name}**."

        data["Return"] = data["Close"].pct_change().fillna(0)
        avg_return = float(data["Return"].mean() * 100)
        volatility = float(data["Return"].std() * 100)
        total_change = float(((data["Close"].iloc[-1] / data["Close"].iloc[0]) - 1) * 100)

        # --- NEWS AND SENTIMENT LOGIC REMOVED ---
        # Initialize placeholders for metrics that relied on sentiment (now based on trend)
        avg_sentiment = 0.0
        
        # --- Fetch Fundamentals ---
        try:
            metrics, _ = fundamentals.get_fundamentals(company_name)
            pe = metrics.get("P/E Ratio", "N/A")
            roe = metrics.get("ROE", "N/A")
            de = metrics.get("Debt-to-Equity", "N/A")
            pm = metrics.get("Profit Margin", "N/A")
            dy = metrics.get("Dividend Yield", "N/A")
        except Exception as e:
            pe = roe = de = pm = dy = "N/A"

        # --- Interpretations ---
        trend = "📈 Upward" if total_change > 0 else "📉 Downward"
        
        # Tone simplified to reflect stock trend rather than external news sentiment
        tone = (
            "positive" if total_change > 5 else
            "negative" if total_change < -5 else
            "stable"
        )
        
        risk = (
            "low volatility ✅" if volatility < 1 else
            "moderate volatility ⚙️" if volatility < 2 else
            "high volatility ⚠️"
        )

        # --- Generate narrative paragraphs ---
        overview = (
            f"Over the past six months, **{company_name}** has shown a {trend.lower()} trend "
            f"with a total change of **{total_change:.2f}%** and an average daily return of **{avg_return:.2f}%**. "
            f"Volatility remains {risk.replace('⚙️','').replace('✅','').replace('⚠️','')}, "
            f"indicating {('a stable trading range' if volatility < 1 else 'moderate price fluctuations typical of an active stock' if volatility < 2 else 'a highly reactive and risky movement pattern')}."
        )

        # REMOVED SENTIMENT PART PARAGRAPH
        
        # --- Smarter Fundamentals Interpretation ---
        try:
            # Parse numeric values safely
            pe_val = float(str(pe).replace("N/A", "").replace("%", "").strip()) if "N/A" not in str(pe) else None
            roe_val = float(str(roe).replace("%", "").strip()) if "N/A" not in str(roe) else None
            de_val = float(str(de).replace("%", "").strip()) if "N/A" not in str(de) else None
            pm_val = float(str(pm).replace("%", "").strip()) if "N/A" not in str(pm) else None
            dy_val = float(str(dy).replace("%", "").strip()) if "N/A" not in str(dy) else None

            # Context-based evaluation
            pe_eval = "attractive valuation" if pe_val and pe_val < 20 else \
                    "fairly valued" if pe_val and pe_val <= 35 else \
                    "richly valued" if pe_val else "valuation unavailable"

            roe_eval = "strong efficiency in shareholder returns" if roe_val and roe_val > 15 else \
                        "moderate returns" if roe_val and roe_val > 5 else \
                        "weak profitability" if roe_val is not None else "ROE data unavailable"

            de_eval = "solid financial structure" if de_val and de_val < 1 else \
                    "moderate leverage" if de_val and de_val <= 2 else \
                    "high debt exposure" if de_val else "leverage data unavailable"

            pm_eval = "excellent profit margins" if pm_val and pm_val > 20 else \
                    "healthy margins" if pm_val and pm_val > 10 else \
                    "thin margins" if pm_val else "margin data unavailable"

            dy_eval = "strong dividend yield" if dy_val and dy_val > 3 else \
                    "modest dividend payout" if dy_val and dy_val > 0 else \
                    "no dividend distribution"

            fundamentals_part = (
                f"Financially, **{company_name}** reports a **P/E ratio of {pe}** "
                f"({pe_eval}), a **Return on Equity (ROE)** of **{roe}** "
                f"({roe_eval}), and a **Debt-to-Equity ratio** of **{de}** "
                f"({de_eval}). Profit margins stand at **{pm}** "
                f"({pm_eval}), with a dividend yield of **{dy}** "
                f"({dy_eval}). "
                f"Overall, these metrics indicate that the company maintains "
                f"{'strong fundamentals and sustainable profitability' if pm_val and pm_val > 20 else 'a moderate financial footing with room for improvement'}."
            )
        except Exception:
            fundamentals_part = (
                f"Financial data for **{company_name}** is partially available. "
                f"Key metrics such as P/E, ROE, and margins could not be fully interpreted."
            )


        conclusion = (
            f"In summary, **{company_name}** exhibits {('positive momentum and sound financial fundamentals' if total_change > 0 and (pe_val and pe_val > 0) else 'mixed signals between market tone and internal performance')}."
        )

        # --- Combine everything into AI-style report ---
        summary = (
            f"**{company_name} — AI Market Summary**\n\n"
            f"📊 **Trend:** {trend} over 6 months (**{total_change:.2f}%** change)\n"
            f"📈 **Average Daily Return:** {avg_return:.2f}%\n"
            f"⚙️ **Volatility:** {risk}\n"
            f"💬 **Recent Tone:** {tone} (based on 6-month price action)\n"
            f"💰 **Fundamentals:** P/E = {pe}, ROE = {roe}, D/E = {de}, Margin = {pm}, Yield = {dy}\n\n"
            f"🧠 **AI Analysis:**\n\n"
            f"{overview}\n\n"
            f"{fundamentals_part}\n\n"
            f"💡 **Insight:** {conclusion}"
        )

        return summary

    except Exception as e:
        return f"⚠️ Error generating AI summary: {e}"