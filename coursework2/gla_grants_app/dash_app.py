import os
from dash import Dash, html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud, STOPWORDS
import base64
from io import BytesIO
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
from pathlib import Path

# Download NLTK resources
try:
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        # Try to download with SSL verification disabled if necessary
        import ssl
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context
        nltk.download('vader_lexicon', quiet=True)
except Exception as e:
    print(f"Warning: Could not download NLTK vader_lexicon. Sentiment analysis might not work. Error: {e}")
    # Define a fallback sentiment analyzer that returns neutral sentiment
    def analyze_sentiment(text):
        return 0

def process_data():
    """
    Process and load the grants data from an Excel file.

    Returns:
        pandas.DataFrame: Processed DataFrame containing grants data with
        properly formatted datetime columns.
    """
    # Define the path to the Excel file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    excel_file_path = os.path.join(project_root, 'coursework1', 'data', 'cleaned_grants_data.xlsx')
    
    # Check if the file exists
    if not os.path.exists(excel_file_path):
        # If not, look in alternative locations
        alternative_paths = [
            os.path.join(project_root, 'data', 'cleaned_grants_data.xlsx'),
            os.path.join(current_dir, '..', 'data', 'cleaned_grants_data.xlsx'),
            os.path.join(current_dir, 'data', 'cleaned_grants_data.xlsx')
        ]
        
        for path in alternative_paths:
            if os.path.exists(path):
                excel_file_path = path
                break
        else:
            # If file not found anywhere, use sample data
            print("Excel file not found. Using sample data from the database instead.")
            from coursework2.gla_grants_app import db
            from coursework2.gla_grants_app.models import Grant
            
            grants = db.session.query(Grant).all()
            data = pd.DataFrame([{
                'Identifier': g.id,
                'Title': g.title,
                'Description_': g.description,
                'Amount_awarded': g.amount_awarded,
                'Award_Date': g.award_date,
                'Funding_Org:Department': g.funding_org_department,
                'Recipient_Org:Name': g.recipient_org_name,
                'Duration_(Days)': 365  # Sample duration
            } for g in grants])
            
            data['Award_Date'] = pd.to_datetime(data['Award_Date'])
            data = data.sort_values(by='Award_Date')
            return data
    
    # Load and process the data
    data = pd.read_excel(excel_file_path)
    data['Award_Date'] = pd.to_datetime(data['Award_Date'])
    data = data.sort_values(by='Award_Date')
    return data

def analyze_sentiment(text):
    """
    Analyze the sentiment of a given text using NLTK's
    SentimentIntensityAnalyzer.

    Args:
        text (str): The text to analyze.

    Returns:
        float: The compound sentiment score (-1 to 1) or 0 if text is invalid.
    """
    if isinstance(text, str):
        sid = SentimentIntensityAnalyzer()
        scores = sid.polarity_scores(text)
        return scores['compound']
    else:
        return 0

def generate_wordcloud(data):
    """
    Generate a WordCloud object from the provided text data.

    Args:
        data (pandas.Series): Series containing text data for
        word cloud generation.

    Returns:
        WordCloud: Generated WordCloud object with customized parameters.
    """
    stopwords = set(['to', 'the', 'and', 'for', 'of', 'in', 'on', 'with', 'a',
                     'an', 'as', 'at', 'by', 'from', 'that', 'which', 'this',
                     'be', 'grant', 'Grant']) | STOPWORDS
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
        min_word_length=4
    ).generate(text)
    return wc

