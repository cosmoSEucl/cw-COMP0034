from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from wordcloud import WordCloud, STOPWORDS
import base64
from io import BytesIO
import dash.dependencies as dd
import sys
from pathlib import Path

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
    data = data.sort_values(by='Award_Date')
    return data

df = process_data()

date_range = df['Award_Date'].dt.year.unique()

# Function to generate the word cloud image with exclusions
def generate_wordcloud(data):
    stopwords = set(['to', 'the', 'and', 'for', 'of', 'in', 'on', 'with', 'a', 'an', 'as', 'at', 'by', 'from', 'that', 'which', 'this', 'be', 'grant', 'Grant']) | STOPWORDS
    text = ' '.join(data.dropna())  # Join all titles into one large text string
    wc = WordCloud(
        stopwords=stopwords,
        width=900,
        height=400,
        background_color="white",  # Set background color to white
        colormap="viridis",
        collocations=True,
        regexp=r"[a-zA-Z#&]+",
        max_words=30,
        min_word_length=4,
        font_path="assets/Arial Unicode.ttf"  # Specify a suitable font path if needed
    ).generate(text)
    return wc

# Function to convert word cloud image to base64
def wordcloud_to_base64(wc):
    img = BytesIO()
    wc.to_image().save(img, format='PNG')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Grant Funding Analysis", className="text-center mb-3 mt-3",
                    style={'color': '#2C3E50', 'font-weight': 'bold'})
        ])
    ], className="mb-4"),
    
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
                    dcc.Graph(id='timeline-chart')
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),
    
    # New Row for Word Cloud with Dropdown Filters (Removed Year Range Slider for Word Cloud)
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Word Cloud of Grant Titles", className="mb-3 text-primary"),
                    
                    # Add a department filter for the word cloud
                    html.Label("Select Department(s):"),
                    dcc.Dropdown(
                        id='wordcloud-department-selector',
                        options=[{'label': dept, 'value': dept} 
                                 for dept in df['Funding_Org:Department'].unique()],
                        multi=True,
                        placeholder="Select departments for word cloud",
                        className="mb-3"
                    ),
                    
                    # Word cloud graph
                    dcc.Graph(id="wordcloud", config={"displayModeBar": False})
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),
], fluid=True, style={'background-color': '#f8f9fa', 'padding': '20px'})

@app.callback(
    Output('department-grants-chart', 'figure'),
    [Input('department-selector', 'value')]
)
def update_department_chart(selected_departments):
    if not selected_departments:
        filtered_df = df
    else:
        filtered_df = df[df['Funding_Org:Department'].isin(selected_departments)]
    
    fig = px.bar(
        filtered_df.groupby('Funding_Org:Department')['Amount_awarded'].sum().reset_index(),
        x='Funding_Org:Department',
        y='Amount_awarded',
        title='Total Grants by Department',
        labels={'Amount_awarded': 'Total Amount Awarded (£)', 'Funding_Org:Department': 'Department'},
        template='plotly_white'
    )
    return fig

@app.callback(
    Output('timeline-chart', 'figure'),
    [Input('year-slider', 'value')]
)
def update_timeline_chart(years_range):
    filtered_df = df[
        (df['Award_Date'].dt.year >= years_range[0]) &
        (df['Award_Date'].dt.year <= years_range[1])
    ]
    
    yearly_data = filtered_df.groupby(filtered_df['Award_Date'].dt.year)['Amount_awarded'].sum().reset_index()
    yearly_data.rename(columns={'Award_Date': 'Year'}, inplace=True)
    
    fig = px.line(
        yearly_data,
        x='Year',
        y='Amount_awarded',
        title='Grants Timeline',
        labels={'Amount_awarded': 'Total Amount Awarded (£)', 'Year': 'Year'},
        template='plotly_white'
    )
    return fig

@app.callback(
    Output('wordcloud', 'figure'),
    [Input('wordcloud-department-selector', 'value')]
)
def update_wordcloud(departments):
    filtered_df = df
    
    if departments:
        filtered_df = filtered_df[filtered_df['Funding_Org:Department'].isin(departments)]
    
    wc = generate_wordcloud(filtered_df['Title'])
    
    # Create the plotly figure using go.Image
    fig = go.Figure()
    fig.add_trace(go.Image(z=wc.to_array()))  # Add the word cloud image to the plot
    fig.update_layout(
        height=400,
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"t": 0, "b": 0, "l": 0, "r": 0},
        hovermode=False,
        paper_bgcolor="white",  # Set paper background to white
        plot_bgcolor="white",  # Set plot background to white
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
