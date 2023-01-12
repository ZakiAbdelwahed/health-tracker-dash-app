# -------------------------------------------------------------------------
#                                  Imports
# -------------------------------------------------------------------------
import creds # import py file that holds access tokens and other ID's
import dash
from dash.dependencies import Input, Output
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import dash_extensions as de
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pandas import json_normalize 
import scipy.stats as stats
import requests
import datetime
import pandas as pd
import numpy as np

# -------------------------------------------------------------------------
#                             Get Oura Ring Data
# -------------------------------------------------------------------------

# Get data from Oura's API
url = "https://api.ouraring.com/v2/usercollection/sleep"
params = {
    "start_date": "2021-06-11",
    "end_date": datetime.datetime.now().strftime("%Y-%m-%d"),
}
headers = {
    "Authorization": f"Bearer {creds.api_key}"
}
response = requests.request("GET", url, headers=headers, params=params)

# Read data
json = response.json()
oura_data = json_normalize(json, "data")

# Convert column "day" to datetime
oura_data["day"] = pd.to_datetime(oura_data["day"])

# Change the posistion of the "day" column
oura_data = oura_data[["day"] + list(oura_data.columns.difference(["day"]))]

# Remove duplicates and only keep "long_sleep" types
oura_data = oura_data.sort_values("type")
oura_data = oura_data.drop_duplicates(subset="day", keep="first")

# Sort data by "day" (ascending) and reset index
oura_data = oura_data.sort_values("day", ascending=True).reset_index(drop=True)

# -------------------------------------------------------------------------
#                            Get Apple Health Data: running
# -------------------------------------------------------------------------

# Get data from Google Drive
gauth = GoogleAuth()
drive = GoogleDrive(gauth)
file = drive.CreateFile({"id": creds.file_id})
file.GetContentFile("Export.csv")
ah_data = pd.read_csv("Export.csv")

# Add a "day" column by splitting the "Date" column which holds a start and end date
ah_data["day"] = ah_data.Date.apply(lambda x: pd.to_datetime(x.split(" - ")[1]))

# -------------------------------------------------------------------------
#                            Get Apple Health Data: VO2 max
# -------------------------------------------------------------------------

# Get data from Google Drive
gauth = GoogleAuth()
drive = GoogleDrive(gauth)
file_id = "1lN5DGfasVOtI43gTCnesT1KCwjU2k6bL"
file = drive.CreateFile({"id": file_id})
file.GetContentFile("vo2max.csv")
vo2 = pd.read_csv("vo2max.csv")

# Convert date from string to datetime type
vo2.Date = pd.to_datetime(vo2.Date)

# -------------------------------------------------------------------------
#                                  Metrics
# -------------------------------------------------------------------------

# Average HRV
avg_hrv = round(oura_data.average_hrv.mean())

# Average lowest HR
avg_lowhr = round(oura_data.lowest_heart_rate.mean())

# Average total sleep
avg_sleep = round(oura_data.total_sleep_duration.mean())
avg_sleep = pd.to_datetime(str(datetime.timedelta(seconds=float(avg_sleep)))).strftime("%Hh%M")

# VO2 max
vo2max = 47.80

# Number of km run (not counting runs < 1 km)
run = ah_data.loc[(ah_data["Activity"]=="Running") & (ah_data["Distance(km)"]>1)].reset_index(drop=True)
km_run = round(run["Distance(km)"].sum(), 0)
km_run = round(km_run + 1586) # Adding total of km run with Nike Run Club app

# Percentage of run around the world goal
earth_circumference = 40075
pct_achieved = round(km_run / earth_circumference * 100, 2)

# -------------------------------------------------------------------------
#                                 Colors
# -------------------------------------------------------------------------

# Create variables for colors to quickly update the aesthetic of the app
font_color = "#e6e6e6"
marker_color = "#a02c5a"

# -------------------------------------------------------------------------
#                              Graph function
# -------------------------------------------------------------------------


