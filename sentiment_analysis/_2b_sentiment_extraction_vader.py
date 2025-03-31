import pandas as pd
import re
import spacy  # spacy-3.8.4
import matplotlib.pyplot as plt
from collections import Counter
import os
from pathlib import Path
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

PROJECT_PATH = Path().absolute().parent

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load VADER for sentiment analysis
analyzer = SentimentIntensityAnalyzer()

def preprocess_text(text):
    """Basic text preprocessing including tokenization, lemmatization, and stopword removal."""
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Remove special characters
    text = text.lower().strip()
    doc = nlp(text)
    processed_text = ' '.join([token.lemma_ for token in doc if not token.is_stop])
    return processed_text

def analyze_sentiment(text):
    """Use VADER sentiment analysis to determine sentiment scores."""
    sentiment_scores = analyzer.polarity_scores(text)
    return sentiment_scores['compound']  # Compound score represents overall sentiment

def categorize_sentiment(score):
    """Categorizes sentiment based on VADER scores"""
    if score >= 0.5:
        return "Good Design & Quality (Pos)"
    elif 0.0 <= score < 0.5:
        return "Satisfactory & Recommended (Pos)"
    else:
        return "Needs Improvement (Neg)"

# Load sample data
review_data = pd.read_csv(os.path.join(PROJECT_PATH, "data/All_reviews.csv"))

# Preprocess text
review_data['Cleaned_Review'] = review_data['review_content'].apply(preprocess_text)

# Perform sentiment analysis
review_data['Sentiment_Score'] = review_data['Cleaned_Review'].apply(analyze_sentiment)
review_data['Sentiment'] = review_data['Sentiment_Score'].apply(categorize_sentiment)

# Visualize sentiment distribution
sentiment_counts = Counter(review_data['Sentiment'])
plt.figure(figsize=(6, 4))
plt.bar(sentiment_counts.keys(), sentiment_counts.values(), color=['green', 'blue', 'red'])
plt.xlabel("Sentiment Category")
plt.ylabel("Count")
plt.xticks(rotation=45, fontsize=8)
plt.title("Sentiment Analysis Distribution")
plt.show()

# Generate final report
report = f"""
Product Sentiment Analysis Report
---------------------------------
Total Reviews: {len(review_data)}
Positive Feedback (Good Design & Quality): {sentiment_counts.get('Good Design & Quality (Pos)', 0)}
Satisfactory Feedback (Satisfactory & Recommended): {sentiment_counts.get('Satisfactory & Recommended (Pos)', 0)}
Negative Feedback (Needs Improvement): {sentiment_counts.get('Needs Improvement (Neg)', 0)}

Recommendations:
- Address common concerns from negative feedback.
- Enhance product features based on user reviews.
- Continue maintaining high-quality standards.
"""
print(report)
