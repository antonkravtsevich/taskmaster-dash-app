import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import requests
from collections import deque
import sys


ENV = os.environ.get('ENV', 'test')
if ENV == 'test':
    API_PORT = '32111'
    API_HOST = '188.166.115.138'
else:
    API_PORT = '8080'
    API_HOST = os.environ.get('API_HOST', 'localhost')

X = deque(maxlen=400)
Y = deque(maxlen=400)

app = dash.Dash(__name__)
server = app.server

app = dash.Dash(__name__)
app.layout = html.Div(
    [
        html.Div(id='header'),

        dcc.Dropdown(
            id='film-dropdown',
            options=[
                {'label': 'Avengers', 'value': 'Avengers'},
                {'label': 'Black Panther', 'value': 'Black Panther'},
                {'label': 'Ready Player One', 'value': 'Ready Player One'},
                {'label': 'Shape of Water', 'value': 'Shape of Water'},
                {'label': 'Justice Leagure', 'value': 'Justice Leagure'},
                {'label': 'Star Wars', 'value': 'Star Wars'},
            ],
            value='Avengers'
        ),

        html.Div(className='row', children=[dcc.Graph(id='live-graph', animate=False)]),
        html.Div(className='row', children=[dcc.Graph(id='sentiment-pie', animate=False)]),

        dcc.Interval(
            id='graph-update',
            interval=5*1000
        ),

        dcc.Interval(
            id='sentiment-pie-update',
            interval=4*1000
        )
    ]
)


@app.callback(dash.dependencies.Output('live-graph', 'figure'),
              [dash.dependencies.Input(component_id='film-dropdown', component_property='value')],
              events=[dash.dependencies.Event('graph-update', 'interval')])
def update_graph_scatter(theme):
    data = get_polarity(theme)
    polarity_array = data['polarity']
    timestamp_array = data['timestamps']

    X = timestamp_array
    Y = polarity_array

    data = plotly.graph_objs.Scatter(
            x=list(X),
            y=list(Y),
            name='Scatter',
            mode= 'lines'
            )

    return {'data': [data],'layout' : plotly.graph_objs.Layout(xaxis=dict(range=[min(X),max(X)]),
                                                yaxis=dict(range=[min(Y)-0.1,max(Y)+0.1]),)}


@app.callback(dash.dependencies.Output('sentiment-pie', 'figure'),
              [dash.dependencies.Input(component_id='film-dropdown', component_property='value')],
              events=[dash.dependencies.Event('sentiment-pie-update', 'interval')])
def update_piechart(theme):
    request_theme = theme.lower().replace(' ', '+')
    data = get_percentage(request_theme)
    negative_tweets_count = data['negative_tweets_count']
    positive_tweets_count = data['positive_tweets_count']
    neutral_tweets_count = data['neutral_tweets_count']

    tweets_count = negative_tweets_count + positive_tweets_count + neutral_tweets_count

    negative_percentage = (negative_tweets_count / tweets_count) * 100
    positive_percentage = (positive_tweets_count / tweets_count) * 100
    neutral_percentage = (neutral_tweets_count / tweets_count) * 100

    labels = ['Positive', 'Negative', 'Neutral']
    values = [positive_percentage, negative_percentage, neutral_percentage]
    colors = ['#00FF00','#F20505','#FFFF00']

    trace = go.Pie(labels=labels, values=values,
                   hoverinfo='label+percent', textinfo='value', 
                   textfont=dict(size=20),
                   marker=dict(colors=colors, 
                               line=dict( width=2)))

    return {"data":[trace],'layout' : plotly.graph_objs.Layout(
                                                  title=theme+' tweet piechart',
                                                  showlegend=True)}


@app.callback(dash.dependencies.Output('header', 'children'),
    [dash.dependencies.Input('film-dropdown', 'value')])
def update_output(value):
    return '{} live rating'.format(value)


def get_polarity(theme):
    request_theme = theme.lower().replace(" ", "+")
    res = requests.get('http://'+API_HOST+':'+API_PORT+'/polarity?theme='+request_theme)
    # TODO: Async
    # TODO: validate
    return(res.json()['result'])


def get_percentage(theme):
    request_theme = theme.lower().replace(" ", "+")
    res = requests.get('http://'+API_HOST+':'+API_PORT+'/percentage?theme='+request_theme)
    # TODO: Async
    # TODO: validate
    return(res.json()['result'])


if __name__ == '__main__':
    if ENV=='test':
        print('Test environment')
        debug=True
    else: 
        print('Production environment')
        debug=False
    app.run_server(debug=debug)