# Define a function that plots a scatter plot for a given dataframe
def scatter_plot(
        df, x, y, ylabel, avg_line_text, hovertemplate, ytickvals=False,
        annot1_x=-0.18, annot2_x=1.2, margin_l=110, margin_r=115):
    """
    Creates a scatter plot with a trend line using the provided dataframe and columns specified.

    Parameters:
    df (pandas.DataFrame): The dataframe to use for the scatter plot.
    x (str): The column to use for the x-axis.
    y (str): The column to use for the y-axis.
    ylabel (str): The label to use for the y-axis.
    avg_line_text (str): The label to use for the average line on the y-axis.
    hovertemplate (str): Hovertemplate to use for points.
    ytickvals (bool): Whether to reformat y ticks or not.
    annot1_x (float): x position for ylabel text.
    annot2_x (float): x position for avg_line_text.
    margin_l (int): Left margin for the plot.
    margin_r (int): Right margin for the plot.
    
    Returns:
    fig (plotly.graph_objs._figure.Figure) : The created scatter plot figure.
    """
    
    # Add column to the dataframe to use for a custom hover template
    df["formatted_duration"] = [
        pd.to_datetime(str(datetime.timedelta(seconds=float(d)))).strftime("%Hh%M") 
        for d in df[y]
    ]
    
    # Draw scatter plot with trend line
    fig = px.scatter(df, x=x, y=y, trendline="ols", trendline_color_override="#ffdd1a",
                     custom_data=['formatted_duration']  # Add custom data to use in a custom hover template
                    ) 

    # Reformat y ticks if argument ytickvals is True
    if ytickvals is True:
        step = round((df[y].max() - df[y].min()) / 7)
        ytickvals = np.arange(start=df[y].min(), 
                              stop=df[y].max(), 
                              step=step)
        yticktext = [
            pd.to_datetime(str(datetime.timedelta(seconds=float(d)))).round("10min").strftime("%Hh%M") 
            for d in ytickvals
        ]
        fig.update_yaxes(tickvals=ytickvals, ticktext=yticktext)

    # Update layout: define the plot's background color, the font and font color, the margins and remove the grid
    fig.update_layout(paper_bgcolor="#2B2B2B", plot_bgcolor="#2B2B2B", font_family="sans-serif",
                      font_color=font_color, xaxis_showgrid=False, yaxis_showgrid=False, 
                      xaxis=dict(title=None, zeroline=False), yaxis=dict(title=None, zeroline=False),
                      margin=dict(l=margin_l,r=margin_r,b=75,t=10, pad=20), autosize=True
                      )

    # Update layout: define the markers' size and color and overwrite the hover template with a custom one
    fig.update_traces(marker=dict(size=7, color=marker_color), hovertemplate=hovertemplate)

    # Add title to the y axis with annotation since 'title_standoff' doesn't seem to work in Dash
    fig.add_annotation(x=annot1_x, xref="paper", y=0.5, yref="paper", text=ylabel, textangle=-90, 
                       showarrow=False, font=dict(color=font_color, size=14)
                      )

    # Add a horizontal line for the average using 'add_shape' because 'add_hline' doesn't seem to work in Dash
    fig.add_shape(type="line", xref="paper", x0=0, y0=df[y].mean(), x1=0.98, y1=df[y].mean(),
                  line=dict(dash="dot", color=font_color, width=1.25)
                 )

    # Add annotation to specify that the horizontal line is the average
    fig.add_annotation(x=annot2_x, xref="paper", y=df[y].mean(), text=avg_line_text, showarrow=False, 
                       font=dict(color=font_color, size=12)
                      )

    return fig


# -------------------------------------------------------------------------
#                                Cards
# -------------------------------------------------------------------------


# Define a function that creates a card for a given metric
def metric_card(metric, title, icon):
    """
    Returns a 'CardGroup' component containing two 'Card' components that display a metric, a title 
    and an icon to illustrate the metric.

    Parameters:
        - metric (int or float): the numeric value to be displayed on top of the card
        - title (str): the title of the card
        - icon (str): the class of the icon to be displayed inside the card

    Returns:
        A 'CardGroup' component from the 'dash_bootstrap_components' library (which is imported as 'dbc') 
    """

    return dbc.CardGroup(
               [
                   dbc.Card(
                       dbc.CardBody([html.H2(metric), html.H5(title, className="card-text")]),
                       style={
                           "color":font_color, "background-color":"#2B2B2B",
                           "font-family":"sans-serif", "padding":"0px"
                       }
                   ),
                   dbc.Card(html.Div(className=icon, style={"color": font_color, "textAlign": "center",
                                                            "fontSize": 40, "margin": "auto"
                                                     }
                            ),
                            className="bg-warning", 
                            style={"maxWidth": 75}
                   )
               ],
               className="m-1"
           )


