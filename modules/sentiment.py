# modules/sentiment.py
import matplotlib.pyplot as plt
from textblob import TextBlob
from modules import data_fetch

def analyze_sentiment(company_name: str):
    """
    Analyze sentiment of recent news headlines for a company.
    Returns (summary string, matplotlib figure)
    """
    try:
        headlines = data_fetch.get_headlines(company_name)

        # Handle dict or string headline formats
        if not headlines:
            return "No recent headlines found.", None

        processed_headlines = []
        for h in headlines:
            if isinstance(h, dict):
                if 'title' in h:
                    processed_headlines.append(h['title'])
                elif 'headline' in h:
                    processed_headlines.append(h['headline'])
            elif isinstance(h, str):
                processed_headlines.append(h)

        if not processed_headlines:
            return "No valid text headlines found.", None

        sentiments = []
        for headline in processed_headlines:
            blob = TextBlob(str(headline))
            sentiments.append(blob.sentiment.polarity)

        # Categorize sentiments
        positive = sum(1 for s in sentiments if s > 0.1)
        negative = sum(1 for s in sentiments if s < -0.1)
        neutral = len(sentiments) - positive - negative

        summary = (
            f"📰 Analyzed {len(sentiments)} headlines\n\n"
            f"😊 Positive: {positive}\n"
            f"😐 Neutral: {neutral}\n"
            f"😞 Negative: {negative}"
        )

        # Plot
        labels = ['Positive', 'Neutral', 'Negative']
        sizes = [positive, neutral, negative]
        colors = ['#4CAF50', '#FFC107', '#F44336']

        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.set_title(f"Sentiment — {company_name}")

        return summary, fig

    except Exception as e:
        return f"Error analyzing sentiment: {e}", None
