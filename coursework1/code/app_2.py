from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import pandas as pd
import sys

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
    data = data.sort_values(by='Award_Date')  # Sort rows by Award_Date in chronological order
    return data

df = process_data()

# Improved Layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1("Grant Funding Analysis", 
                        className="text-center mb-3 mt-3",
                        style={'color': '#2C3E50', 'font-weight': 'bold'})
            ], style={'background-color': '#f8f9fa', 'padding': '20px', 'border-radius': '10px'})
        ])
    ], className="mb-4"),
    
    # Department Grants Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Grants by Department", 
                           className="mb-3 text-primary",
                           style={'font-weight': 'bold'}),
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
    
    # Timeline Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Grants Timeline", 
                           className="mb-3 text-primary",
                           style={'font-weight': 'bold'}),
                    html.Div([
                        dcc.RangeSlider(
                            id='year-slider',
                            min=df['Award_Date'].astype(int).min(),
                            max=df['Award_Date'].astype(int).max(),
                            step=1,
                            marks={str(year): str(year) 
                                  for year in sorted(df['Award_Date'].astype(int).unique())},
                            value=[df['Award_Date'].astype(int).min(), 
                                  df['Award_Date'].astype(int).max()]
                        )
                    ], style={'padding': '0 20px'}),
                    dcc.Graph(id='timeline-chart')
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),
    
    # Animated Bubble Chart Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Grant Distribution Over Time", 
                           className="mb-3 text-primary",
                           style={'font-weight': 'bold'}),
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Button(
                                    'Play/Pause',
                                    id='animation-button',
                                    n_clicks=0,
                                    className="btn btn-primary mb-3"
                                )
                            ])
                        ]),
                        dcc.Graph(id='bubble-chart'),
                        dcc.Interval(
                            id='animation-interval',
                            interval=1500,  # 1.5 seconds between frames
                            n_intervals=0,
                            max_intervals=-1
                        )
                    ])
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
        labels={'Amount_awarded': 'Total Amount Awarded (£)',
                'Funding_Org:Department': 'Department'},
        template='plotly_white'
    )
    
    fig.update_layout(
        xaxis_title="Department",
        yaxis_title="Total Amount Awarded (£)",
        bargap=0.2,
        height=500,
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Arial', 'size': 12}
    )
    
    return fig

@app.callback(
    Output('timeline-chart', 'figure'),
    [Input('year-slider', 'value')]
)
def update_timeline_chart(years_range):
    filtered_df = df[
        (df['Award_Date'].astype(int) >= years_range[0]) &
        (df['Award_Date'].astype(int) <= years_range[1])
    ]
    
    yearly_data = filtered_df.groupby('Award_Date')['Amount_awarded'].sum().reset_index()
    
    fig = px.line(
        yearly_data,
        x='Award_Date',
        y='Amount_awarded',
        title='Grants Timeline',
        labels={'Amount_awarded': 'Total Amount Awarded (£)',
                'Award_Date': 'Year'},
        template='plotly_white'
    )
    
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Total Amount Awarded (£)",
        height=500,
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Arial', 'size': 12}
    )
    
    return fig

@app.callback(
    Output('bubble-chart', 'figure'),
    [Input('animation-interval', 'n_intervals')]
)
def update_bubble_chart(n_intervals):
    if n_intervals is None:
        n_intervals = 0
    
    # Get unique years and current year based on animation frame
    years = sorted(df['Award_Date'].unique())
    current_year = years[n_intervals % len(years)]
    
    # Filter data for current year
    year_data = df[df['Award_Date'] == current_year]
    
    fig = px.scatter(
        year_data,
        x='Duration_(Days)',
        y='Amount_awarded',
        size='Amount_awarded',
        color='Funding_Org:Department',
        hover_name='Title',
        hover_data={
            'Description_': True,  # Fixed column name
            'Amount_awarded': ':£,.0f',
            'Duration_(Days)': True
        },
        title=f'Grant Distribution in {current_year}',
        labels={
            'Duration_(Days)': 'Project Duration (Days)',
            'Amount_awarded': 'Grant Amount (£)',
            'Funding_Org:Department': 'Department',
            'Description_': 'Description'  # Added label to show without underscore
        }
    )
    
    fig.update_layout(
        height=600,
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Arial', 'size': 12},
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05
        )
    )
    
    # Add better axis formatting
    fig.update_xaxes(title_font=dict(size=12), tickfont=dict(size=10))
    fig.update_yaxes(title_font=dict(size=12), tickfont=dict(size=10))
    
    return fig

def update_graph(_):  # Removed unused 'id' parameter
    return update_bubble_chart(None)


if __name__ == '__main__':
    app.run_server(debug=True)