# Define a function that creates a card for a given plot
def graph_card(title, figure):
    """
    Returns a Dash Bootstrap Card component containing a graph.

    Parameters:
        - title (str): The title of the card
        - figure (str): The callback id of the graph

    Returns:
        - A Dash Bootstrap Card component containing the graph
    """

    return dbc.Card(
               [
                   dbc.CardHeader(title, style={
                                             "color":font_color, "background-color":'#2B2B2B',
                                             "font-family":"sans-serif", "font-size": 20,
                                             "border-color":font_color, "border-width": "1px"
                                         }
                   ),
                   dbc.CardBody(dbc.Spinner(
                                    dcc.Graph(id=figure, config={
                                                             "modeBarButtons" : [["zoomIn2d", "zoomOut2d", "toImage"]],
                                                             "toImageButtonOptions": {"scale": 3}
                                                         }
                                    )
                                ),
                                style={"background-color":"#2B2B2B"}
                   )
               ],
               className="ml-1 mr-1"
           )
    
    
# Card 1: Average HRV 
hrv_card = metric_card(metric=f"{avg_hrv} ms",
                       title="Average HRV", 
                       icon="fa fa-heartbeat"
                      )

# Card 2: Average lowest heart rate
lowhr_card = metric_card(metric=f"{avg_lowhr} bpm",
                       title="Average lowest HR", 
                       icon="fa fa-heartbeat"
                      )

# Card 3: Average sleep
sleep_card = metric_card(metric=f"{avg_sleep}",
                       title="Average sleep duration", 
                       icon="fa fa-bed"
                      )

# Card 4: VO2 max
vo2max_card = metric_card(metric=f"{vo2max}",
                       title="VO2 max", 
                       icon="fa fa-bicycle"
                      )

# Card 5: Number of km run + the percentage of the earth's circumference displayed as a progress bar
run_goal_card = dbc.Card(
                    dbc.CardBody(
                        [
                            html.H2(
                                f"{km_run:,} km run since Oct 2016".replace(',', ' '), 
                                className="card-title"
                            ),
                            html.H5(
                                "Percentage of the earth's circumference (40 075 km)",
                                className="card-text"
                            ),
                            dbc.Progress(
                                children=[f"{pct_achieved}%"], value=pct_achieved, max=100,
                                color="warning", style={"height": "20px", "background-color": "#1E1E1E"}
                            )
                        ]
                    ),
                    style={"color":font_color, "background-color":"#2B2B2B", "font-family":"sans-serif"},
                    className="ml-1 mr-1 g-0"
                )

# Card 6: HRV trend graph
hrv_graph_card = graph_card(title="HRV trend", figure="hrv_fig")

# Card 7: Zone 2 performance graph
zone2_graph_card = graph_card(title="Zone 2 performance trend", figure="zone2_fig")

# Card 8: VO2 max graph
vo2_graph_card = graph_card(title="VO2 max trend", figure="vo2max_fig")

# Card 9: Total sleep trend graph
sleep_graph_card = graph_card(title="Total sleep trend", figure="sleep_fig")

# Card 10: Deep sleep vs REM sleep
deep_vs_rem_card = graph_card(title="Deep sleep vs REM sleep", figure="deep_vs_rem")

# Card 11: Deep sleep trend graph
deep_sleep_graph_card = graph_card(title="Deep sleep trend", figure="deep_sleep_fig")

# Card 12: REM sleep trend graph
rem_sleep_graph_card = graph_card(title="REM sleep trend", figure="rem_sleep_fig")

# -------------------------------------------------------------------------
#                                App layout
# -------------------------------------------------------------------------

# Link to icons used to illustrate each metric
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.10.2/css/all.css"

# Link to animated LinkedIn logo + options controlling the display
url = "https://assets5.lottiefiles.com/packages/lf20_pWLTA9.json" 
options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio="xMidYMid slice"))

# Choose Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, FONT_AWESOME],
                suppress_callback_exceptions=True
               )

