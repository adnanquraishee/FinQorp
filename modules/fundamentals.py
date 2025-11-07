import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =============================================================
# ✅ CORE DATA FETCH
# =============================================================
def get_fundamentals(ticker_symbol: str):
    """
    Fetches key fundamentals, ratios, and financial statement metrics.
    Returns dict of metrics and prepared visual figures.
    """
    try:
        t = yf.Ticker(ticker_symbol)
        info = t.info
        fin = t.financials
        bs = t.balance_sheet
        cf = t.cashflow

        if not fin.empty:
            fin = fin.transpose().fillna(0)
        if not bs.empty:
            bs = bs.transpose().fillna(0)
        if not cf.empty:
            cf = cf.transpose().fillna(0)

        # =============================================================
        # 🔹 BASIC METRICS
        # =============================================================
        metrics = {
            "Market Cap": f"${info.get('marketCap', 0):,}" if info.get('marketCap') else "N/A",
            "P/E Ratio": round(info.get("trailingPE", np.nan), 2) if info.get("trailingPE") else "N/A",
            "EPS": round(info.get("trailingEps", np.nan), 2) if info.get("trailingEps") else "N/A",
            "Beta": round(info.get("beta", np.nan), 2) if info.get('beta') else "N/A",
            "Dividend Yield": f"{round(info.get('dividendYield', 0)*100,2)}%" if info.get("dividendYield") else "N/A",
            "Revenue (TTM)": f"${info.get('totalRevenue', 0):,}" if info.get('totalRevenue') else "N/A",
            "Profit Margin": f"{round(info.get('profitMargins', 0)*100,2)}%" if info.get("profitMargins") else "N/A",
        }

        # =============================================================
        # 🔹 COMPUTE ADDITIONAL RATIOS (FALLBACK)
        # =============================================================
       
        if not fin.empty and not bs.empty:
            try:
                # Identify correct column names (different tickers use different labels)
                ni_col = next((c for c in fin.columns if "net income" in c.lower()), None)
                eq_col = next((c for c in bs.columns if "stockholder" in c.lower() or "equity" in c.lower()), None)
                liab_col = next((c for c in bs.columns if "liab" in c.lower()), None)
                asset_col = next((c for c in bs.columns if "asset" in c.lower()), None)

                net_income = fin[ni_col].iloc[-1] if ni_col else np.nan
                equity = bs[eq_col].iloc[-1] if eq_col else np.nan
                liabilities = bs[liab_col].iloc[-1] if liab_col else np.nan
                assets = bs[asset_col].iloc[-1] if asset_col else np.nan

                # --- Compute ratios directly if possible ---
                roe = (net_income / equity) * 100 if equity and not np.isnan(equity) else np.nan
                de_ratio = (liabilities / equity) if equity and not np.isnan(equity) else np.nan
                roa = (net_income / assets) * 100 if assets and not np.isnan(assets) else np.nan

                # --- Fallback: Approximate ROE if equity missing ---
                if np.isnan(roe) and info.get("profitMargins") and info.get("returnOnAssets"):
                    try:
                        pm = info["profitMargins"] * 100
                        roa_est = info["returnOnAssets"] * 100
                        # estimate leverage multiplier if available
                        leverage = (info.get("totalDebt", 0) / info.get("totalStockholderEquity", 1)) + 1
                        roe = min(pm * leverage, 80)  # cap to realistic range
                    except Exception:
                        roe = np.nan

                metrics["ROE"] = f"{roe:.2f}%" if not np.isnan(roe) else "N/A"
                metrics["ROA"] = f"{roa:.2f}%" if not np.isnan(roa) else "N/A"
                metrics["Debt-to-Equity"] = f"{de_ratio:.2f}" if not np.isnan(de_ratio) else "N/A"

            except Exception as e:
                print(f"⚠️ Ratio computation fallback failed: {e}")


        # =============================================================
        # 🔹 FINANCIAL TREND FIGURES
        # =============================================================
        figs = {}

        # Revenue vs Net Income
        try:
            revenue = fin["Total Revenue"]
            income = fin["Net Income"]
            fig1, ax1 = plt.subplots(figsize=(5, 2.5))
            ax1.plot(revenue.index, revenue.values / 1e9, label="Revenue (B$)", color="#32D600", linewidth=2)
            ax1.plot(income.index, income.values / 1e9, label="Net Income (B$)", color="#FFCB20", linewidth=2)
            ax1.legend(facecolor="black", labelcolor="white", fontsize=7)
            ax1.set_facecolor("black")
            fig1.patch.set_facecolor("black")
            ax1.set_title("Revenue vs Net Income", color="white", fontsize=9)
            ax1.tick_params(colors="white", rotation=25)
            for spine in ax1.spines.values():
                spine.set_color("white")
            plt.tight_layout()
            figs["rev_income"] = fig1
        except Exception:
            pass

        # Cash Flow Trend
        try:
            ocf = cf["Total Cash From Operating Activities"]
            fig2, ax2 = plt.subplots(figsize=(5, 2.5))
            ax2.bar(ocf.index, ocf.values / 1e9, color="#00FFFF")
            ax2.set_facecolor("black")
            fig2.patch.set_facecolor("black")
            ax2.set_title("Operating Cash Flow (B$)", color="white", fontsize=9)
            ax2.tick_params(colors="white", rotation=25)
            for spine in ax2.spines.values():
                spine.set_color("white")
            plt.tight_layout()
            figs["cash_flow"] = fig2
        except Exception:
            pass

        # Balance Sheet Snapshot
        try:
            assets = bs["Total Assets"].iloc[-1] / 1e9
            liab = bs["Total Liab"].iloc[-1] / 1e9
            eq = bs["Total Stockholder Equity"].iloc[-1] / 1e9
            fig3, ax3 = plt.subplots(figsize=(3, 2))
            ax3.bar(["Assets", "Liabilities", "Equity"], [assets, liab, eq],
                    color=["#32D600", "#D40000", "#FFCB20"])
            ax3.set_facecolor("black")
            fig3.patch.set_facecolor("black")
            ax3.set_title("Balance Sheet (B$)", color="white", fontsize=9)
            for spine in ax3.spines.values():
                spine.set_color("white")
            ax3.tick_params(colors="white")
            plt.tight_layout()
            figs["balance_sheet"] = fig3
        except Exception:
            pass

        return metrics, figs

    except Exception as e:
        return {"Error": str(e)}, {}
