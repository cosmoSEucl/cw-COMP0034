from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from .components import create_metric_card, create_department_section

def create_layout(df, department_colors):
    """Create the main layout of the dashboard."""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("Grant Funding Analysis", 
                        className="text-center mb-3 mt-3",
                        style={'color': '#2C3E50', 'font-weight': 'bold'})
            ])
        ], className="mb-4"),

        # Metrics
        dbc.Row([
            dbc.Col(create_metric_card("Total Grants Value (Millions)", "total-value"), width=6),
            dbc.Col(create_metric_card("Total Number of Grants", "total-number"), width=6),
        ], className="mb-4"),

        # Department Analysis
        dbc.Row([
            dbc.Col([
                create_department_section(
                    df,
                    df['Award_Date'].dt.year.min(),
                    df['Award_Date'].dt.year.max()
                )
            ])
        ], className="mb-4"),

        # Word Cloud
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3("Word Cloud of Grant Titles", 
                               className="mb-3 text-primary",
                               style={'textAlign': 'center'}),
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
                            style={'display': 'flex', 'justifyContent': 'center'}
                        )
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),

        # Timelines
        dbc.Row([
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
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(id="interactive-timeline-title", className="mb-3 text-primary"),
                        dcc.Dropdown(
                            id='department-selector',
                            options=[{'label': dept, 'value': dept} 
                                    for dept in df['Funding_Org:Department'].unique()],
                            value=df['Funding_Org:Department'].iloc[0],
                            clearable=False,
                            className="mb-3"
                        ),
                        dcc.Graph(id='interactive-timeline', style={'height': '400px'})
                    ])
                ], className="shadow-sm")
            ], md=6)
        ], className="mb-4"),

        # Grants Table
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
                            columns=[{"name": i, "id": i} for i in df.columns],
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
                            style_data_conditional=[{
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }],
                            fixed_rows={'headers': True},
                            virtualization=False,
                        ),
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),

    ], fluid=True, style={'background-color': '#f8f9fa', 'padding': '20px'})
