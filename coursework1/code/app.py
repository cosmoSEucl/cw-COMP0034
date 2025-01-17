from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import pandas as pd
import sys

# Initialize the Dash app with Bootstrap
meta_tags = [
    {"name": "viewport", "content": "width=device-width, initial-scale=1"},
]
external_stylesheets = [dbc.themes.BOOTSTRAP]
app = Dash(__name__, external_stylesheets=external_stylesheets, meta_tags=meta_tags)

# Data processing function
def process_data():
    code_directory = Path(__file__).resolve().parent
    coursework1_root = code_directory.parent
    sys.path.append(str(coursework1_root))
    excel_file_path = coursework1_root / 'data' / 'cleaned_grants_data.xlsx'
    data = pd.read_excel(excel_file_path)
    return data

df = process_data()

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Grant Funding Analysis", className="text-center mb-4 mt-4")
        ])
    ]),
    
    # Department Grants Section
    dbc.Row([
        dbc.Col([
            html.H3("Grants by Department", className="mb-3"),
            dcc.Dropdown(
                id='department-selector',
                options=[{'label': dept, 'value': dept} 
                        for dept in df['Funding_Org:Department'].unique()],
                multi=True,  # Enable multiple selection
                placeholder="Select departments to compare",
                className="mb-3"
            ),
            dcc.Graph(id='department-grants-chart')
        ])
    ], className="mb-4"),
    
    # Timeline Section
    dbc.Row([
        dbc.Col([
            html.H3("Grants Timeline", className="mb-3"),
            dcc.RangeSlider(
                id='year-slider',
                min=df['Award_Date'].astype(int).min(),
                max=df['Award_Date'].astype(int).max(),
                step=1,
                marks={str(year): str(year) for year in sorted(df['Award_Date'].astype(int).unique())},
                value=[df['Award_Date'].astype(int).min(), df['Award_Date'].astype(int).max()],
                className="mb-3"
            ),
            dcc.Graph(id='timeline-chart')
        ])
    ])
], fluid=True)

# Callback for Department Grants Chart
@app.callback(
    Output('department-grants-chart', 'figure'),
    [Input('department-selector', 'value')]
)
def update_department_chart(selected_departments):
    if not selected_departments:
        # If no departments selected, show all
        filtered_df = df
    else:
        # Filter for selected departments
        filtered_df = df[df['Funding_Org:Department'].isin(selected_departments)]
    
    fig = px.bar(
        filtered_df.groupby('Funding_Org:Department')['Amount_awarded'].sum().reset_index(),
        x='Funding_Org:Department',
        y='Amount_awarded',
        title='Total Grants by Department',
        labels={
            'Amount_awarded': 'Total Amount Awarded (£)',
            'Funding_Org:Department': 'Department'
        }
    )
    
    fig.update_layout(
        xaxis_title="Department",
        yaxis_title="Total Amount Awarded (£)",
        bargap=0.2,
        height=500
    )
    
    return fig

# Callback for Timeline Chart
@app.callback(
    Output('timeline-chart', 'figure'),
    [Input('year-slider', 'value')]
)
def update_timeline_chart(years_range):
    filtered_df = df[
        (df['Award_Date'].astype(int) >= years_range[0]) &
        (df['Award_Date'].astype(int) <= years_range[1])
    ]
    
    # Group by year and sum the amounts
    yearly_data = filtered_df.groupby('Award_Date')['Amount_awarded'].sum().reset_index()
    
    fig = px.line(
        yearly_data,
        x='Award_Date',
        y='Amount_awarded',
        title='Grants Timeline',
        labels={
            'Amount_awarded': 'Total Amount Awarded (£)',
            'Award_Date': 'Year'
        }
    )
    
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Total Amount Awarded (£)",
        height=500
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)