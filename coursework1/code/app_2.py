from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
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
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3("Grant Distribution Over Time", className="mb-3 text-primary"),
                    dcc.Loading(
                        id="loading",
                        type="cube",
                        children=dcc.Graph(id='bubble-chart')
                    )
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
    Output('bubble-chart', 'figure'),
    Input('loading', 'loading_state')
)
def update_bubble_chart(loading_state):
    fig = px.scatter(
        df,
        x='Award_Date',
        y='Duration_(Days)',
        size='Amount_awarded',
        color='Funding_Org:Department',
        hover_name='Title',
        hover_data={
            'Award_Date': True,
            'Amount_awarded': ':,.0f',
            'Duration_(Days)': True,
            'Funding_Org:Department': True
        },
        animation_frame=df['Award_Date'].dt.strftime('%Y-%m'),
        size_max=50,
        template='plotly_white'
    )

    # Update layout
    fig.update_layout(
        height=600,
        title_x=0.5,
        xaxis=dict(
            title='Award Date',
            range=[df['Award_Date'].min(), df['Award_Date'].max()]
        ),
        yaxis=dict(
            title='Duration (Days)',
            range=[0, df['Duration_(Days)'].quantile(0.95)]
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=1,
            xanchor="right",
            x=1.1
        )
    )

    # Update animation settings
    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 1000
    fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 500

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)


