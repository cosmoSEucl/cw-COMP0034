from dash import Dash, html, dcc, Input, Output, dash_table, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud, STOPWORDS
import base64
from io import BytesIO
import dash.dependencies as dd
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler  # For scaling
from sklearn.model_selection import train_test_split
import itertools
from sklearn.svm import SVR
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.model_selection import train_test_split
from sklearn import linear_model, tree, neighbors

# Initialize the Dash app with a modern Bootstrap theme
meta_tags = [
    {"name": "viewport", "content": "width=device-width, initial-scale=1"},
]
external_stylesheets = [dbc.themes.FLATLY]
app = Dash(__name__, external_stylesheets=external_stylesheets, meta_tags=meta_tags)

def process_data():
    code_directory = Path(__file__).resolve().parent
    coursework1_root = code_directory.parent
    sys.path.append(str(coursework1_root))
    excel_file_path = coursework1_root / 'data' / 'cleaned_grants_data.xlsx'
    data = pd.read_excel(excel_file_path)
    data['Award_Date'] = pd.to_datetime(data['Award_Date'])  # Ensure correct datetime conversion
    data = data.sort_values(by='Award_Date')
    return data

df = process_data()

date_range = df['Award_Date'].dt.year.unique()

# --- Sentiment Analysis Function ---
def analyze_sentiment(text):
    if isinstance(text, str):
        sid = SentimentIntensityAnalyzer()
        scores = sid.polarity_scores(text)
        return scores['compound']  # Use compound score as a single measure
    else:
        return 0  # Handle missing descriptions

# Apply sentiment analysis to the DataFrame
df['Sentiment_Score'] = df['Description_'].apply(analyze_sentiment)

# --- Word Cloud Function ---
def generate_wordcloud(data):
    stopwords = set(['to', 'the', 'and', 'for', 'of', 'in', 'on', 'with', 'a', 'an', 'as', 'at', 'by', 'from', 'that', 'which', 'this', 'be', 'grant', 'Grant']) | STOPWORDS
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
    img = BytesIO()
    wc.to_image().save(img, format='PNG')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

# --- Department Color Mapping ---
department_colors = {
    'Communities and Intelligence': '#1f77b4',   # muted blue
    'Communities and Skills': '#ff7f0e',        # safety orange
    'Development, Enterprise and Environment': '#2ca02c', # cooked asparagus green
    'Team London': '#d62728',                   # brick red
    'Sports Team': '#9467bd',                   # muted purple
    'Education and Youth': '#8c564b',           # chestnut brown
    'Good Growth': '#e377c2',                  # raspberry yogurt pink
    'Communities and Social Policy': '#7f7f7f',   # middle gray
    'Skills and Employment': '#bcbd22',          # curry yellow-green
    'Culture and Creative Industries': '#17becf'  # blue-teal
}

# --- Helper Components ---
def MetricCard(title, id):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5(title, className="card-title"),
                html.Div(id=id, className="lead"),
            ]
        ),
        className="shadow-sm",
    )


