from wordcloud import WordCloud, STOPWORDS
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64

class VisualizationManager:
    def __init__(self, department_colors):
        self.department_colors = department_colors

    @staticmethod
    def generate_wordcloud(data):
        """Generate wordcloud from text data."""
        stopwords = set(['to', 'the', 'and', 'for', 'of', 'in', 'on', 'with', 'a', 'an', 'as', 
                        'at', 'by', 'from', 'that', 'which', 'this', 'be', 'grant', 'Grant']) | STOPWORDS
        text = ' '.join(data.dropna())
        wc = WordCloud(
            stopwords=stopwords,
            width=900,
            height=400,
            background_color="white",
            colormap="viridis",
            collocations=True,
            regexp=r"[a-zA-Z#&]+",
            max_words=30,
            min_word_length=4,
            font_path="assets/Arial Unicode.ttf"
        ).generate(text)
        return wc

    @staticmethod
    def wordcloud_to_base64(wc):
        """Convert wordcloud to base64 string."""
        img = BytesIO()
        wc.to_image().save(img, format='PNG')
        img.seek(0)
        return base64.b64encode(img.getvalue()).decode()

    def create_department_charts(self, filtered_df, click_data=None):
        """Create pie and duration charts for departments."""
        # Pie Chart
        department_counts = filtered_df['Funding_Org:Department'].value_counts().reset_index()
        department_counts.columns = ['Department', 'Count']
        
        pie_fig = px.pie(
            department_counts,
            names='Department',
            values='Count',
            title='Share of Grants by Department',
            color='Department',
            color_discrete_map=self.department_colors
        )

        # Duration Chart
        if click_data:
            selected_department = click_data['points'][0]['label']
            duration_df = filtered_df[filtered_df['Funding_Org:Department'] == selected_department]
        else:
            duration_df = filtered_df

        max_duration = int(duration_df['Duration_(Days)'].max())
        bins = list(range(0, max_duration + 100, 100))
        labels = [f"{i}-{i+99}" for i in bins[:-1]]
        
        duration_df['Duration_Category'] = pd.cut(duration_df['Duration_(Days)'], 
                                                bins=bins, labels=labels, right=False)
        
        duration_data = duration_df.groupby(['Duration_Category', 'Funding_Org:Department'])['Identifier'].count().reset_index()
        duration_data.rename(columns={'Identifier': 'Count'}, inplace=True)

        total_counts = duration_data.groupby('Duration_Category')['Count'].sum()
        valid_categories = total_counts[total_counts > 0].index
        duration_data = duration_data[duration_data['Duration_Category'].isin(valid_categories)]

        duration_fig = px.bar(
            duration_data,
            x='Duration_Category',
            y='Count',
            color='Funding_Org:Department',
            color_discrete_map=self.department_colors,
            title='Grant Duration Analysis',
            labels={'Duration_Category': 'Duration (Days)', 
                   'Count': 'Number of Grants', 
                   'Funding_Org:Department': 'Department'},
            template='plotly_white'
        )
        
        duration_fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_gridcolor='rgba(0,0,0,0)',
            yaxis_gridcolor='rgba(0,0,0,0)'
        )

        return pie_fig, duration_fig

    def create_timeline_chart(self, filtered_df, aggregation):
        """Create timeline chart with specified aggregation."""
        time_data = filtered_df.groupby(
            pd.Grouper(key='Award_Date', freq=aggregation))['Amount_awarded'].sum().reset_index()
        time_data.rename(columns={'Award_Date': 'Time'}, inplace=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time_data['Time'],
            y=time_data['Amount_awarded'],
            mode='lines',
            fill='tozeroy',
            name='Total Amount Awarded'
        ))

        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='Total Amount Awarded (£)',
            template='plotly_white',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_gridcolor='rgba(0,0,0,0)',
            yaxis_gridcolor='rgba(0,0,0,0)'
        )
        return fig