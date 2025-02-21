import pandas as pd
from pathlib import Path
import sys
from sklearn.preprocessing import StandardScaler
from nltk.sentiment import SentimentIntensityAnalyzer
import numpy as np

class DataProcessor:
    def __init__(self):
        self.df = self.process_data()
        self.df['Sentiment_Score'] = self.df['Description_'].apply(self.analyze_sentiment)

    def process_data(self):
        """Load and process the grants data."""
        code_directory = Path(__file__).resolve().parent
        coursework1_root = code_directory.parent
        sys.path.append(str(coursework1_root))
        excel_file_path = coursework1_root / 'data' / 'cleaned_grants_data.xlsx'
        data = pd.read_excel(excel_file_path)
        data['Award_Date'] = pd.to_datetime(data['Award_Date'])
        return data.sort_values(by='Award_Date')

    @staticmethod
    def analyze_sentiment(text):
        """Analyze sentiment of text using NLTK."""
        if isinstance(text, str):
            sid = SentimentIntensityAnalyzer()
            scores = sid.polarity_scores(text)
            return scores['compound']
        return 0

    def filter_dataframe(self, departments=None, years_range=None):
        """Filter dataframe based on departments and years."""
        filtered_df = self.df.copy()

        if departments:
            filtered_df = filtered_df[filtered_df['Funding_Org:Department'].isin(departments)]

        if years_range:
            filtered_df = filtered_df[
                (filtered_df['Award_Date'].dt.year >= years_range[0]) &
                (filtered_df['Award_Date'].dt.year <= years_range[1])
            ]

        return filtered_df

    def get_date_range(self):
        """Get unique years in the dataset."""
        return self.df['Award_Date'].dt.year.unique()