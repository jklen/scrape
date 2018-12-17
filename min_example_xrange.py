# -*- coding: utf-8 -*-
"""
Created on Fri Dec 14 09:33:25 2018

@author: Dell
"""

import dash
import dash_html_components as html
import dash_core_components as dcc
from plotly.graph_objs import Bar, Figure, Scatter
import pandas as pd
import datetime

from dash.dependencies import Input, Output, State, Event

app = dash.Dash()

app.layout = html.Div([
        dcc.RadioItems(id = 'xaxis',
                                options = [{'label': 'Number', 'value':'nr'},
                                                  {'label': 'Date', 'value':'date'}
                                                  ],
                                value = 'date'),
        dcc.Graph(id = 'graph')
])

@app.callback(Output('graph', 'figure'),
              [Input('xaxis', 'value')])
def graph_figure(xtype):
    if xtype == 'nr':
        x = [i for i in range(0,100)]
        y = [i for i in range(0,100)]
        x_range = [x[-20], x[-1]]
    elif xtype == 'date':
        x = pd.date_range(pd.datetime.today(), periods = 100).tolist()
        x = [i.to_pydatetime() for i in x]
        y = [i for i in range(0,100)]
        x_range = [x[-1] - datetime.timedelta(days = 30), x[-1]]
    
    trace = Scatter(x = x,
                    y = y)
    layout = dict(xaxis = dict(range = x_range))
    
    to_return =  Figure(data = [trace], layout = layout)
    
    return to_return

if __name__ == '__main__':
    app.run_server(debug=True)