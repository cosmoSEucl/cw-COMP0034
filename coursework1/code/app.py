from dash import Dash, html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud, STOPWORDS
import base64
from io import BytesIO
import sys
from pathlib import Path
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer

meta_tags = [
    {"name": "viewport", "content": "width=device-width, initial-scale=1"},
]
external_stylesheets = [dbc.themes.FLATLY]
app = Dash(__name__, external_stylesheets=external_stylesheets,
           meta_tags=meta_tags)


def process_data():
    """
    Process and load the grants data from an Excel file.

    Returns:
        pandas.DataFrame: Processed DataFrame containing grants data with
        properly formatted datetime columns.
    """
    code_directory = Path(__file__).resolve().parent
    coursework1_root = code_directory.parent
    sys.path.append(str(coursework1_root))
    excel_file_path = coursework1_root / 'data' / 'cleaned_grants_data.xlsx'
    data = pd.read_excel(excel_file_path)
    data['Award_Date'] = pd.to_datetime(data['Award_Date'])
    data = data.sort_values(by='Award_Date')
    return data


df = process_data()
date_range = df['Award_Date'].dt.year.unique()


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


df['Sentiment_Score'] = df['Description_'].apply(analyze_sentiment)


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
        min_word_length=4,
        font_path="assets/Arial Unicode.ttf"
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


def MetricCard(title, id):
    """
    Create a Bootstrap card component for displaying metrics.

    Args:
        title (str): The title of the metric card.
        id (str): The HTML ID for the card component.

    Returns:
        dbc.Card: A styled Bootstrap card component.
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


def filter_dataframe(df, departments, years_range=None):
    """
    Filter the DataFrame based on departments and year range.

    Args:
        df (pandas.DataFrame): The DataFrame to filter.
        departments (list): List of departments to include.
        years_range (list): Two-element list with start and end years.

    Returns:
        pandas.DataFrame: Filtered DataFrame based on the specified criteria.
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


@app.callback(
    [Output('total-value', 'children'),
     Output('total-number', 'children')],
    [Input('department-year-slider', 'value')]
)
def update_total_metrics(years_range):
    """
    Update the total metrics display based on the selected year range.

    Args:
        years_range (list): Two-element list containing start and end years.

    Returns:
        tuple: Updated total value (in millions) and number of grants.
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

    Args:
        years_range (list): Two-element list containing start and end years.
        click_data (dict): Data from clicks on the pie chart.

    Returns:
        tuple: Updated pie chart and duration chart figures.
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

    if click_data:
        selected_department = click_data['points'][0]['label']
        duration_df = filtered_df[
            filtered_df['Funding_Org:Department'] == selected_department
        ]
    else:
        duration_df = filtered_df

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
    duration_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_gridcolor='rgba(0,0,0,0)',
        yaxis_gridcolor='rgba(0,0,0,0)'
    )
    return pie_fig, duration_fig


@app.callback(
    Output('timeline-chart', 'figure'),
    [Input('timeline-aggregation', 'value')]
)
def update_timeline_chart(aggregation):
    """
    Update the timeline chart based on selected time aggregation.

    Args:
        aggregation (str): Time period for aggregation ('YE', 'QE', or 'ME').

    Returns:
        go.Figure: Updated timeline chart figure.
    """
    filtered_df = filter_dataframe(df, None)
    time_data = filtered_df.groupby(
        pd.Grouper(key='Award_Date', freq=aggregation),
        observed=True
    )['Amount_awarded'].sum().reset_index()
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


@app.callback(
    Output('interactive-timeline', 'figure'),
    [Input('department-selector', 'value')]
)
def update_interactive_timeline(selected_department):
    """
    Update the interactive timeline based on selected department.

    Args:
        selected_department (str): The selected department name.

    Returns:
        dict: Updated interactive timeline figure or message if no data.
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
                    'plot_bgcolor': 'rgba(0,0,0,0)'
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
                    'plot_bgcolor': 'rgba(0,0,0,0)'
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
        template='plotly_white'
    )
    return fig


