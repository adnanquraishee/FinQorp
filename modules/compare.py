import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from modules import fundamentals
# IMPORT NEW RESOLVER MODULE
from modules import ticker_resolver 

# =====================================================
# ✅ Utility: Convert string metrics to float safely
# =====================================================
def safe_to_float(val):
    try:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            val = val.replace("%", "").replace("$", "").replace(",", "").strip()
            if val in ["N/A", "", "-", "nan"]:
                return np.nan
            return float(val)
    except Exception:
        return np.nan
    return np.nan


# =====================================================
# ✅ Core Comparison Function — Modular 2x2 Layout (Revised)
# =====================================================
def compare_companies(input_symbols):
    """
    Compare multiple companies' financial fundamentals visually and analytically.
    Applies ticker resolution to all input symbols before fetching data.
    """
    if not input_symbols or len(input_symbols) < 2:
        return "Please enter at least two companies or tickers for comparison.", None, None

    metrics_list = []
    resolved_tickers = []
    
    # 1. RESOLVE ALL TICKERS BEFORE FETCHING DATA
    for symbol_input in input_symbols:
        symbol_upper = symbol_input.upper().strip()
        final_ticker = symbol_upper
        
        # Use the universal network resolver
        resolved = ticker_resolver.resolve_ticker_from_name(symbol_input)
        
        if resolved:
            final_ticker = resolved.upper().strip()
        
        # Only proceed if the ticker has not been processed and it's not a clear failure (long name)
        # We rely on the robustness of the resolver, if it fails, we assume the user entered the ticker directly
        if final_ticker not in resolved_tickers:
            resolved_tickers.append(final_ticker)

    
    # 2. FETCH FUNDAMENTALS FOR RESOLVED TICKERS
    for ticker in resolved_tickers:
        try:
            # We use the resolved ticker here
            data, _ = fundamentals.get_fundamentals(ticker)
            
            # Check for generic data fetch error (e.g., ticker not found)
            if "Error" in data:
                print(f"Skipping {ticker}: {data['Error']}")
                continue
                
            metrics_list.append({
                "Ticker": ticker,
                "P/E Ratio": safe_to_float(data.get("P/E Ratio", np.nan)),
                "ROE": safe_to_float(data.get("ROE", np.nan)),
                "Debt-to-Equity": safe_to_float(data.get("Debt-to-Equity", np.nan)),
                "Profit Margin": safe_to_float(data.get("Profit Margin", np.nan)),
            })
        except Exception as e:
            print(f"Failed to process fundamentals for {ticker}: {e}")
            continue

    if not metrics_list:
        return "No valid financial data available for comparison after attempting resolution.", None, None

    df = pd.DataFrame(metrics_list).set_index("Ticker")
    
    # --- Check for minimum data points (optional, but good practice) ---
    if len(df) < 2:
         return "Comparison requires at least two companies with valid data.", None, None


    # =====================================================
    # 📊 Unified Modular 2x2 Comparative Layout
    # =====================================================
    metrics_to_plot = ["P/E Ratio", "ROE", "Debt-to-Equity", "Profit Margin"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 6))
    axes = axes.flatten()

    for i, metric in enumerate(metrics_to_plot):
        ax = axes[i]
        valid_df = df.dropna(subset=[metric])
        if valid_df.empty:
            ax.text(0.5, 0.5, f"No valid data\nfor {metric}",
                    color="gray", ha="center", va="center", fontsize=9)
            ax.set_facecolor("black")
            for spine in ax.spines.values():
                spine.set_color("white")
            continue

        bars = ax.bar(valid_df.index, valid_df[metric], color="#32D600", alpha=0.9)
        ax.set_title(metric, color="white", fontsize=10)
        ax.set_facecolor("black")
        fig.patch.set_facecolor("black")
        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_color("white")

        # Add value labels
        for bar, val in zip(bars, valid_df[metric]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{val:.2f}", ha="center", va="bottom", color="white", fontsize=8)

    plt.tight_layout(pad=2.0)

    # =====================================================
    # 💡 AI Comparative Insight
    # =====================================================
    try:
        top_roe = df["ROE"].idxmax() if df["ROE"].notna().any() else None
        top_pm = df["Profit Margin"].idxmax() if df["Profit Margin"].notna().any() else None
        low_de = df["Debt-to-Equity"].idxmin() if df["Debt-to-Equity"].notna().any() else None

        summary = (
            f"**AI Comparative Insight:**\n\n"
            f"📊 **{top_roe}** leads in Return on Equity, showing strong shareholder returns.\n"
            f"💰 **{top_pm}** exhibits the highest profit margins, highlighting operational efficiency.\n"
            f"⚖️ **{low_de}** maintains the lowest debt levels, signaling solid financial stability.\n\n"
            f"Overall, the companies display distinct risk–reward and profitability profiles."
            if top_roe and top_pm and low_de else
            "Not enough consistent data for a detailed comparative insight."
        )
    except Exception:
        summary = "Could not generate comparative insight."

    return summary, df, fig