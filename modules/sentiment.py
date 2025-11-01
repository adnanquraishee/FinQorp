from textblob import TextBlob
import matplotlib.pyplot as plt

def analyze_sentiment(headlines):
    try:
        if not headlines:
            return "No headlines to analyze.", None

        sentiments = []
        for h in headlines:
            if isinstance(h, str):
                sentiments.append(TextBlob(h).sentiment.polarity)

        if not sentiments:
            return "No valid text data for sentiment analysis.", None

        avg_sentiment = sum(sentiments) / len(sentiments)
        sentiment_summary = f"**Average Sentiment Score:** {avg_sentiment:.2f}  \n"
        sentiment_summary += "🟢 Positive" if avg_sentiment > 0 else "🔴 Negative" if avg_sentiment < 0 else "⚪ Neutral"

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.hist(sentiments, bins=10, color="skyblue", edgecolor="black")
        ax.set_title("Sentiment Distribution", fontsize=10)
        ax.set_xlabel("Sentiment Score")
        ax.set_ylabel("Frequency")
        plt.tight_layout()

        return sentiment_summary, fig

    except Exception as e:
        return f"Error analyzing sentiment: {e}", None
