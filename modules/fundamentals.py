import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =============================================================
# ✅ REVISED UNIVERSAL FUNDAMENTALS WITH DYNAMIC CURRENCY
# =============================================================
def get_fundamentals(ticker_symbol: str):
    """
    Fetches financial fundamentals using yfinance, providing robust handling
    for missing data and dynamic currency symbols.
    """
    try:
        t = yf.Ticker(ticker_symbol)
        info = t.info
        fin = t.financials
        bs = t.balance_sheet
        cf = t.cashflow

        # Clean column names and transpose (latest data is in the first row after transpose)
        def normalize(df):
            if df is not None and not df.empty:
                df = df.transpose().fillna(0)
                # Normalize columns: lower, remove spaces, keep only alphanumeric and underscore
                df.columns = df.columns.astype(str).str.lower().str.replace(r'[^\w]', '', regex=True)
                return df.iloc[::-1] # Reverse order so the latest date is last for plotting/iloc[-1]
            return pd.DataFrame()

        fin = normalize(fin)
        bs = normalize(bs)
        cf = normalize(cf)
        
        # =============================================================
        # 🔹 Currency Detection
        # =============================================================
        currency_code = info.get("currency", "USD")
        
        # Simple mapping for common currencies to ensure correct symbol display
        currency_map = {
            "USD": "$",
            "INR": "₹",
            "CAD": "C$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "AUD": "A$"
        }
        
        # Default to $ if currency code is unknown or missing
        currency_symbol = currency_map.get(currency_code.upper(), "$")


        # =============================================================
        # 🔹 Dividend & Payout (Safer Data Access)
        # =============================================================
        div_yield = 0.0
        payout_ratio = 0.0

        # Use .get() with a default value to prevent errors
        dividend_yield_info = info.get("dividendYield")
        trailing_div = info.get("trailingAnnualDividendRate", 0)
        current_price = info.get("currentPrice", 0)
        trailing_eps = info.get("trailingEps", 0)

        # 1. Primary Check (Yahoo's pre-calculated yield)
        if dividend_yield_info:
            div_yield = dividend_yield_info * 100
        # 2. Fallback Check (Rate / Price)
        elif trailing_div > 0 and current_price > 0:
            div_yield = (trailing_div / current_price) * 100

        # Payout Ratio (Rate / EPS)
        if trailing_div > 0 and trailing_eps > 0:
            payout_ratio = (trailing_div / trailing_eps) * 100
        
        # Clean up any potential NaN from yfinance info
        div_yield = 0 if np.isnan(div_yield) else div_yield
        payout_ratio = 0 if np.isnan(payout_ratio) else payout_ratio

        # =============================================================
        # 🔹 Basic Metrics (USING DYNAMIC CURRENCY_SYMBOL)
        # =============================================================
        metrics = {
            "Market Cap": f"{currency_symbol}{info.get('marketCap', 0):,}" if info.get('marketCap') else "N/A",
            "P/E Ratio": round(info.get("trailingPE", np.nan), 2) if info.get("trailingPE") else "N/A",
            "EPS": round(info.get("trailingEps", np.nan), 2) if info.get("trailingEps") else "N/A",
            "Beta": round(info.get("beta", np.nan), 2) if info.get('beta') else "N/A",
            "Dividend Yield": f"{div_yield:.2f}%",
            "Payout Ratio": f"{payout_ratio:.2f}%",
            "Revenue (TTM)": f"{currency_symbol}{info.get('totalRevenue', 0):,}" if info.get('totalRevenue') else "N/A",
            "Profit Margin": f"{round(info.get('profitMargins', 0)*100,2)}%" if info.get("profitMargins") else "N/A",
        }
        
        # --- DIAGNOSTIC CHECK FOR MISSING P/E (Kept for logging) ---
        if metrics["P/E Ratio"] == "N/A":
            eps_value = info.get("trailingEps", np.nan)
            if not np.isnan(eps_value) and eps_value <= 0:
                print(f"DIAGNOSTIC: P/E is N/A for {ticker_symbol} because EPS is non-positive ({eps_value:.2f}).")
            elif info.get("trailingPE") is None:
                print(f"DIAGNOSTIC: P/E is N/A for {ticker_symbol} because 'trailingPE' key is missing from YF data.")
        # ---------------------------------------------------


        # =============================================================
        # 🔹 Advanced Ratios — D/E, ROE, ROA (Robust Balance Sheet Extraction)
        # =============================================================
        roe = roa = de_ratio = np.nan
        total_debt = 0
        equity = np.nan
        assets = np.nan
        total_liab = np.nan

        try:
            # Net Income for ROE/ROA
            net_income = fin.filter(like="netincome").iloc[-1].sum() if not fin.empty and len(fin) > 0 else np.nan
            
            # --- Robust Balance Sheet Column Detection ---
            # Search for broader terms to catch variants (e.g., shareholdersequity)
            eq_cols = [c for c in bs.columns if "equity" in c or "shareholder" in c]
            asset_cols = [c for c in bs.columns if "asset" in c]
            liab_cols = [c for c in bs.columns if "liab" in c or "borrow" in c]
            debt_cols = [c for c in bs.columns if "debt" in c or "borrow" in c]
            
            # 1. PRIMARY SOURCE: Balance Sheet Dataframe (bs)
            if not bs.empty and len(bs) > 0:
                # Latest figures are at iloc[-1] after the dataframe is reversed
                equity = bs[eq_cols].iloc[-1].sum() if eq_cols else np.nan
                assets = bs[asset_cols].iloc[-1].sum() if asset_cols else np.nan
                total_liab = bs[liab_cols].iloc[-1].sum() if liab_cols else np.nan
                total_debt = bs[debt_cols].iloc[-1].sum() if debt_cols else 0
            
            # 2. FALLBACK SOURCE: Ticker Info (info)
            if np.isnan(equity):
                equity = info.get("totalStockholderEquity", np.nan)
            if np.isnan(assets):
                assets = info.get("totalAssets", np.nan)
            if np.isnan(total_liab):
                total_liab = info.get("totalLiab", np.nan)
            if total_debt == 0:
                total_debt = info.get("totalDebt", 0)
                
            # Debt estimation if totalDebt is missing but Liab and Equity are present
            if total_debt == 0 and not np.isnan(total_liab) and not np.isnan(equity):
                total_debt = max(total_liab - equity, 0)

            # Compute ratios
            if not np.isnan(total_debt) and not np.isnan(equity) and equity != 0:
                de_ratio = total_debt / equity
            
            if not np.isnan(net_income) and not np.isnan(equity) and equity != 0:
                roe = (net_income / equity) * 100
            
            if not np.isnan(net_income) and not np.isnan(assets) and assets != 0:
                roa = (net_income / assets) * 100

            # Fallbacks from info dict for ROE/ROA (already normalized)
            if np.isnan(roe) and info.get("returnOnEquity"):
                roe = info["returnOnEquity"] * 100
            if np.isnan(roa) and info.get("returnOnAssets"):
                roa = info["returnOnAssets"] * 100

            metrics["ROE"] = f"{roe:.2f}%" if not np.isnan(roe) else "N/A"
            metrics["ROA"] = f"{roa:.2f}%" if not np.isnan(roa) else "N/A"
            # Explicitly return 'N/A' if D/E cannot be calculated
            metrics["Debt-to-Equity"] = f"{de_ratio:.2f}" if not np.isnan(de_ratio) else "N/A"

        except Exception as e:
            metrics["Debt-to-Equity"] = metrics["ROE"] = metrics["ROA"] = "N/A"


        # =============================================================
        # 🔹 Financial Trend Visualizations (3 Graphs)
        # =============================================================
        figs = {}

        # 1️⃣ Revenue vs Net Income
        try:
            if not fin.empty and "totalrevenue" in fin.columns and "netincome" in fin.columns:
                fig1, ax1 = plt.subplots(figsize=(5, 2.5))
                ax1.plot(fin.index, fin["totalrevenue"] / 1e9, label="Revenue (B$)", color="#32D600", linewidth=2)
                ax1.plot(fin.index, fin["netincome"] / 1e9, label="Net Income (B$)", color="#FFCB20", linewidth=2)
                ax1.legend(facecolor="black", labelcolor="white", fontsize=7)
                ax1.set_facecolor("black")
                fig1.patch.set_facecolor("black")
                ax1.set_title(f"{ticker_symbol} Revenue vs Net Income", color="white", fontsize=9)
                ax1.tick_params(colors="white", rotation=25)
                for spine in ax1.spines.values():
                    spine.set_color("white")
                plt.tight_layout()
                figs["rev_income"] = fig1
        except Exception:
            pass

        # 2️⃣ Operating Cash Flow
        try:
            if not cf.empty and "totalcashfromoperatingactivities" in cf.columns:
                fig2, ax2 = plt.subplots(figsize=(5, 2.5))
                ax2.bar(cf.index, cf["totalcashfromoperatingactivities"] / 1e9, color="#00FFFF")
                ax2.set_facecolor("black")
                fig2.patch.set_facecolor("black")
                ax2.set_title(f"{ticker_symbol} Operating Cash Flow (B$)", color="white", fontsize=9)
                ax2.tick_params(colors="white", rotation=25)
                for spine in ax2.spines.values():
                    spine.set_color("white")
                plt.tight_layout()
                figs["cash_flow"] = fig2
        except Exception:
            pass

        # 3️⃣ Balance Sheet Snapshot (always draw something)
        try:
            # Check if all components are non-NaN (as determined in the Advanced Ratios section)
            if (not np.isnan(assets)) and (not np.isnan(total_liab)) and (not np.isnan(equity)):
                fig3, ax3 = plt.subplots(figsize=(3.5, 2))
                ax3.bar(["Assets", "Liabilities", "Equity"], 
                        [assets / 1e9, total_liab / 1e9, equity / 1e9],
                        color=["#32D600", "#D40000", "#FFCB20"])
                ax3.set_facecolor("black")
                fig3.patch.set_facecolor("black")
                ax3.set_title("Balance Sheet (B$)", color="white", fontsize=9)
                ax3.tick_params(colors="white")
                for spine in ax3.spines.values():
                    spine.set_color("white")
                plt.tight_layout()
                figs["balance_sheet"] = fig3
        except Exception as e:
            pass

        return metrics, figs

    except Exception as e:
        # Catch errors like invalid ticker symbols or connection failures
        return {"Error": f"Failed to fetch data for {ticker_symbol}: {str(e)}"}, {}