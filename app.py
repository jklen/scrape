# -*- coding: utf-8 -*-
"""
Created on Tue Sep 18 20:59:57 2018

@author: j.klen
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
from plotly.graph_objs import Bar
from plotly.graph_objs import Figure
from dash.dependencies import Input, Output
import pymongo
import numpy as np

myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection_rmetrics = scrapedb['rmetrics']

app = dash.Dash(__name__)

app.layout = html.Div(
    html.Div([
        html.H4('Requests data'),
        html.Div(id='live-update-text'),
        dcc.Graph(id='live-update-graph'),
        dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )
    ])
)

@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def gen_histogram1(interval):
    
    values = [r['time success'] for r in adcollection_rmetrics.find()]
    bin_val = np.histogram(values, bins = 30)
    trace = Bar(x = bin_val[1],
                y = bin_val[0])
    return Figure(data = [trace])

if __name__ == '__main__':
    app.run_server(debug = True)