# Define app layout
app.layout = dbc.Container(
                 [
                    # Cards displaying each metric (HRV, Lowest HR, Total sleep and VO2 max)
                    dbc.Row(
                        [
                            dbc.Col(
                                hrv_card, style={"margin-bottom":"25px"}, 
                                xs=12, sm=6, md=6, lg=3, xl=3
                            ),
                            dbc.Col(
                                lowhr_card, style={"margin-bottom":"25px"}, 
                                xs=12, sm=6, md=6, lg=3, xl=3
                            ),
                            dbc.Col(
                                sleep_card, style={"margin-bottom":"25px"},
                                xs=12, sm=6, md=6, lg=3, xl=3
                            ),
                            dbc.Col(
                                vo2max_card, style={"margin-bottom":"25px"},
                                xs=12, sm=6, md=6, lg=3, xl=3
                            )
                        ],
                        className="g-0"
                    ),
                    # Run goal
                    dbc.Row(
                        dbc.Col(
                            run_goal_card, style={"margin-bottom":"42px"},
                            xs=12, sm=12, md=12, lg=12, xl=12
                        ),
                    ),
                    # Graphs
                    dbc.Row(
                        [
                            dbc.Col(
                                # Calendar to change the date range
                                dcc.DatePickerRange(id="my-date-picker-range",  # ID to be used for callback
                                                    calendar_orientation="horizontal",  # vertical or horizontal
                                                    day_size=39, # size of calendar image. Default is 39
                                                    start_date_placeholder_text="Start date",  # text that appears when no start date chosen
                                                    end_date_placeholder_text="End date",  # text that appears when no end date chosen
                                                    with_portal=False,  # if True calendar will open in a full screen overlay portal
                                                    first_day_of_week=1,  # Display of calendar when open (0 = Sunday)
                                                    reopen_calendar_on_clear=True,
                                                    is_RTL=False,  # True or False for direction of calendar
                                                    clearable=True,  # whether or not the user can clear the dropdown
                                                    number_of_months_shown=1,  # number of months shown when calendar is open
                                                    min_date_allowed=datetime.datetime(2021, 6, 12),  # minimum date allowed on the DatePickerRange component
                                                    max_date_allowed=datetime.datetime.now().date() + datetime.timedelta(days=1),  # maximum date allowed on the DatePickerRange component
                                                    initial_visible_month=datetime.datetime.now().date(),  # the month initially presented when the user opens the calendar
                                                    start_date=datetime.datetime(2021, 6, 12).date(),
                                                    end_date=datetime.datetime.now().date(),
                                                    display_format="MMM Do, YY",  # how selected dates are displayed in the DatePickerRange component.
                                                    month_format="MMMM, YYYY",  # how calendar headers are displayed when the calendar is opened.
                                                    minimum_nights=1,  # minimum number of days between start and end date
                                                    persistence=True,
                                                    persisted_props=["start_date", "end_date"],
                                                    persistence_type="memory",  # session, local, or memory. Default is 'local'
                                                    updatemode="singledate", # singledate or bothdates. Determines when callback is triggered.
                                                    className="ml-1 mr-1"                                                    
                                ),
                                style={"margin-bottom":"25px"}
                            )
                        ]
                    ),
                    dbc.Row(
                        [
                            # HRV trend
                            dbc.Col(
                                hrv_graph_card, style={"margin-bottom":"42px"},
                                xs=12, sm=12, md=12, lg=12, xl=6
                            ),
                            # Zone 2 trend
                            dbc.Col(
                                zone2_graph_card, style={"margin-bottom":"42px"},
                                xs=12, sm=12, md=12, lg=12, xl=6
                            )
                        ]
                    ),
                    dbc.Row(
                        [
                            # VO2 max trend
                            dbc.Col(
                                vo2_graph_card, style={"margin-bottom":"42px"},
                                xs=12, sm=12, md=12, lg=6, xl=6
                            ),
                            # Total sleep trend
                            dbc.Col(
                                sleep_graph_card, style={"margin-bottom":"42px"},
                                xs=12, sm=12, md=12, lg=6, xl=6
                            )
                        ]
                    ),
                    dbc.Row(
                        # Deep sleep vs REM sleep
                        dbc.Col(
                            deep_vs_rem_card, style={"margin-bottom":"42px"},
                            xs=12, sm=12, md=12, lg=12, xl=12
                        )
                    ),
                    dbc.Row(
                        [
                            # Deep sleep trend
                            dbc.Col(
                                deep_sleep_graph_card, style={"margin-bottom":"42px"},
                                xs=12, sm=12, md=12, lg=6, xl=6
                            ),
                            # REM sleep trend
                            dbc.Col(rem_sleep_graph_card, style={"margin-bottom":"42px"},
                                    xs=12, sm=12, md=12, lg=6, xl=6
                            )
                        ]
                    ),
                    # LinkedIn animated logo
                    dbc.Row(
                        dbc.Col(
                            html.A(
                                html.Div(de.Lottie(options=options, width="50%", height="50%", url=url)),
                                href="https://www.linkedin.com/in/zaki-abdelwahed/", target="_blank"
                            ),
                            width=1
                        )
                    )
                 ],
                 style={"padding":"35px"}, fluid=True
             )