# --- Layout ---
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Grant Funding Analysis", className="text-center mb-3 mt-3",
                    style={'color': '#2C3E50', 'font-weight': 'bold'})
        ])
    ], className="mb-4"),

        # --- Metrics Row ---
    dbc.Row(
        [
            dbc.Col(MetricCard("Total Grants Value (Millions)", id="total-value"), width=6),
            dbc.Col(MetricCard("Total Number of Grants", id="total-number"), width=6),
        ],
        className="mb-4",
    ),

    # --- Grants by Department Chart ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Grants by Department", className="mb-3 text-primary"),
                    dbc.Row([
                         dbc.Col(dcc.RangeSlider(
                            id='department-year-slider',
                            min=df['Award_Date'].dt.year.min(),
                            max=df['Award_Date'].dt.year.max(),
                            step=1,
                            marks={str(year): str(year) for year in sorted(df['Award_Date'].dt.year.unique())},
                            value=[df['Award_Date'].dt.year.min(), df['Award_Date'].dt.year.max()]
                        ), md=12),
                        dbc.Col(dcc.Graph(id='department-pie-chart'), md=6),  # Pie chart
                        dbc.Col(dcc.Graph(id='department-duration-chart'), md=6),  # Duration chart
                    ])
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),

    # --- Word Cloud (Full Width) ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Word Cloud of Grant Titles", className="mb-3 text-primary", style={'textAlign': 'center'}),
                    dcc.Dropdown(
                        id='wordcloud-department-selector',
                        options=[{'label': dept, 'value': dept}
                                 for dept in df['Funding_Org:Department'].unique()],
                        multi=True,
                        placeholder="Select Departments",
                        className="mb-3"
                    ),
                    html.Div(
                        html.Img(id="wordcloud", style={'height': '400px'}),
                        style={'display': 'flex', 'justifyContent': 'center'}  # Center the image
                    )
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),

    # --- Grants Timeline Chart (Half Width) ---
    dbc.Row([
        # Original Timeline Chart
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Overall Grants Timeline", className="mb-3 text-primary"),
                    dcc.Dropdown(
                        id='timeline-aggregation',
                        options=[
                            {'label': 'Yearly', 'value': 'Y'},
                            {'label': 'Quarterly', 'value': 'Q'},
                            {'label': 'Monthly', 'value': 'M'}
                        ],
                        value='Y',
                        clearable=False,
                        className="mb-3"
                    ),
                    dcc.Graph(id='timeline-chart', style={'height': '400px'})
                ])
            ], className="shadow-sm")
        ], md=6),
        
        # New Interactive Timeline
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(id="interactive-timeline-title", className="mb-3 text-primary"),
                    dcc.Dropdown(
                        id='department-selector',
                        options=[{'label': dept, 'value': dept} 
                                for dept in df['Funding_Org:Department'].unique()],
                        value=df['Funding_Org:Department'].iloc[0],  # Default to first department
                        clearable=False,
                        className="mb-3"
                    ),
                    dcc.Graph(id='interactive-timeline', style={'height': '400px'})
                ])
            ], className="shadow-sm")
        ], md=6)
    ], className="mb-4"),

    # --- Top N Grants Section (Sunburst Chart) ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(id="top-grants-title", className="mb-3 text-primary", style={'textAlign': 'center'}),
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
                        style={'display': 'flex', 'justifyContent': 'center'}
                    )
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),

    # --- Grants Table ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Grants Table", className="mb-3 text-primary"),
                      # --- Search Bar for Table ---
                    dbc.Row([
                        dbc.Col([
                            dbc.Input(type="search", id="table-search", placeholder="Search the table..."),
                         ])
                    ], className="mb-2"),
                    dash_table.DataTable(
                        id='department-table',
                        columns=[{"name": i, "id": i} for i in df.columns],
                        data=df.to_dict('records'),
                        filter_action="native",
                        sort_action="native",
                        page_action="native",
                        page_current=0,
                        page_size=10,
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'minWidth': '50px', 'width': '100px', 'maxWidth': '200px',
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

# --- Callbacks ---
# --- Data Filtering Function ---
def filter_dataframe(df, departments, years_range=None):
    filtered_df = df.copy()  # Avoid modifying the original DataFrame

    if departments:
        filtered_df = filtered_df[filtered_df['Funding_Org:Department'].isin(departments)]

    if years_range:
        filtered_df = filtered_df[
            (filtered_df['Award_Date'].dt.year >= years_range[0]) &
            (filtered_df['Award_Date'].dt.year <= years_range[1])
        ]

    return filtered_df

# --- Total Value and Number of Grants Callback ---
@app.callback(
    [Output('total-value', 'children'),
     Output('total-number', 'children')],
    [Input('department-year-slider', 'value')]
)
def update_total_metrics(years_range):
    filtered_df = filter_dataframe(df, None, years_range)

    total_value = filtered_df['Amount_awarded'].sum()
    total_value_millions = round(total_value / 1_000_000, 1)  # Convert to millions and round to 1 decimal place
    total_grants = len(filtered_df)

    return f"{total_value_millions}m", f"{total_grants:,}"

# --- Pie Chart and Duration Chart Callback ---
@app.callback(
    [Output('department-pie-chart', 'figure'),
     Output('department-duration-chart', 'figure')],
    [Input('department-year-slider', 'value'),
     Input('department-pie-chart', 'clickData')]
)
def update_pie_and_duration_chart(years_range, click_data):
    filtered_df = filter_dataframe(df, None, years_range)

    # Pie Chart: Share of grants by department
    department_counts = filtered_df['Funding_Org:Department'].value_counts().reset_index()
    department_counts.columns = ['Department', 'Count']

    pie_fig = px.pie(
        department_counts,
        names='Department',
        values='Count',
        title='Share of Grants by Department',
        color='Department',
        color_discrete_map=department_colors
    )

    # Duration Chart: Update based on clicked department in the pie chart
    if click_data:
        selected_department = click_data['points'][0]['label']
        duration_df = filtered_df[filtered_df['Funding_Org:Department'] == selected_department]
    else:
        duration_df = filtered_df  # Show all departments if no department is selected

    # Create duration bins
    max_duration = int(duration_df['Duration_(Days)'].max())
    bins = list(range(0, max_duration + 100, 100))
    labels = [f"{i}-{i+99}" for i in bins[:-1]]

    # Assign duration bins to each grant
    duration_df['Duration_Category'] = pd.cut(duration_df['Duration_(Days)'], bins=bins, labels=labels, right=False)

    # Group by duration category and department
    duration_data = duration_df.groupby(['Duration_Category', 'Funding_Org:Department'])['Identifier'].count().reset_index()
    duration_data.rename(columns={'Identifier': 'Count'}, inplace=True)

    # Filter out duration categories with zero counts across all departments
    total_counts = duration_data.groupby('Duration_Category')['Count'].sum()
    valid_categories = total_counts[total_counts > 0].index
    duration_data = duration_data[duration_data['Duration_Category'].isin(valid_categories)]

    # Create the bar chart
    duration_fig = px.bar(
        duration_data,
        x='Duration_Category',
        y='Count',
        color='Funding_Org:Department',
        color_discrete_map=department_colors,
        title='Grant Duration Analysis',
        labels={'Duration_Category': 'Duration (Days)', 'Count': 'Number of Grants', 'Funding_Org:Department': 'Department'},
        template='plotly_white'
    )
    duration_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        xaxis_gridcolor='rgba(0,0,0,0)',  # Transparent gridlines
        yaxis_gridcolor='rgba(0,0,0,0)'   # Transparent gridlines
    )
    return pie_fig, duration_fig

