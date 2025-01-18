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
external_stylesheets = [dbc.themes.FLATLY]  # Changed theme to FLATLY for a modern look
app = Dash(__name__, external_stylesheets=external_stylesheets, meta_tags=meta_tags)

# Data processing function remains the same
def process_data():
    code_directory = Path(__file__).resolve().parent
    coursework1_root = code_directory.parent
    sys.path.append(str(coursework1_root))
    excel_file_path = coursework1_root / 'data' / 'cleaned_grants_data.xlsx'
    data = pd.read_excel(excel_file_path)
    return data

df = process_data()

# Improved Layout
app.layout = dbc.Container([
    # Header with background
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
                        className="mb-3",
                        style={'border-radius': '5px'}
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
                                  df['Award_Date'].astype(int).max()],
                            className="mb-4",
                        )
                    ], style={'padding': '0 20px'}),
                    dcc.Graph(id='timeline-chart')
                ])
            ], className="shadow-sm")
        ])
    ], className="mb-4"),
], fluid=True, style={'background-color': '#f8f9fa', 'padding': '20px'})

# Update the chart callbacks with better styling
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
        labels={
            'Amount_awarded': 'Total Amount Awarded (£)',
            'Funding_Org:Department': 'Department'
        },
        template='plotly_white'  # Clean template
    )
    
    fig.update_layout(
        xaxis_title="Department",
        yaxis_title="Total Amount Awarded (£)",
        bargap=0.2,
        height=500,
        title_x=0.5,  # Center the title
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
        labels={
            'Amount_awarded': 'Total Amount Awarded (£)',
            'Award_Date': 'Year'
        },
        template='plotly_white'  # Clean template
    )
    
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Total Amount Awarded (£)",
        height=500,
        title_x=0.5,  # Center the title
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Arial', 'size': 12}
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
