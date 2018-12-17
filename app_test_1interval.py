# -*- coding: utf-8 -*-
"""
Created on Mon Dec 10 09:30:36 2018

@author: Dell
"""


import dash
import dash_core_components as dcc
import dash_html_components as html
from plotly.graph_objs import Bar, Figure, Scatter, Histogram, Pie, Box
import plotly.figure_factory as ff
from dash.dependencies import Input, Output, Event, State
import pymongo
import numpy as np
from collections import Counter
from operator import itemgetter
import pandas as pd
import datetime
import json
from dash.exceptions import PreventUpdate

app = dash.Dash(__name__)
app.css.append_css({'external_url':'https://codepen.io/amyoshino/pen/jzXypZ.css'})
app.config['suppress_callback_exceptions'] = True

def lay():
    return html.Div([
            html.Div(id = 'prompts', children = [
                    html.Button(children = 'Stop refresh', id = 'interval_button'),
                    html.Div(id = 'times_refreshed')
            ], className = 'two columns'),
            html.Div([
                    dcc.Tabs(id = 'tabs', value = 'tab1', children = [
                            dcc.Tab(label = 'tab1', value = 'tab1'),
                            dcc.Tab(label = 'tab2', value = 'tab2'),
                            dcc.Tab(label = 'tab3', value = 'tab3')
                    ]),
                    html.Div([
                            html.Div(id = 'content', children = [
                                    ]),
                            dcc.Interval(id = 'interval', interval = 2000, n_intervals = 0)
                    ])
            ]),
            html.Div([
                html.Div(id = 'stored_clicks', style = {'display':'none'}),
                html.Div(id = 'stored_clicks2', style = {'display':'none'})
            ]),
            dcc.Store(id = 'store_tab1')
            
            
    ])

app.layout = lay()
@app.callback(Output('store_tab1', 'data'),
              [Input('tabs', 'value'),
               Input('interval', 'n_intervals')],
               [State('store_tab1', 'data')])
def storetab1_data(tab, interval, data):
    print((tab, interval))
    print(data)
    
    if data:
        if tab == 'tab1':
            rows = np.random.choice([1,2,3,4,5])
            data = pd.DataFrame(data)
            data_new = pd.read_csv('data/iris.tsv', sep = '\t', nrows = rows, skiprows = len(data))
            data_new = data_new.iloc[:,0:5]
            data_new.columns = ['SepalLength', 'SepalWidth', 'PetalLength', 'PetalWidth', 'Species']
            data = pd.concat([data, data_new], ignore_index = True)
            return data.to_dict()
           
        else:
            raise PreventUpdate
    else:
        df = pd.read_csv('data/iris.tsv', sep = '\t', nrows = 5)
        df = df[['SepalLength', 'SepalWidth', 'PetalLength', 'PetalWidth', 'Species']]
        return df.to_dict()
        
        

@app.callback(Output('stored_clicks', 'children'),
              [Input('tab1_chart1', 'clickData')])
def stored_clicks_children(click):
    return click['points'][0]['x']

@app.callback(Output('stored_clicks2', 'children'),
              [Input('tab2_chart1', 'clickData')])
def stored_clicks2_children(click):
    return click['points'][0]['curveNumber']

@app.callback(Output('content', 'children'),
              [Input('tabs', 'value')])
def content_children(tab):
    if tab:
        if tab == 'tab1':
            to_return = html.Div([
                            html.Div([
                                html.Div(id = 'tab1_chart1_div', className = 'five columns'),
                                html.Div(id = 'tab1_chart2_div', className = 'five columns')
                            ], className = 'row'),
                            html.Div([
                                html.Div(id = 'show_data_div', className = 'five columns')
                            ], className = 'row')
                        ])
        elif tab == 'tab2':
            to_return = html.Div([
                            html.Div([
                                html.Div(id = 'tab2_chart1_div', className = 'five columns'),
                                html.Div(id = 'tab2_chart2_div', className = 'five columns')
                                
                            ], className = 'row'),
                            html.Div([
                                html.Div(id = 'show_data_div2', className = 'five columns')
                            ], className = 'row')
                        ])
        return to_return


@app.callback(Output('tab2_chart2_div', 'children'),
              [Input('interval', 'n_intervals'),
               Input('stored_clicks2', 'children')])
def gen_tab2_graph2(interval, data):
    print(data)
    if data:
        y = np.random.rand(10) + data
        
        return dcc.Graph(id = 'tab2_chart2', figure = Figure(data = [Box(y = y)]))

@app.callback(Output('tab2_chart1_div', 'children'),
              [Input('interval', 'n_intervals')])
def gen_tab2_graph1(interval):
    y1 = np.random.rand(20) + 5
    y2 = np.random.rand(20) + 4.3
    y3 = np.random.rand(20) + 5.7
    
    data = [Box(y = y1), Box(y = y2), Box(y = y3)]
    
    return dcc.Graph(id = 'tab2_chart1', figure = Figure(data = data))

@app.callback(Output('show_data_div2', 'children'),
              [Input('tab2_chart1', 'clickData'),
               Input('interval', 'n_intervals')])
def show_data_children2(data, interval):
    return html.Pre(json.dumps(data, indent = 2), style = {'border': 'thin lightgrey solid', 'overflowX': 'scroll'})

@app.callback(Output('tab1_chart2_div', 'children'),
              [Input('stored_clicks', 'children'),
               Input('store_tab1', 'data')])
def gen_tab1_graph2(click, data):
    #print(data)
    if data:
        data = pd.DataFrame(data)
        x = data['SepalLength']
        y = data['SepalWidth']
        if click:
            x = x * click
            y = y * click
        
        return dcc.Graph(id = 'tab1_chart2', figure = Figure(data = [Scatter(x = x, y = y, mode = 'markers')]))

@app.callback(Output('tab1_chart1_div', 'children'),
              [Input('store_tab1', 'data')])
def gen_tab1_graph1(data):
    if data:
        data = pd.DataFrame(data)
        x = data['SepalLength']
        y = data['SepalWidth']
        
        return dcc.Graph(id = 'tab1_chart1', figure = Figure(data = [Scatter(x = x, y = y, mode = 'markers')]))

@app.callback(Output('show_data_div', 'children'),
              [Input('tab1_chart1', 'clickData')])
def show_data_children(data):
    return html.Pre(json.dumps(data, indent = 2), style = {'border': 'thin lightgrey solid', 'overflowX': 'scroll'})

@app.callback(Output('interval', 'interval'),
              [Input('interval_button', 'n_clicks')])
def interval_interval(button):
    if button:
        if button % 2 == 1:
            return 600000
        else:
            return 2000
    else:
        return 2000

@app.callback(Output('interval_button', 'children'),
              [Input('interval', 'interval')])
def interval_button_children(interval):
    if interval:
        if interval == 2000:
            return 'Stop'
        else:
            return 'Start'
    else:
        'Stop'

@app.callback(Output('times_refreshed', 'children'),
              [Input('interval', 'n_intervals')])
def times_refreshed_children(interval):
    if interval:
        return html.H6('Times refreshed: ' + str(interval))
    else:
        return html.H6('Times refreshed: 0')

if __name__ == '__main__':
    app.run_server(debug = True)