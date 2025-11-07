import numpy as np
import matplotlib.pyplot as plt
from textblob import TextBlob
from modules import data_fetch


def analyze_sentiment(company_name: str):
    """
    Analyze sentiment of recent news headlines for a company
    and visualize results as:
    1️⃣ A horizontal bar (Bearish → Bullish sentiment index)
    2️⃣ A pie chart of sentiment distribution
    Returns (summary string, matplotlib figure)
    """
    try:
        # --- Fetch latest headlines ---
        headlines = data_fetch.get_headlines(company_name)

        if not headlines:
            return "No recent headlines found.", None

        # Extract headline text
        processed_headlines = []
        for h in headlines:
            if isinstance(h, dict):
                if "title" in h:
                    processed_headlines.append(h["title"])
                elif "headline" in h:
                    processed_headlines.append(h["headline"])
            elif isinstance(h, str):
                processed_headlines.append(h)

        if not processed_headlines:
            return "No valid text headlines found.", None

        # --- Compute sentiment polarity for each headline ---
        sentiments = [TextBlob(str(h)).sentiment.polarity for h in processed_headlines]

        # --- Compute sentiment stats ---
        avg_sentiment = np.mean(sentiments)
        positive = sum(1 for s in sentiments if s > 0.1)
        negative = sum(1 for s in sentiments if s < -0.1)
        neutral = len(sentiments) - positive - negative

        summary = (
            f"📰 Analyzed {len(sentiments)} headlines\n\n"
            f"😊 Positive: {positive}\n"
            f"😐 Neutral: {neutral}\n"
            f"😞 Negative: {negative}\n\n"
            f"**Overall Sentiment:** {avg_sentiment:.2f}"
        )

        # --- Determine sentiment label and color (FinQorp palette) ---
        if avg_sentiment > 0.05:
            sentiment_label = "Positive 😊"
            color = "#32D600"  # FinQorp green
        elif avg_sentiment < -0.05:
            sentiment_label = "Negative 😞"
            color = "#D40000"  # FinQorp red
        else:
            sentiment_label = "Neutral 😐"
            color = "#FFCB20"  # FinQorp gold

        # --- Create combined figure ---
        fig, axes = plt.subplots(1, 2, figsize=(9, 2.5))  # 🔹 Side-by-side: bar + pie

        # ===== Chart 1: Sentiment Bar (Bearish → Bullish) =====
        ax = axes[0]
        ax.barh([0], [avg_sentiment], color=color, height=0.35)
        ax.set_xlim(-1, 1)
        ax.set_yticks([])
        ax.set_xticks([-1, 0, 1])
        ax.set_xticklabels(["Bearish", "Neutral", "Bullish"], color="white", fontsize=8)
        ax.set_title(
            f"Sentiment Index — {company_name}\n{sentiment_label} ({avg_sentiment:.2f})",
            color="white", fontsize=9
        )
        ax.set_facecolor("black")
        for spine in ax.spines.values():
            spine.set_color("white")
        ax.grid(True, color="#333333", alpha=0.25)

        # ===== Chart 2: Sentiment Distribution (Pie) =====
        ax2 = axes[1]
        sizes = [positive, neutral, negative]
        labels = ["Positive", "Neutral", "Negative"]
        colors = ["#32D600", "#FFCB20", "#D40000"]  # Updated FinQorp palette

        ax2.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
            textprops={"color": "white", "fontsize": 8},
        )
        ax2.set_title("Sentiment Breakdown", color="white", fontsize=9)
        ax2.set_facecolor("black")

        # ===== Layout & Theme =====
        fig.patch.set_facecolor("black")
        plt.tight_layout(pad=1.2)

        return summary, fig

    except Exception as e:
        return f"Error analyzing sentiment: {e}", None
