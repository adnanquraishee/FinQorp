import yfinance as yf
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def generate_correlation_heatmap(tickers: list):
    """
    Downloads 1 year of price data for a list of tickers,
    calculates their daily return correlation, and plots a heatmap.
    """
    if not tickers or len(tickers) < 2:
        return None

    try:
        # Download 1 year of adjusted close prices
        data = yf.download(tickers, period="1y", interval="1d", progress=False)['Adj Close']
        
        # Handle case where only one valid ticker is returned (as a Series)
        if isinstance(data, pd.Series):
            print("Correlation error: Only one valid ticker's data was returned.")
            return None

        # Calculate daily percentage returns
        returns = data.pct_change()
        
        # --- FIX: Removed the .dropna() ---
        # The .corr() method handles NaNs by default using pairwise.
        # The .dropna() was too aggressive and was removing all data.
        corr_matrix = returns.corr()

        # If the matrix is empty or all-NaN (e.g., no overlapping data), stop.
        if corr_matrix.empty or corr_matrix.isna().all().all():
            print("Correlation matrix is empty or all NaN. Likely no overlapping data.")
            return None

        # --- Plotting the Heatmap ---
        
        # --- THEME COLORS (SLATE & SAPPHIRE) ---
        BG_COLOR = "#121A2A" # Dark Panel Blue
        TEXT_COLOR = "#FFFFFF"
        BORDER_COLOR = "#30363D"

        fig, ax = plt.subplots(figsize=(8, 5))
        fig.patch.set_facecolor(BG_COLOR)
        
        sns.heatmap(
            corr_matrix,
            annot=True,          # Show the correlation numbers
            cmap='vlag',         # A good Blue-White-Red color map
            fmt=".2f",           # Format numbers to 2 decimal places
            linewidths=.5,
            ax=ax,
            cbar_kws={"label": "Correlation"}
        )
        
        # Theme the plot
        ax.set_facecolor(BG_COLOR)
        ax.tick_params(colors=TEXT_COLOR, rotation=45)
        ax.figure.axes[-1].yaxis.label.set_color(TEXT_COLOR) # Colorbar label
        ax.figure.axes[-1].tick_params(colors=TEXT_COLOR) # Colorbar ticks
        
        for spine in ax.spines.values():
            spine.set_color(BORDER_COLOR)
            
        plt.title("Stock Price Correlation Matrix (1-Year)", color=TEXT_COLOR, fontsize=14)
        plt.tight_layout()
        
        return fig

    except Exception as e:
        print(f"Error generating correlation map: {e}")
        return None