# --- Grants Timeline Chart Callback ---
@app.callback(
    Output('timeline-chart', 'figure'),
    [Input('timeline-aggregation', 'value')]
)
def update_timeline_chart(aggregation):
    filtered_df = filter_dataframe(df, None)

    # Group the data by the specified time period and sum the amount awarded
    time_data = filtered_df.groupby(pd.Grouper(key='Award_Date', freq=aggregation))['Amount_awarded'].sum().reset_index()
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
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        xaxis_gridcolor='rgba(0,0,0,0)',  # Transparent gridlines
        yaxis_gridcolor='rgba(0,0,0,0)'   # Transparent gridlines
    )
    return fig

@app.callback(
    Output('interactive-timeline', 'figure'),
    [Input('department-selector', 'value')]
)
def update_interactive_timeline(selected_department):
    # Filter data based on department
    filtered_df = df[df['Funding_Org:Department'] == selected_department]
    
    # Group by date and sum the amounts
    time_data = filtered_df.groupby('Award_Date')['Amount_awarded'].sum().reset_index()

    if len(time_data) <= 1:
        if not time_data.empty:
            amount = round(time_data['Amount_awarded'].iloc[0])
            return {
                'layout': {
                    'annotations': [{
                        'text': f"There is only one grant with a value of £{amount:,}",  # Format with commas
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
    
    # Create figure
    fig = go.Figure()

    # Dynamically assign color based on department_colors
    color = department_colors.get(selected_department, 'grey')  # Default to grey if not found
    
    # Add trace with department color
    fig.add_trace(
        go.Scatter(
            x=time_data['Award_Date'],
            y=time_data['Amount_awarded'],
            mode='lines',
            name='Amount Awarded',
            line=dict(color=color)  # Set line color
        )
    )
    
    # Update layout
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(count=3, label="3y", step="year", stepmode="backward"),
                    dict(count=5, label="5y", step="year", stepmode="backward"),
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

# --- Word Cloud Callback ---
@app.callback(
    Output('wordcloud', 'src'),
    [Input('wordcloud-department-selector', 'value')]
)
def update_wordcloud(selected_departments):
    if not selected_departments:
        filtered_df = df.copy()
    else:
        filtered_df = df[df['Funding_Org:Department'].isin(selected_departments)]

    wc = generate_wordcloud(filtered_df['Title'])
    img_data = wordcloud_to_base64(wc)
    return f'data:image/png;base64,{img_data}'

# --- Top Grants Callback ---
@app.callback(
    Output('top-grants-sunburst', 'figure'),
    [Input('top-n-slider', 'value')]
)
def update_top_grants_sunburst(top_n):
    # Aggregate grants with the same title
    aggregated_grants = df.groupby(['Title', 'Funding_Org:Department'], as_index=False)['Amount_awarded'].sum()

    # Get the top N grants
    top_grants = aggregated_grants.nlargest(top_n, 'Amount_awarded')

    # Sunburst Chart
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

# --- Table Data Callback with Search ---
@app.callback(
    Output('department-table', 'data'),
    [Input('table-search', 'value')]
)
def update_table(search_term):
    if search_term:
        # Apply the search filter
        filtered_df = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
        data = filtered_df.to_dict('records')
    else:
        # If no search term, return the entire dataset
        data = df.to_dict('records')
    return data

# --- Dynamic Titles Callback ---
@app.callback(
    Output('interactive-timeline-title', 'children'),
    [Input('department-selector', 'value')]
)
def update_interactive_timeline_title(selected_department):
    return f"Grant Awards Time Series - {selected_department}"

@app.callback(
    Output('top-grants-title', 'children'),
    [Input('top-n-slider', 'value')]
)
def update_top_grants_title(top_n):
    return f"Top {top_n} Grants - Sunburst Chart"

if __name__ == '__main__':
    app.run_server(debug=True)