# -------------------------------------------------------------------------
#                                Callbacks
# -------------------------------------------------------------------------

@app.callback(
    [
        Output("hrv_fig", "figure"), 
        Output("zone2_fig", "figure"),
        Output("vo2max_fig", "figure"),
        Output("sleep_fig", "figure"),
        Output("deep_vs_rem", "figure"), 
        Output("deep_sleep_fig", "figure"),
        Output("rem_sleep_fig", "figure")
    ],
    [
        Input("my-date-picker-range", "start_date"),
        Input("my-date-picker-range", "end_date")
    ]
)

# Define a function that updates the output when the callback is triggered
def update_output(start_date, end_date):
    """
    Returns an updated version of each graph based on a given date range specified by the start_date and end_date parameters.
    If there are not enough data points within the given date range, a message saying "Not enough data. Try a different date range." 
    will be displayed instead of the graph.

    Parameters:
        - start_date (str): start of the date range
        - end_date (str): end of the date range

    Returns:
        The updated graph for each card.
    """

    # Update the Oura ring dataframe based on the date range specified
    oura = oura_data.loc[
        (oura_data.day.apply(lambda x: x.date()) >= pd.to_datetime(start_date).date()) 
        & (oura_data.day.apply(lambda x: x.date()) <= pd.to_datetime(end_date).date())
        ]
    
    # Update the Apple Health running dataframe based on the date range specified
    new_run = run.loc[
        (run.day.apply(lambda x: x.date()) >= pd.to_datetime(start_date).date()) 
        & (run.day.apply(lambda x: x.date()) <= pd.to_datetime(end_date).date())
        ]
    
    # Update the Apple Health VO2 max dataframe based on the date range specified
    new_vo2 = vo2.loc[
        (vo2.Date.apply(lambda x: x.date()) >= pd.to_datetime(start_date).date()) 
        & (vo2.Date.apply(lambda x: x.date()) <= pd.to_datetime(end_date).date())
        ]
    
    # HRV trend graph
    if oura.shape[0] >= 2:
        # Draw graph
        hrv_fig = scatter_plot(df=oura, x="day", y="average_hrv", ylabel="HRV (ms)",
                               hovertemplate="%{x} - %{y} ms", avg_line_text="Average HRV",
                               ytickvals=False, annot1_x=-0.15, annot2_x=1.15, 
                               margin_l=97.5, margin_r=102.5,
                              )
    else:
        # Show message saying "Not enough data. Try a different date range."
        hrv_fig = go.Figure()

        # Update layout: define the plot's background color, the font and font color, the margins and remove the grid
        hrv_fig.update_layout(paper_bgcolor="#2B2B2B", plot_bgcolor="#2B2B2B",
                              xaxis=dict(showgrid=False, zeroline=False),
                              yaxis=dict(showgrid=False, zeroline=False),
                              margin=dict(l=0,r=0,b=0,t=0, pad=0)
                             )

        # Add annotation: "Not enough data. Try a different date range."
        hrv_fig.add_annotation(x=0.5, xref="paper", y=0.5, yref="paper",
                               text="Not enough data. Try a different date range.", 
                               showarrow=False, font=dict(color=font_color, size=16)
                              )
                             

    # Zone 2 performance trend

    # Calculate pace per run
    new_run["pace(km/h)"] = new_run["Distance(km)"] * 3600 / new_run["Duration(s)"]

    # Divide average pace by average heart rate to compare performances
    new_run["Performance"] = new_run["pace(km/h)"] / new_run["Heart rate: Average(count/min)"]

    # Remove outliers (values greater than 3 standard deviations from the mean)
    new_run = new_run.loc[abs(stats.zscore(new_run["Performance"])) < 3]

    # Scatter plot
    if new_run.shape[0] >= 2:
        # Draw graph
        zone2_fig = scatter_plot(df=new_run, x="day", y="Performance", 
                                 ylabel="Performance (Speed / Average HR)",
                                 hovertemplate="%{x} - %{y:.3f}",
                                 avg_line_text="Average performance", ytickvals=False,
                                 annot1_x=-0.2, annot2_x=1.26, margin_l=117.5, margin_r=145
                                )
    else:
        # Show message saying "Not enough data. Try a different date range."
        zone2_fig = go.Figure()

        # Update layout: define the plot's background color, the font and font color, the margins and remove the grid
        zone2_fig.update_layout(paper_bgcolor="#2B2B2B", plot_bgcolor="#2B2B2B",
                                xaxis=dict(showgrid=False, zeroline=False),
                                yaxis=dict(showgrid=False, zeroline=False),
                                margin=dict(l=0,r=0,b=0,t=0, pad=0)
                               )
        
        # Add annotation "Not enough data. Try a different date range."
        zone2_fig.add_annotation(x=0.5, xref="paper", y=0.5, yref="paper",
                                 text="Not enough data. Try a different date range.", 
                                 showarrow=False, font=dict(color=font_color, size=16)
                                )
        
    # VO2 max trend
    if new_vo2.shape[0] >= 2:
        # Draw graph
        vo2max_fig = scatter_plot(df=new_vo2, x="Date", y="VO2 Max(mL/min·kg)", 
                                  ylabel="VO2 max (ml/min/kg)", hovertemplate="%{x} - %{y:.1f}",
                                  avg_line_text="Average VO2 max", ytickvals=False,
                                  annot1_x=-0.2, annot2_x=1.26, margin_l=117.5, margin_r=145
                                 )
    else:
        # Show message saying "Not enough data. Try a different date range."
        zone2_fig = go.Figure()

        # Update layout: define the plot's background color, the font and font color, the margins and remove the grid
        zone2_fig.update_layout(paper_bgcolor="#2B2B2B", plot_bgcolor="#2B2B2B",
                                xaxis=dict(showgrid=False, zeroline=False),
                                yaxis=dict(showgrid=False, zeroline=False),
                                margin=dict(l=0,r=0,b=0,t=0, pad=0)
                               )
        
        # Add annotation "Not enough data. Try a different date range."
        zone2_fig.add_annotation(x=0.5, xref="paper", y=0.5, yref="paper",
                                 text="Not enough data. Try a different date range.", 
                                 showarrow=False, font=dict(color=font_color, size=16)
                                )
    
    # Total sleep trend
    if oura.shape[0] >= 2:
        # Draw graph
        sleep_fig = scatter_plot(df=oura, x="day", y="total_sleep_duration", 
                                 ylabel="Total sleep duration", hovertemplate="%{x} - %{customdata[0]}",
                                 avg_line_text="Average total sleep", ytickvals=True,
                                 annot1_x=-0.2, annot2_x=1.22, margin_l=117.5, margin_r=130
                                )
    else:
        # Show message saying "Not enough data. Try a different date range."
        sleep_fig = go.Figure()

        # Update layout: define the plot's background color, the font and font color, the margins and remove the grid
        sleep_fig.update_layout(paper_bgcolor="#2B2B2B", plot_bgcolor="#2B2B2B",
                                xaxis=dict(showgrid=False, zeroline=False),
                                yaxis=dict(showgrid=False, zeroline=False),
                                margin=dict(l=0,r=0,b=0,t=0, pad=0)
                               )

        # Add annotation "Not enough data. Try a different date range." 
        sleep_fig.add_annotation(x=0.5, xref="paper", y=0.5, yref="paper",
                                 text="Not enough data. Try a different date range.", 
                                 showarrow=False, font=dict(color=font_color, size=16)
                                )
        
    # Deep sleep trend
    if oura.shape[0] >= 2:
        # Draw graph
        deep_sleep_fig = scatter_plot(df=oura, x="day", y="deep_sleep_duration", 
                                      ylabel="Deep sleep duration",         
                                      hovertemplate="%{x} - %{customdata[0]}",
                                      avg_line_text="Average deep sleep", ytickvals=True,
                                      annot1_x=-0.2, annot2_x=1.22, margin_l=117.5, margin_r=130
                                     )
    else:
        # Show message saying "Not enough data. Try a different date range."
        deep_sleep_fig = go.Figure()

        # Update layout
        deep_sleep_fig.update_layout(paper_bgcolor="#2B2B2B", plot_bgcolor="#2B2B2B",
                                     xaxis=dict(showgrid=False, zeroline=False),
                                     yaxis=dict(showgrid=False, zeroline=False),
                                     margin=dict(l=0,r=0,b=0,t=0, pad=0)
                                    )

        # Add annotation "Not enough data. Try a different date range."
        deep_sleep_fig.add_annotation(x=0.5, xref="paper", y=0.5, yref="paper",
                                      text="Not enough data. Try a different date range.", 
                                      showarrow=False, font=dict(color=font_color, size=16)
                                     )

    # REM sleep trend
    if oura.shape[0] >= 2:
        # Draw graph
        rem_sleep_fig = scatter_plot(df=oura, x="day", y="rem_sleep_duration", 
                                     ylabel="REM sleep duration", 
                                     hovertemplate="%{x} - %{customdata[0]}",
                                     avg_line_text="Average REM sleep", ytickvals=True,
                                     annot1_x=-0.2, annot2_x=1.22, margin_l=117.5, margin_r=130
                                    )
    else:
        # Show message saying "Not enough data. Try a different date range."
        rem_sleep_fig = go.Figure()

        # Update layout: define the plot's background color, the font and font color, the margins and remove the grid
        rem_sleep_fig.update_layout(paper_bgcolor="#2B2B2B", plot_bgcolor="#2B2B2B",
                                    xaxis=dict(showgrid=False, zeroline=False),
                                    yaxis=dict(showgrid=False, zeroline=False),
                                    margin=dict(l=0,r=0,b=0,t=0, pad=0)
                                   )

        # Add annotation "Not enough data. Try a different date range."
        rem_sleep_fig.add_annotation(x=0.5, xref="paper", y=0.5, yref="paper",
                                     text="Not enough data. Try a different date range.", 
                                     showarrow=False, font=dict(color=font_color, size=16)
                                    )
        
    # Deep sleep vs REM sleep
    
    if oura.shape[0] < 2:
        # Show message saying "Not enough data. Try a different date range."
        deep_vs_rem = go.Figure()

        # Update layout: define the plot's background color, the font and font color, the margins and remove the grid
        deep_vs_rem.update_layout(paper_bgcolor="#2B2B2B", plot_bgcolor="#2B2B2B",
                                  xaxis=dict(showgrid=False, zeroline=False),
                                  yaxis=dict(showgrid=False, zeroline=False),
                                  margin=dict(l=0,r=0,b=0,t=0, pad=0)
                                 )

        # Add annotation "Not enough data. Try a different date range."
        deep_vs_rem.add_annotation(x=0.5, xref="paper", y=0.5, yref="paper",
                                   text="Not enough data. Try a different date range.", 
                                   showarrow=False, font=dict(color=font_color, size=16)
                                  )
    else:
        # Draw graph
        
        # Create a plot with 2 y axis
        deep_vs_rem = make_subplots(specs=[[{"secondary_y": True}]])

        # Create customdata to control the hover
        customdata1 = pd.DataFrame()
        customdata1[0] = pd.to_datetime(oura.day).apply(lambda x : x.strftime("%b %d, %Y"))
        customdata1[1] = oura.deep_sleep_duration.apply(lambda x: str(datetime.timedelta(seconds=x)))
        customdata1[1] = pd.to_datetime(customdata1[1]).apply(lambda x : x.strftime("%Hh%M"))
        customdata2 = pd.DataFrame()
        customdata2[0] = pd.to_datetime(oura.day).apply(lambda x : x.strftime("%b %d, %Y"))
        customdata2[1] = oura.rem_sleep_duration.apply(lambda x: str(datetime.timedelta(seconds=x)))
        customdata2[1] = pd.to_datetime(customdata2[1]).apply(lambda x : x.strftime("%Hh%M"))

        # Add the deep sleep graph
        deep_vs_rem.add_trace(go.Scatter(x=oura.day, y=oura.deep_sleep_duration, 
                                         name="Deep sleep", marker_color="#ffdd1a",
                                         customdata=customdata1, 
                                         hovertemplate="%{customdata[0]} - %{customdata[1]}"
                                        ),
                                        secondary_y=False,
                             )

        # Add the REM sleep graph
        deep_vs_rem.add_trace(go.Scatter(x=oura.day, y=oura.rem_sleep_duration, 
                                         name="REM sleep", marker_color=marker_color,
                                         customdata=customdata2,
                                         hovertemplate="%{customdata[0]} - %{customdata[1]}"
                                        ),
                                        secondary_y=True
                             )

        # Update layout: define the plot's background color, the font and font color, the margins and remove the grid
        deep_vs_rem.update_layout(paper_bgcolor="#2B2B2B", plot_bgcolor = "#2B2B2B",
                                  font_family = "sans-serif", font_color=font_color,
                                  xaxis_showgrid=False, yaxis_showgrid=False, 
                                  margin=dict(l=120,r=130,b=75,t=10, pad=20))

        # # Reformat y ticks so that the sleep duration is the hh:mm format
        if oura["deep_sleep_duration"].max() > oura["rem_sleep_duration"].max():
            max_value = oura["deep_sleep_duration"].max()
        else:
            max_value = oura["rem_sleep_duration"].max()

        if oura["deep_sleep_duration"].min() < oura["rem_sleep_duration"].min():
            min_value = oura["deep_sleep_duration"].min()
        else:
            min_value = oura["rem_sleep_duration"].min()

        step = round((max_value - min_value) / 7)
        ytickvals = np.arange(start=min_value, stop=max_value, step=step)
        yticktext = [pd.to_datetime(str(datetime.timedelta(seconds=float(d)))).round("10min").strftime("%Hh%M") for d in ytickvals]

        deep_vs_rem.update_yaxes(tickvals = ytickvals, ticktext= yticktext,
                                 secondary_y=False, zeroline=False
                                )

        # Add title to the y axis with annotation since 'title_standoff' doesn't seem to work in Dash
        deep_vs_rem.add_annotation(x=-0.2, xref="paper", y=0.5, yref="paper", text="Duration", 
                                   textangle=-90, showarrow=False, font=dict(color=font_color, size=14)
                                  )

        # Remove secondary y axis
        deep_vs_rem.update_yaxes(secondary_y=True, showticklabels=False, showgrid=False, zeroline=False) 

        # Add a horizontal line for the average deep sleep using 'add_shape' because 'add_hline' doesn't seem to work in Dash
        deep_vs_rem.add_shape(type="line", xref="paper", x0=0, y0=oura.deep_sleep_duration.mean(),
                              x1=0.98, y1=oura.deep_sleep_duration.mean(), line=dict(dash="dot",
                                                                                     color=font_color,
                                                                                     width=1.25
                                                                                    )
                             )

        # Add annotation to specify that the horizontal line is the average
        deep_vs_rem.add_annotation(x=1.08, xref="paper", y=oura.deep_sleep_duration.mean(),
                                   text="Average deep sleep", showarrow=False, 
                                   font=dict(color=font_color, size=12)
                                  )

        # Add a horizontal line for the average REM sleep using 'add_shape' because 'add_hline' doesn't seem to work in Dash
        deep_vs_rem.add_shape(type="line", xref="paper", x0=0, y0=oura.rem_sleep_duration.mean(), x1=0.98, 
                              y1=oura.rem_sleep_duration.mean(), line=dict(dash="dot", color=font_color, width=1.25)
                             )

        # Add annotation to specify that the horizontal line is the average
        deep_vs_rem.add_annotation(x=1.08, xref="paper", y=oura.rem_sleep_duration.mean(),
                                   text="Average REM sleep", showarrow=False, 
                                   font=dict(color=font_color, size=12)
                                  )
    
    return hrv_fig, zone2_fig, vo2max_fig, sleep_fig, deep_vs_rem, deep_sleep_fig, rem_sleep_fig


if __name__ == "__main__":
    app.run_server(debug=True)