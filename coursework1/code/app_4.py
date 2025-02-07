from dash import Dash, html, dcc, Input, Output
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

# --- Layout ---
models = {'Regression': linear_model.LinearRegression,
          'Decision Tree': tree.DecisionTreeRegressor,
          'k-NN': neighbors.KNeighborsRegressor}

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Grant Funding Analysis", className="text-center mb-3 mt-3",
                    style={'color': '#2C3E50', 'font-weight': 'bold'})
        ])
    ], className="mb-4"),

    # --- Grants by Department Chart ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Grants by Department", className="mb-3 text-primary"),
                    dcc.Dropdown(
                        id='department-selector',
                        options=[{'label': dept, 'value': dept}
                                 for dept in df['Funding_Org:Department'].unique()],
                        multi=True,
                        placeholder="Select departments to compare",
                        className="mb-3"
                    ),
                    dcc.Graph(id='department-grants-chart')
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),

    # --- Grants Timeline Chart ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Grants Timeline", className="mb-3 text-primary"),
                    dcc.RangeSlider(
                        id='year-slider',
                        min=df['Award_Date'].dt.year.min(),
                        max=df['Award_Date'].dt.year.max(),
                        step=1,
                        marks={str(year): str(year) for year in sorted(df['Award_Date'].dt.year.unique())},
                        value=[df['Award_Date'].dt.year.min(), df['Award_Date'].dt.year.max()]
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
                        className="mb-3"
                    ),
                    dcc.Graph(id='timeline-chart')
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),

    # --- Word Cloud ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Word Cloud of Grant Titles", className="mb-3 text-primary"),
                    html.Label("Select Department(s):"),
                    dcc.Dropdown(
                        id='wordcloud-department-selector',
                        options=[{'label': dept, 'value': dept}
                                 for dept in df['Funding_Org:Department'].unique()],
                        multi=True,
                        placeholder="Select departments for word cloud",
                        className="mb-3"
                    ),
                    dcc.Graph(id="wordcloud", config={"displayModeBar": False})
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),

    # --- Grant Duration Analysis ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Grant Duration Analysis", className="mb-3 text-primary"),
                    dcc.Dropdown(
                        id='duration-department-selector',
                        options=[{'label': dept, 'value': dept}
                                 for dept in df['Funding_Org:Department'].unique()],
                        multi=True,
                        placeholder="Select departments",
                        className="mb-3"
                    ),
                    dcc.Graph(id='duration-chart')
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),

    # --- Top N Grants Overall ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Top N Grants Overall", className="mb-3 text-primary"),
                    dcc.Slider(
                        id='top-n-slider',
                        min=2,
                        max=10,
                        step=1,
                        value=5,
                        marks={i: str(i) for i in range(2, 11)}
                    ),
                    dcc.Graph(id='top-grants-chart')
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),

    # --- Regression Analysis Graph ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Regression Analysis", className="mb-3 text-primary"),
                    html.P("Select model:"),
                    dcc.Dropdown(
                        id='dropdown',
                        options=[{"label":k, "value":k} for k in models.keys()],
                        value='Decision Tree',
                        clearable=False
                    ),
                    dcc.Graph(id="regression-chart"),
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),

], fluid=True, style={'background-color': '#f8f9fa', 'padding': '20px'})

# --- Callbacks ---

# --- Grants by Department Chart Callback ---
@app.callback(
    Output('department-grants-chart', 'figure'),
    [Input('department-selector', 'value')]
)
def update_department_chart(selected_departments):
    if not selected_departments:
        filtered_df = df
    else:
        filtered_df = df[df['Funding_Org:Department'].isin(selected_departments)]

    # Group by department and sum the amount awarded
    department_data = filtered_df.groupby('Funding_Org:Department')['Amount_awarded'].sum().reset_index()

    # Create the bar chart
    fig = px.bar(
        department_data,
        x='Funding_Org:Department',
        y='Amount_awarded',
        title='Total Grants by Department',
        labels={'Amount_awarded': 'Total Amount Awarded (£)', 'Funding_Org:Department': 'Department'},
        template='plotly_white',
        color='Funding_Org:Department',  # Use department for color mapping
        color_discrete_map=department_colors # Apply the color mapping
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        xaxis_gridcolor='rgba(0,0,0,0)',  # Transparent gridlines
        yaxis_gridcolor='rgba(0,0,0,0)'   # Transparent gridlines
    )

    # Add drill-down interactivity
    fig.update_layout(clickmode='event+select')
    return fig

