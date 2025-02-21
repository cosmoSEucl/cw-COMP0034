from dash import html, dcc
import dash_bootstrap_components as dbc

def create_metric_card(title, id):
    """Create a metric card component."""
    return dbc.Card(
        dbc.CardBody([
            html.H5(title, className="card-title"),
            html.Div(id=id, className="lead"),
        ]),
        className="shadow-sm",
    )

def create_department_section(df, year_min, year_max):
    """Create the department analysis section."""
    return dbc.Card([
        dbc.CardBody([
            html.H3("Grants by Department", className="mb-3 text-primary"),
            dbc.Row([
                dbc.Col(
                    dcc.RangeSlider(
                        id='department-year-slider',
                        min=year_min,
                        max=year_max,
                        step=1,
                        marks={str(year): str(year) for year in sorted(df['Award_Date'].dt.year.unique())},
                        value=[year_min, year_max]
                    ), 
                    md=12
                ),
                dbc.Col(dcc.Graph(id='department-pie-chart'), md=6),
                dbc.Col(dcc.Graph(id='department-duration-chart'), md=6),
            ])
        ])
    ], className="shadow-sm")