def wordcloud_to_base64(wc):
    """
    Convert a WordCloud object to a base64 encoded string.

    Args:
        wc (WordCloud): WordCloud object to convert.

    Returns:
        str: Base64 encoded string representation of the WordCloud image.
    """
    img = BytesIO()
    wc.to_image().save(img, format='PNG')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def init_dash(server):
    """
    Initialize the Dash app as part of the Flask server.

    Args:
        server (Flask): The Flask application instance.

    Returns:
        Dash: The Dash application instance.
    """
    # Load and process data
    df = process_data()
    
    # Add sentiment analysis
    df['Sentiment_Score'] = df['Description_'].apply(analyze_sentiment)
    
    # Define department colors
    department_colors = {
        'Communities and Intelligence': '#1f77b4',
        'Communities and Skills': '#ff7f0e',
        'Development, Enterprise and Environment': '#2ca02c',
        'Team London': '#d62728',
        'Sports Team': '#9467bd',
        'Education and Youth': '#8c564b',
        'Good Growth': '#e377c2',
        'Communities and Social Policy': '#7f7f7f',
        'Skills and Employment': '#bcbd22',
        'Culture and Creative Industries': '#17becf'
    }
    
    # Initialize Dash app
    meta_tags = [
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ]
    external_stylesheets = [dbc.themes.FLATLY]
    
    # Create assets folder if it doesn't exist
    assets_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
    if not os.path.exists(assets_folder):
        os.makedirs(assets_folder)
    
    app = Dash(
        __name__,
        server=server,
        url_base_pathname='/dash/',
        external_stylesheets=external_stylesheets,
        meta_tags=meta_tags,
        suppress_callback_exceptions=True,
        assets_folder=assets_folder
    )
    
    # Create metric card component
    def MetricCard(title, id):
        """
        Create a Bootstrap card component for displaying metrics.
        """
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H5(title, className="card-title"),
                    html.Div(id=id, className="lead"),
                ]
            ),
            className="shadow-sm",
        )
    
    # Define filter function
    def filter_dataframe(df, departments, years_range=None):
        """
        Filter the DataFrame based on departments and year range.
        """
        filtered_df = df.copy()

        if departments:
            filtered_df = filtered_df[
                filtered_df['Funding_Org:Department'].isin(departments)
            ]

        if years_range:
            filtered_df = filtered_df[
                (filtered_df['Award_Date'].dt.year >= years_range[0]) &
                (filtered_df['Award_Date'].dt.year <= years_range[1])
            ]

        return filtered_df
    
    # Define app layout - optimized for iframe embedding with white background
    app.layout = dbc.Container([
        # Metrics cards
        dbc.Row([
            dbc.Col(MetricCard("Total Grants Value (Millions)", id="total-value"),
                    width=6),
            dbc.Col(MetricCard("Total Number of Grants", id="total-number"),
                    width=6),
        ], className="mb-3"),  # Reduced margin for iframe

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(
                            "Grants by Department",
                            className="mb-2 text-primary"),  # Smaller header
                        dbc.Row([
                            dbc.Col(
                                dcc.RangeSlider(
                                    id='department-year-slider',
                                    min=df['Award_Date'].dt.year.min(),
                                    max=df['Award_Date'].dt.year.max(),
                                    step=1,
                                    marks={
                                        str(year): str(year)
                                        for year in sorted(
                                            df['Award_Date'].dt.year.unique()
                                        )
                                    },
                                    value=[
                                        df['Award_Date'].dt.year.min(),
                                        df['Award_Date'].dt.year.max()
                                    ]
                                ),
                                md=12
                            ),
                            dbc.Col(dcc.Graph(id='department-pie-chart'), md=6),
                            dbc.Col(
                                dcc.Graph(
                                    id='department-duration-chart'), md=6),
                        ])
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-3"),  # Reduced margin for iframe

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(
                            "Word Cloud of Grant Titles",
                            className="mb-2 text-primary",
                            style={'textAlign': 'center'}
                        ),
                        dcc.Dropdown(
                            id='wordcloud-department-selector',
                            options=[
                                {'label': dept, 'value': dept}
                                for dept in df['Funding_Org:Department'].unique()
                            ],
                            multi=True,
                            placeholder="Select Departments",
                            className="mb-2"  # Reduced margin
                        ),
                        html.Div(
                            html.Img(id="wordcloud", style={'height': '350px'}),  # Reduced height for iframe
                            style={
                                'display': 'flex',
                                'justifyContent': 'center'
                            }
                        )
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-3"),  # Reduced margin for iframe

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(
                            "Overall Grants Timeline",
                            className="mb-2 text-primary"  # Reduced margin
                        ),
                        dcc.Dropdown(
                            id='timeline-aggregation',
                            options=[
                                {'label': 'Yearly', 'value': 'Y'},
                                {'label': 'Quarterly', 'value': 'Q'},
                                {'label': 'Monthly', 'value': 'M'}
                            ],
                            value='Y',
                            clearable=False,
                            className="mb-2"  # Reduced margin
                        ),
                        dcc.Graph(
                            id='timeline-chart',
                            style={'height': '350px'}  # Reduced height for iframe
                        )
                    ])
                ], className="shadow-sm")
            ], md=6),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(
                            id="interactive-timeline-title",
                            className="mb-2 text-primary"  # Reduced margin
                        ),
                        dcc.Dropdown(
                            id='department-selector',
                            options=[
                                {'label': dept, 'value': dept}
                                for dept in df['Funding_Org:Department'].unique()
                            ],
                            value=df['Funding_Org:Department'].iloc[0],
                            clearable=False,
                            className="mb-2"  # Reduced margin
                        ),
                        dcc.Graph(
                            id='interactive-timeline',
                            style={'height': '350px'}  # Reduced height for iframe
                        )
                    ])
                ], className="shadow-sm")
            ], md=6)
        ], className="mb-3"),  # Reduced margin for iframe

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(
                            id="top-grants-title",
                            className="mb-2 text-primary",
                            style={'textAlign': 'center'}
                        ),
                        dcc.Slider(
                            id='top-n-slider',
                            min=2,
                            max=20,
                            step=1,
                            value=10,
                            marks={i: str(i) for i in range(2, 21, 2)}
                        ),
                        html.Div(
                            dcc.Graph(id='top-grants-sunburst', style={'height': '350px'}),  # Reduced height for iframe
                            style={
                                'display': 'flex',
                                'justifyContent': 'center'
                            }
                        )
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-3"),  # Reduced margin for iframe

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Grants Table", className="mb-2 text-primary"),  # Smaller header
                        dbc.Row([
                            dbc.Col([
                                dbc.Input(
                                    type="search",
                                    id="table-search",
                                    placeholder="Search the table..."
                                ),
                            ])
                        ], className="mb-2"),  # Reduced margin
                        dash_table.DataTable(
                            id='department-table',
                            columns=[
                                {"name": i, "id": i} for i in df.columns
                            ],
                            data=df.to_dict('records'),
                            filter_action="native",
                            sort_action="native",
                            page_action="native",
                            page_current=0,
                            page_size=10,
                            style_table={'overflowX': 'auto', 'height': '350px'},  # Added fixed height for iframe
                            style_cell={
                                'minWidth': '50px',
                                'width': '100px',
                                'maxWidth': '200px',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                            },
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold',
                                'textAlign': 'center'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(248, 248, 248)'
                                }
                            ],
                            fixed_rows={'headers': True},
                            virtualization=True,  # Enable for better performance in iframe
                        ),
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-3"),  # Reduced margin for iframe
    ], fluid=True, style={'background-color': '#ffffff', 'padding': '10px'})  # White background with reduced padding for iframe
    
    # Define callbacks
    @app.callback(
        [Output('total-value', 'children'),
         Output('total-number', 'children')],
        [Input('department-year-slider', 'value')]
    )
    def update_total_metrics(years_range):
        """
        Update the total metrics display based on the selected year range.
        """
        filtered_df = filter_dataframe(df, None, years_range)
        total_value = filtered_df['Amount_awarded'].sum()
        total_value_millions = round(total_value / 1_000_000, 1)
        total_grants = len(filtered_df)
        return f"{total_value_millions}m", f"{total_grants:,}"
    
    @app.callback(
        [Output('department-pie-chart', 'figure'),
         Output('department-duration-chart', 'figure')],
        [Input('department-year-slider', 'value'),
         Input('department-pie-chart', 'clickData')]
    )
    def update_pie_and_duration_chart(years_range, click_data):
        """
        Update the pie chart and duration chart based on
        selected year range and clicks.
        """
        filtered_df = filter_dataframe(df, None, years_range)

        department_counts = filtered_df['Funding_Org:Department'].value_counts()
        department_counts = department_counts.reset_index()
        department_counts.columns = ['Department', 'Count']

        pie_fig = px.pie(
            department_counts,
            names='Department',
            values='Count',
            title='Share of Grants by Department',
            color='Department',
            color_discrete_map=department_colors
        )
        # Make the pie chart more compact for iframe
        pie_fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor='rgba(0,0,0,0)')

        if click_data:
            selected_department = click_data['points'][0]['label']
            duration_df = filtered_df[
                filtered_df['Funding_Org:Department'] == selected_department
            ]
        else:
            duration_df = filtered_df

        if 'Duration_(Days)' not in duration_df.columns:
            duration_df['Duration_(Days)'] = 365  # Default if column doesn't exist

        max_duration = int(duration_df['Duration_(Days)'].max())
        bins = list(range(0, max_duration + 100, 100))
        labels = [f"{i}-{i+99}" for i in bins[:-1]]

        duration_df = duration_df.copy()
        duration_df['Duration_Category'] = pd.cut(
            duration_df['Duration_(Days)'],
            bins=bins,
            labels=labels,
            right=False
        )

        duration_data = duration_df.groupby(
            ['Duration_Category', 'Funding_Org:Department'],
            observed=True
        )['Identifier'].count().reset_index()
        duration_data.rename(columns={'Identifier': 'Count'}, inplace=True)

        total_counts = duration_data.groupby('Duration_Category',
                                            observed=True)['Count'].sum()
        valid_categories = total_counts[total_counts > 0].index
        duration_data = duration_data[
            duration_data['Duration_Category'].isin(valid_categories)
        ]

        duration_fig = px.bar(
            duration_data,
            x='Duration_Category',
            y='Count',
            color='Funding_Org:Department',
            color_discrete_map=department_colors,
            title='Grant Duration Analysis',
            labels={
                'Duration_Category': 'Duration (Days)',
                'Count': 'Number of Grants',
                'Funding_Org:Department': 'Department'
            },
            template='plotly_white'
        )
        # Make the duration chart more compact for iframe
        duration_fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0.02)',  # Very light gray for plot area
            paper_bgcolor='rgba(0,0,0,0)',    # Transparent paper background
            xaxis_gridcolor='rgba(0,0,0,0.1)',
            yaxis_gridcolor='rgba(0,0,0,0.1)',
            margin=dict(l=20, r=20, t=30, b=20)
        )
        return pie_fig, duration_fig
    
    @app.callback(
        Output('timeline-chart', 'figure'),
        [Input('timeline-aggregation', 'value')]
    )
    def update_timeline_chart(aggregation):
        """
        Update the timeline chart based on selected time aggregation.
        """
        filtered_df = filter_dataframe(df, None)
        
        # Check if DataFrame is empty or Award_Date column is missing
        if filtered_df.empty or 'Award_Date' not in filtered_df.columns:
            # Return an empty figure with a message
            fig = go.Figure()
            fig.update_layout(
                annotations=[{
                    'text': 'No data available for this time period',
                    'showarrow': False,
                    'font': {'size': 16},
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': 0.5
                }],
                xaxis=dict(title='Time'),
                yaxis=dict(title='Total Amount Awarded (£)'),
                template='plotly_white',
                plot_bgcolor='rgba(0,0,0,0.02)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=350
            )
            return fig
            
        # Ensure Award_Date is datetime type
        if not pd.api.types.is_datetime64_any_dtype(filtered_df['Award_Date']):
            filtered_df['Award_Date'] = pd.to_datetime(filtered_df['Award_Date'], errors='coerce')
            # Drop rows where date conversion failed
            filtered_df = filtered_df.dropna(subset=['Award_Date'])
            
        # Check if we still have data after cleaning
        if filtered_df.empty:
            fig = go.Figure()
            fig.update_layout(
                annotations=[{
                    'text': 'No valid date information available',
                    'showarrow': False,
                    'font': {'size': 16},
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': 0.5
                }],
                xaxis=dict(title='Time'),
                yaxis=dict(title='Total Amount Awarded (£)'),
                template='plotly_white',
                plot_bgcolor='rgba(0,0,0,0.02)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=350
            )
            return fig

        # Adapt aggregation based on data range
        min_date = filtered_df['Award_Date'].min()
        max_date = filtered_df['Award_Date'].max()
        date_range = (max_date - min_date).days
        
        if aggregation == 'YE' and date_range < 365:
            # If less than a year of data, use quarterly
            used_aggregation = 'QE'
        elif aggregation == 'QE' and date_range < 90:
            # If less than 3 months, use monthly
            used_aggregation = 'ME'
        elif aggregation == 'ME' and date_range < 30:
            # If less than a month, use weekly
            used_aggregation = 'W'
        else:
            used_aggregation = aggregation
            
        # Group data by time period
        time_data = filtered_df.groupby(
            pd.Grouper(key='Award_Date', freq=used_aggregation),
            observed=True
        )['Amount_awarded'].sum().reset_index()
        
        # Ensure we have data after grouping
        if time_data.empty or time_data['Amount_awarded'].sum() == 0:
            # If no data after grouping, try a different approach - directly use all points
            time_data = filtered_df[['Award_Date', 'Amount_awarded']].copy()
            time_data = time_data.sort_values('Award_Date')
            
        time_data.rename(columns={'Award_Date': 'Time'}, inplace=True)

        # Create the figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time_data['Time'],
            y=time_data['Amount_awarded'],
            mode='lines+markers',  # Add markers to see individual data points
            fill='tozeroy',
            name='Total Amount Awarded',
            line=dict(width=3, color='#3498db'),  # Thicker line, specific color
            marker=dict(size=6)  # Make markers more visible
        ))

        # Calculate y-axis range with proper padding
        y_max = time_data['Amount_awarded'].max() if not time_data.empty else 1
        y_min = time_data['Amount_awarded'].min() if not time_data.empty else 0
        y_padding = (y_max - y_min) * 0.1 if y_max > y_min else y_max * 0.1

        # Improve layout with better axis ranges
        fig.update_layout(
            title={
                'text': f"Grant Amounts Over Time ({used_aggregation})",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis=dict(
                title='Time Period',
                titlefont=dict(size=12),
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)'
            ),
            yaxis=dict(
                title='Total Amount Awarded (£)',
                titlefont=dict(size=12),
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                range=[max(0, y_min - y_padding), y_max + y_padding]
            ),
            template='plotly_white',
            plot_bgcolor='rgba(0,0,0,0.02)',  # Very light gray for plot area
            paper_bgcolor='rgba(0,0,0,0)',    # Transparent paper background
            margin=dict(l=20, r=20, t=40, b=20),  # More compact for iframe
            height=350
        )
        return fig
    
    @app.callback(
        Output('interactive-timeline', 'figure'),
        [Input('department-selector', 'value')]
    )
    def update_interactive_timeline(selected_department):
        """
        Update the interactive timeline based on selected department.
        """
        filtered_df = df[df['Funding_Org:Department'] == selected_department]
        time_data = filtered_df.groupby('Award_Date')['Amount_awarded'].sum()
        time_data = time_data.reset_index()

        if len(time_data) <= 1:
            if not time_data.empty:
                amount = round(time_data['Amount_awarded'].iloc[0])
                return {
                    'layout': {
                        'annotations': [{
                            'text':
                            f"There is only one grant with a value of £{amount:,}",
                            'showarrow': False,
                            'font': {'size': 16}
                        }],
                        'xaxis': {'visible': False},
                        'yaxis': {'visible': False},
                        'paper_bgcolor': 'rgba(0,0,0,0)',
                        'plot_bgcolor': 'rgba(255,255,255,1)',  # White plot background,
                        'margin': dict(l=20, r=20, t=10, b=20)  # More compact for iframe
                    }
                }
            else:
                return {
                    'layout': {
                        'annotations': [{
                            'text': "No grants found for this department.",
                            'showarrow': False,
                            'font': {'size': 16}
                        }],
                        'xaxis': {'visible': False},
                        'yaxis': {'visible': False},
                        'paper_bgcolor': 'rgba(0,0,0,0)',
                        'plot_bgcolor': 'rgba(255,255,255,1)',  # White plot background,
                        'margin': dict(l=20, r=20, t=10, b=20)  # More compact for iframe
                    }
                }

        fig = go.Figure()
        color = department_colors.get(selected_department, 'grey')

        fig.add_trace(
            go.Scatter(
                x=time_data['Award_Date'],
                y=time_data['Amount_awarded'],
                mode='lines',
                name='Amount Awarded',
                line=dict(color=color)
            )
        )

        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=3, label="3m", step="month",
                            stepmode="backward"),
                        dict(count=6, label="6m", step="month",
                            stepmode="backward"),
                        dict(count=1, label="1y", step="year",
                            stepmode="backward"),
                        dict(count=3, label="3y", step="year",
                            stepmode="backward"),
                        dict(count=5, label="5y", step="year",
                            stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date"
            ),
            yaxis_title='Amount Awarded (£)',
            template='plotly_white',
            margin=dict(l=20, r=20, t=10, b=20)  # More compact for iframe
        )
        return fig
    
    @app.callback(
        Output('wordcloud', 'src'),
        [Input('wordcloud-department-selector', 'value')]
    )
    def update_wordcloud(selected_departments):
        """
        Update the word cloud based on selected departments.
        """
        if not selected_departments:
            filtered_df = df.copy()
        else:
            filtered_df = df[
                df['Funding_Org:Department'].isin(selected_departments)]

        wc = generate_wordcloud(filtered_df['Title'])
        img_data = wordcloud_to_base64(wc)
        return f'data:image/png;base64,{img_data}'
    
    @app.callback(
        Output('top-grants-sunburst', 'figure'),
        [Input('top-n-slider', 'value')]
    )
    def update_top_grants_sunburst(top_n):
        """
        Update the sunburst chart showing top N grants by value.
        """
        aggregated_grants = df.groupby(
            ['Title', 'Funding_Org:Department'],
            as_index=False
        )['Amount_awarded'].sum()

        top_grants = aggregated_grants.nlargest(top_n, 'Amount_awarded')

        sunburst_fig = px.sunburst(
            top_grants,
            path=['Funding_Org:Department', 'Title'],
            values='Amount_awarded',
            color='Funding_Org:Department',
            color_discrete_map=department_colors
        )

        sunburst_fig.update_layout(
            margin=dict(l=0, r=0, b=0, t=10),
            plot_bgcolor='rgba(0,0,0,0.02)',  # Very light gray for plot area
            paper_bgcolor='rgba(0,0,0,0)'     # Transparent paper background
        )

        return sunburst_fig
    
    @app.callback(
        Output('department-table', 'data'),
        [Input('table-search', 'value')]
    )
    def update_table(search_term):
        """
        Update the data table based on search term.
        """
        if search_term:
            filtered_df = df[
                df.apply(
                    lambda row: row.astype(str).str.contains(
                        search_term,
                        case=False
                    ).any(),
                    axis=1
                )
            ]
            data = filtered_df.to_dict('records')
        else:
            data = df.to_dict('records')
        return data
    
    @app.callback(
        Output('interactive-timeline-title', 'children'),
        [Input('department-selector', 'value')]
    )
    def update_interactive_timeline_title(selected_department):
        """
        Update the interactive timeline title based on selected department.
        """
        return f"Grant Awards Time Series - {selected_department}"
    
    @app.callback(
        Output('top-grants-title', 'children'),
        [Input('top-n-slider', 'value')]
    )
    def update_top_grants_title(top_n):
        """
        Update the top grants title based on selected number of grants.
        """
        return f"Top {top_n} Grants - Sunburst Chart"
    
    # Create the custom CSS file
    css_content = """
    /* Custom styles for embedded dashboard */
    body {
        margin: 0;
        padding: 0;
        background-color: #ffffff !important;
    }

    .container-fluid {
        padding-left: 10px !important;
        padding-right: 10px !important;
        background-color: #ffffff !important;
    }

    .card {
        margin-bottom: 15px !important;
    }

    h4 {
        font-size: 1.2rem !important;
        margin-bottom: 10px !important;
    }

    .mb-3 {
        margin-bottom: 0.7rem !important;
    }

    /* Make elements more compact for iframe display */
    .dash-graph {
        margin-bottom: 0 !important;
    }
    
    /* Fix transparent element issues */
    .dash-spreadsheet-container .dash-spreadsheet-inner th,
    .dash-spreadsheet-container .dash-spreadsheet-inner td {
        background-color: inherit !important;
    }
    """
    
    # Write the custom CSS file to the assets folder
    css_path = os.path.join(assets_folder, 'custom.css')
    try:
        with open(css_path, 'w') as f:
            f.write(css_content)
    except Exception as e:
        print(f"Warning: Could not write custom CSS file: {e}")
    
    return app