@app.callback(
    Output('wordcloud', 'src'),
    [Input('wordcloud-department-selector', 'value')]
)
def update_wordcloud(selected_departments):
    """
    Update the word cloud based on selected departments.

    Args:
        selected_departments (list): List of selected department names.

    Returns:
        str: Base64 encoded image data URL for the word cloud.
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

    Args:
        top_n (int): Number of top grants to display.

    Returns:
        go.Figure: Updated sunburst chart figure.
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
        margin=dict(l=0, r=0, b=0, t=30),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return sunburst_fig


@app.callback(
    Output('department-table', 'data'),
    [Input('table-search', 'value')]
)
def update_table(search_term):
    """
    Update the data table based on search term.

    Args:
        search_term (str): Search term to filter the table data.

    Returns:
        list: List of dictionaries containing filtered table data.
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

    Args:
        selected_department (str): Name of the selected department.

    Returns:
        str: Updated title text.
    """
    return f"Grant Awards Time Series - {selected_department}"


@app.callback(
    Output('top-grants-title', 'children'),
    [Input('top-n-slider', 'value')]
)
def update_top_grants_title(top_n):
    """
    Update the top grants title based on selected number of grants.

    Args:
        top_n (int): Number of top grants selected.

    Returns:
        str: Updated title text.
    """
    return f"Top {top_n} Grants - Sunburst Chart"


app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1(
                "Grant Funding Analysis",
                className="text-center mb-3 mt-3",
                style={'color': '#2C3E50', 'font-weight': 'bold'}
            )
        ])
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(MetricCard("Total Grants Value (Millions)", id="total-value"),
                width=6),
        dbc.Col(MetricCard("Total Number of Grants", id="total-number"),
                width=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(
                        "Grants by Department",
                        className="mb-3 text-primary"),
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
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(
                        "Word Cloud of Grant Titles",
                        className="mb-3 text-primary",
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
                        className="mb-3"
                    ),
                    html.Div(
                        html.Img(id="wordcloud", style={'height': '400px'}),
                        style={
                            'display': 'flex',
                            'justifyContent': 'center'
                        }
                    )
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(
                        "Overall Grants Timeline",
                        className="mb-3 text-primary"
                    ),
                    dcc.Dropdown(
                        id='timeline-aggregation',
                        options=[
                            {'label': 'Yearly', 'value': 'YE'},
                            {'label': 'Quarterly', 'value': 'QE'},
                            {'label': 'Monthly', 'value': 'ME'}
                        ],
                        value='YE',
                        clearable=False,
                        className="mb-3"
                    ),
                    dcc.Graph(
                        id='timeline-chart',
                        style={'height': '400px'}
                    )
                ])
            ], className="shadow-sm")
        ], md=6),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(
                        id="interactive-timeline-title",
                        className="mb-3 text-primary"
                    ),
                    dcc.Dropdown(
                        id='department-selector',
                        options=[
                            {'label': dept, 'value': dept}
                            for dept in df['Funding_Org:Department'].unique()
                        ],
                        value=df['Funding_Org:Department'].iloc[0],
                        clearable=False,
                        className="mb-3"
                    ),
                    dcc.Graph(
                        id='interactive-timeline',
                        style={'height': '400px'}
                    )
                ])
            ], className="shadow-sm")
        ], md=6)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(
                        id="top-grants-title",
                        className="mb-3 text-primary",
                        style={'textAlign': 'center'}
                    ),
                    dcc.Slider(
                        id='top-n-slider',
                        min=2,
                        max=20,
                        step=1,
                        value=10,
                        marks={i: str(i) for i in range(2, 21)}
                    ),
                    html.Div(
                        dcc.Graph(id='top-grants-sunburst'),
                        style={
                            'display': 'flex',
                            'justifyContent': 'center'
                        }
                    )
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Grants Table", className="mb-3 text-primary"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Input(
                                type="search",
                                id="table-search",
                                placeholder="Search the table..."
                            ),
                        ])
                    ], className="mb-2"),
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
                        style_table={'overflowX': 'auto'},
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
                        virtualization=False,
                    ),
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),
], fluid=True, style={'background-color': '#f8f9fa', 'padding': '20px'})

if __name__ == '__main__':
    app.run_server(debug=True)

# End of app.py
# End of Coursework 1
