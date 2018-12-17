

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


myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection_rmetrics = scrapedb['rmetrics']
adcollection_poolmetrics = scrapedb['poolmetrics']
adcollection_proxies = scrapedb['proxies']

app = dash.Dash(__name__)
app.css.append_css({'external_url':'https://codepen.io/amyoshino/pen/jzXypZ.css'})
app.config['suppress_callback_exceptions'] = True

def lay():
    return html.Div([
            html.Div(id = 'prompts', children = [
                    html.Div(id = 'all_tabs_prompts', children = [
                            html.Button(children = 'Stop refresh', id = 'interval_button'),
                            html.Div(id = 'times_refreshed')
                    ]),
                    html.Div(id = 'tab23_prompts', style = {'display':'none'}, children = [
                            html.P('Moving average'),
                            dcc.Input(id = 'ma_input', type = 'number', value = 5, size = 3),
                            html.P('X axis type'),
                            dcc.RadioItems(id = 'xaxis', options = [{'label':'Number', 'value':'nr'},
                                                                    {'label':'Date', 'value':'date'}],
                                            value = 'date',
                                            labelStyle = {'display':'inline-block'}),
                            dcc.Checklist(id = 'limit_check', options = [{'label':'Limit visible data', 'value':'limit'}],
                                          values = ['limit']),
                            dcc.Input(id = 'linput', type = 'number', value = 200)
                    ]),
                    html.Div(id = 'tab4_prompts', style = {'display':'none'}, children = [
                            dcc.RadioItems(id = 'proxy_radio',
                                           options = [{'label':'All proxy data', 'value':'all'},
                                                      {'label':'Window data', 'value':'window'}],
                                                      value = 'all'),
                            dcc.Input(id = 'proxy_window_input',
                                      type = 'number',
                                      value = 10)
                    ])
            ], className = 'two columns'),
            html.Div([
                    dcc.Tabs(id = 'tabs', value = 'tab1', children = [
                            dcc.Tab(label = 'Links overall', value = 'tab1'),
                            dcc.Tab(label = 'Links time window', value = 'tab2'),
                            dcc.Tab(label = 'Bandits', value = 'tab3'),
                            dcc.Tab(label = 'Proxies', value = 'tab4')
                    ]),
                    html.Div([
                            html.Div(id = 'content', children = [
                                    ]),
                            dcc.Interval(id = 'interval', interval = 2000, n_intervals = 0)
                    ])
            ]),
            html.Div([
                html.Div(id = 'stored_clicks', style = {'display':'none'})
            ]),
            dcc.Store(id = 'store_tab12'),
            dcc.Store(id = 'store_tab3'),
            dcc.Store(id = 'store_tab4')
            
            
    ])

app.layout = lay()

@app.callback(Output('store_tab12', 'data'),
              [Input('tabs', 'value'),
               Input('interval', 'n_intervals')],
               [State('store_tab12', 'data')])
def store_tab12_data(tab, interval, data):
    if data:
        print(len(data))
        if tab in ['tab1', 'tab2']:
            col_count = adcollection_rmetrics.estimated_document_count()
            old_count = len(data)
            if col_count - old_count > 0:
                new_data = list(adcollection_rmetrics.find({}, {'_id': False}).sort('$natural', -1).limit(col_count - old_count))
                data.extend(new_data)
                return data
    else:
        data = list(adcollection_rmetrics.find({}, {'_id': False}))
        return data

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
        return html.P('Times refreshed: ' + str(interval))
    else:
        return html.P('Times refreshed: 0')

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
                                html.Div(id = 'tab1_chart3_div', className = 'four columns'),
                                html.Div(id = 'tab1_chart4_div', className = 'four columns'),
                                html.Div(id = 'tab1_chart5_div', className = 'two columns')
                            ], className = 'row')
                        ])
        elif tab == 'tab2':
            to_return = html.Div([
                            html.Div([
                                html.Div(id = 'tab2_chart1_div', className = 'five columns'),
                                html.Div(id = 'tab2_chart2_div', className = 'five columns')
                                
                            ], className = 'row'),
                            html.Div([
                                html.Div(id = 'tab2_chart3_div', className = 'five columns'),
                                html.Div(id = 'tab2_chart4_div', className = 'five columns')
                                
                            ], className = 'row')
                        ])
        elif tab == 'tab3':
            to_return = html.Div([
                            html.Div([
                                html.Div(id = 'tab3_chart1_div', className = 'five columns'),
                                html.Div(id = 'tab3_chart2_div', className = 'five columns')
                                
                            ], className = 'row'),
                            html.Div([
                                html.Div(id = 'tab3_chart3_div', className = 'ten columns')
                                
                            ], className = 'row')
                        ])
        elif tab == 'tab4':
            to_return = html.Div([
                            html.Div([
                                html.Div(id = 'tab4_chart1_div', className = 'five columns'),
                                html.Div(id = 'tab4_chart2_div', className = 'five columns')
                                
                            ], className = 'row'),
                            html.Div([
                                html.Div(id = 'tab4_chart3_div', className = 'ten columns')                                
                            ], className = 'row')
                        ])
        return to_return

@app.callback(Output('tab23_prompts', 'style'),
              [Input('tabs', 'value')])
def tab_prompts(tab):
    if tab in ['tab2', 'tab3']:
        to_return = {'display':'inline-block'}
    else:
        to_return = {'display':'none'}
    return to_return

@app.callback(Output('tab4_prompts', 'style'),
              [Input('tabs', 'value')])
def proxy_prompts(tab):
    if tab == 'tab4':
        to_return = {'display':'inline-block'}
    else:
        to_return = {'display':'none'}
    
    return to_return

@app.callback(Output('proxy_window_input', 'style'),
              [Input('proxy_radio', 'value')])
def proxy_window_input(radio):
    if radio == 'all':
        to_return = {'display':'none'}
    else:
        to_return = {'display':'inline-block'}
    
    return to_return

@app.callback(Output('linput', 'style'),
              [Input('limit_check', 'values')])
def limit_input(check):
    try:
        check[0]
    except:
        to_return = {'display':'none'}
    else:
        to_return = {'display':'inline-block'}
        
    return to_return

if __name__ == '__main__':
    app.run_server(debug = True)