# --- Grants Timeline Chart Callback ---
@app.callback(
    Output('timeline-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('timeline-aggregation', 'value')]
)
def update_timeline_chart(years_range, aggregation):
    filtered_df = df[
        (df['Award_Date'].dt.year >= years_range[0]) &
        (df['Award_Date'].dt.year <= years_range[1])
    ]

    # Group the data by the specified time period and sum the amount awarded
    time_data = filtered_df.groupby(pd.Grouper(key='Award_Date', freq=aggregation))['Amount_awarded'].sum().reset_index()
    time_data.rename(columns={'Award_Date': 'Time'}, inplace=True)

    # Fit a polynomial regression model (best fit line)
    if len(time_data) > 1:  # Ensure there's enough data for regression
        X = np.array(range(len(time_data['Time']))).reshape(-1, 1)  # Use index as feature
        y = time_data['Amount_awarded'].values

        poly = PolynomialFeatures(degree=1)  # Linear trend line
        X_poly = poly.fit_transform(X)

        model = LinearRegression()
        model.fit(X_poly, y)

        y_poly_pred = model.predict(poly.transform(X))

        fig = go.Figure()

        # Add the area chart for total amount awarded
        fig.add_trace(go.Scatter(
            x=time_data['Time'],
            y=time_data['Amount_awarded'],
            mode='lines',
            fill='tozeroy',
            name='Total Amount Awarded'
        ))

        # Add the line chart for best fit line
        fig.add_trace(go.Scatter(
            x=time_data['Time'],
            y=y_poly_pred,
            mode='lines',
            name='Trend Line',
            marker=dict(color='red')
        ))
    else:
        # Handle the case where there's insufficient data for regression
        fig = go.Figure(data=[go.Scatter(x=time_data['Time'], y=time_data['Amount_awarded'], mode='lines+markers')])
        fig.update_layout(title='Insufficient data for trend line', template='plotly_white')

    # Update layout
    fig.update_layout(
        title='Grants Timeline',
        xaxis_title='Time',
        yaxis_title='Total Amount Awarded (£)',
        template='plotly_white'
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        xaxis_gridcolor='rgba(0,0,0,0)',  # Transparent gridlines
        yaxis_gridcolor='rgba(0,0,0,0)'   # Transparent gridlines
    )
    return fig

# --- Word Cloud Callback ---
@app.callback(
    Output('wordcloud', 'figure'),
    [Input('wordcloud-department-selector', 'value')]
)
def update_wordcloud(departments):
    filtered_df = df

    if departments:
        filtered_df = filtered_df[filtered_df['Funding_Org:Department'].isin(departments)]

    wc = generate_wordcloud(filtered_df['Title'])

    fig = go.Figure()
    fig.add_trace(go.Image(z=wc.to_array()))
    fig.update_layout(
        height=400,
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"t": 0, "b": 0, "l": 0, "r": 0},
        hovermode=False,
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return fig

# --- Grant Duration Analysis Callback ---
@app.callback(
    Output('duration-chart', 'figure'),
    [Input('duration-department-selector', 'value')]
)
def update_duration_chart(selected_departments):
    if not selected_departments:
        filtered_df = df
    else:
        filtered_df = df[df['Funding_Org:Department'].isin(selected_departments)]

    # Create duration bins
    max_duration = int(df['Duration_(Days)'].max())
    bins = list(range(0, max_duration + 100, 100))
    labels = [f"{i}-{i+99}" for i in bins[:-1]]

    # Assign duration bins to each grant
    filtered_df['Duration_Category'] = pd.cut(filtered_df['Duration_(Days)'], bins=bins, labels=labels, right=False)

    # Group by duration category and department
    duration_data = filtered_df.groupby(['Duration_Category', 'Funding_Org:Department'])['Identifier'].count().reset_index()
    duration_data.rename(columns={'Identifier': 'Count'}, inplace=True)

    # Filter out duration categories with zero counts across all departments
    total_counts = duration_data.groupby('Duration_Category')['Count'].sum()
    valid_categories = total_counts[total_counts > 0].index
    duration_data = duration_data[duration_data['Duration_Category'].isin(valid_categories)]

    # Create the bar chart
    fig = px.bar(
        duration_data,
        x='Duration_Category',
        y='Count',
        color='Funding_Org:Department',
        color_discrete_map=department_colors,
        title='Grant Duration Analysis',
        labels={'Duration_Category': 'Duration (Days)', 'Count': 'Number of Grants', 'Funding_Org:Department': 'Department'},
        template='plotly_white'
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        xaxis_gridcolor='rgba(0,0,0,0)',  # Transparent gridlines
        yaxis_gridcolor='rgba(0,0,0,0)'   # Transparent gridlines
    )
    return fig

# --- Top N Grants Overall Callback ---
@app.callback(
    Output('top-grants-chart', 'figure'),
    [Input('top-n-slider', 'value')]
)
def update_top_grants_chart(top_n):
    # Sort by amount awarded and take the top N
    top_grants = df.sort_values(by='Amount_awarded', ascending=False).head(top_n)

    # Create the bar chart
    fig = px.bar(
        top_grants,
        x='Title',
        y='Amount_awarded',
        color='Funding_Org:Department',  # Color by department
        color_discrete_map=department_colors,
        title=f'Top {top_n} Grants Overall',
        labels={'Amount_awarded': 'Amount Awarded (£)', 'Title': 'Grant Title', 'Funding_Org:Department': 'Department'},
        template='plotly_white'
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        xaxis_gridcolor='rgba(0,0,0,0)',  # Transparent gridlines
        yaxis_gridcolor='rgba(0,0,0,0)'   # Transparent gridlines
    )

    # Sort bars in descending order
    fig.update_layout(
        xaxis={'categoryorder':'total descending'}
    )

    return fig

# --- Regression Analysis Graph Callback ---
@app.callback(
    Output("regression-chart", "figure"),
    [Input('year-slider', 'value'), Input('dropdown', "value")]
)
def update_regression_chart(years_range, name):
    filtered_df = df[
        (df['Award_Date'].dt.year >= years_range[0]) &
        (df['Award_Date'].dt.year <= years_range[1])
    ]

    X = filtered_df['Duration_(Days)'].values[:, None]
    y = filtered_df['Amount_awarded']
    X = np.nan_to_num(X)
    y = np.nan_to_num(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, random_state=42)

    model = models[name]()
    model.fit(X_train, y_train)

    x_range = np.linspace(X.min(), X.max(), 100)
    y_range = model.predict(x_range.reshape(-1, 1))

    fig = go.Figure([
        go.Scatter(x=X_train.squeeze(), y=y_train,
                   name='train', mode='markers'),
        go.Scatter(x=X_test.squeeze(), y=y_test,
                   name='test', mode='markers'),
        go.Scatter(x=x_range, y=y_range,
                   name='prediction')
    ])

    fig.update_layout(
        plot_bgcolor='white',  # White background
        paper_bgcolor='white',  # White background
        xaxis_gridcolor='rgba(0,0,0,0)',  # Transparent gridlines
        yaxis_gridcolor='rgba(0,0,0,0)'   # Transparent gridlines
    )
    return fig

# --- Department Drill-Down Callback ---
@app.callback(
    Output('department-selector', 'value'),
    Input('department-grants-chart', 'clickData')
)
def drill_down(clickData):
    if clickData:
        return [clickData['points'][0]['x']]
    return []

if __name__ == '__main__':
    app.run_server(debug=True)
