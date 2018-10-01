# -*- coding: utf-8 -*-
"""
Created on Tue Sep 18 20:59:57 2018

@author: j.klen
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
from plotly.graph_objs import Bar, Figure, Scatter, Line, Marker, Layout, Histogram, Pie, Legend
import plotly.figure_factory as ff
from dash.dependencies import Input, Output, Event
import pymongo
import numpy as np
from collections import Counter
import pandas as pd

myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection_rmetrics = scrapedb['rmetrics']

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Tabs(id="tabs", children=[
        dcc.Tab(label='Links overall', children=[
            html.Div([html.Div(id = 'overall_content'), 
                    dcc.Interval(
                            id = 'tab1_interval',
                            interval = 2000,
                            n_intervals = 0)])
        ]),
        dcc.Tab(label='Links time window', children=[
            html.Div([
                    html.Div([
                            html.H5('Times refreshed:')
                    ], className = 'four columns'),
                    html.Div([
                            html.H5('Moving average:')
                    ], className = 'four columns')
            ], className = 'row'),
            html.Div([
                html.Div([
                        html.Div(id = 'times_refreshed')
                ], className = 'two columns'),
                html.Div([
                    html.Button(children = 'Stop refresh', id = 'interval_button')        
                        
                ], className = 'two columns'),
                html.Div([
                    dcc.Slider(
                            id = 'slider_MA_tab2',
                            min = 2,
                            max = 10,
                            value = 5,
                            step = 1,
                            marks = {i:str(i) for i in range(2, 11)})
                ], className = 'four columns')
                
                
            ], className = 'row'),
            html.Div([
                        html.Div(id = 'time_window_content'),
                        dcc.Interval(
                                id = 'tab2_interval',
                                interval = 2000,
                                n_intervals = 0)
                ], className = 'row')
        ]),
        dcc.Tab(label='Tab three', children=[
            html.Div(id = 'tab3_content')
        ]),
    ])
])

#app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
app.css.append_css({'external_url':'https://codepen.io/amyoshino/pen/jzXypZ.css'})

@app.callback(Output('interval_button', 'children'), [Input('interval_button', 'n_clicks')])
def update_button(clicks):
    #if clicks != None:
        if clicks % 2 == 1:
            return 'Start refresh'
        elif clicks % 2 == 0:
            return 'Stop refresh'

@app.callback(Output('tab2_interval', 'interval'), [Input('interval_button', 'n_clicks')])
def stop_interval(clicks):
    #if clicks != None:
        if clicks % 2 == 1:
            return 600000
        elif clicks % 2 == 0:
            return 2000

@app.callback(Output('overall_content', 'children'), [Input('tabs', 'value'), Input('tab1_interval', 'n_intervals')])
def content_links_overall(selected_tab, interval):
    to_return = html.Div([
                    html.Div([
                        html.Div([
                                html.H1('h1 tag ' + str(interval)),
                                dcc.Graph(id='histogram_time', figure=gen_histogram1())
                        ], className = 'six columns'),
                        html.Div([
                                dcc.Graph(id = 'histogram_attempts', figure = gen_histogram_attempts())
                        ], className = 'six columns')
                    ], className = 'row'),
                    html.Div([
                        html.Div([
                                dcc.Graph(id = 'histogram_pure_wait', figure = gen_histogram2())                
                        ], className = 'four columns'),
                        html.Div([
                                dcc.Graph(id = 'density_pure_wait', figure = gen_distplot())                
                        ], className = 'four columns'),        
                        html.Div([
                                dcc.Graph(id = 'pie_chart', figure = gen_piechart())                
                        ], className = 'four columns')            
                    ], className = 'row')
                ])
        
    return to_return

@app.callback(Output('times_refreshed', 'children'), [Input('tab2_interval', 'n_intervals')])
def times_refreshed(interval):
    return html.H5(interval)

@app.callback(Output('time_window_content', 'children'), [Input('tabs', 'value'), Input('tab2_interval', 'n_intervals'), Input('slider_MA_tab2', 'value'), Input('interval_button', 'n_clicks')])
def content_links_time_window(selected_tab, interval, slider, n_clicks):
    to_return = html.Div([
                    dcc.Graph(id = 'line_time', figure = gen_line1(slider))
                ])
         
    
    return to_return

    
def gen_line1(slider):
    x = [r['timestamp'] for r in adcollection_rmetrics.find()]
    x = [i for i in range(0, len(x) + 1)]
    y = [r['time success'] for r in adcollection_rmetrics.find()]
    y_MA = pd.Series(y).rolling(slider).mean()    
    
    trace = Scatter(x = x,
                    y = y,
                    name = 'Regular')
    trace_MA = Scatter(x = x,
                       y = y_MA,
                       marker = {'color':'#fb2e01'},
                        name = str(slider) + ' steps MA')
    
    layout = dict(
            title = 'Time to process links in time',
            xaxis = dict(title = 'Link nr.',
                         rangeslider=dict(visible = True)),
            yaxis = dict(title = 'Time [s]')
    )
    
    return Figure(data = [trace, trace_MA], layout = layout)
    

def gen_histogram1():
        
    values = [r['time success'] for r in adcollection_rmetrics.find()]
    avg_val = np.mean(values)
    median_val = np.median(values)
    bin_val = np.histogram(values, bins = 20)
    
    trace = Bar(x = bin_val[1],
                y = bin_val[0],
                marker = {'color':'#92b4f2'},
                opacity = 0.75)

    layout = Layout(
            title = 'Time per link histogram',
            xaxis = dict(
                    title = 'Time [s]'),
            yaxis = dict(
                    title = 'Count'),
            shapes= [dict(type =  'line',
                     line = Line(dash = 'dash',
                                   width = 5,
                                   color = '#cc0000'),
                     opacity = 0.5,
                     x0 = avg_val,
                     x1 = avg_val,
                     xref = 'x',
                     yref ='y',
                     y0 = 0,
                     y1 = np.max(bin_val[0])),
                    dict(type = 'line',
                    line = Line(dash = 'dash',
                                width = 5),
                    opacity = 0.5,
                    x0 = median_val,
                    x1 = median_val,
                    xref = 'x',
                    yref = 'y',
                    y0 =  0,
                    y1 = np.max(bin_val[0]))
            ],
            annotations = [
                    dict(x = avg_val,
                         y = np.max(bin_val[0]),
                         text = 'Mean = {:,.2f}'.format(avg_val),
                         showarrow = False),
                    dict(x = median_val,
                         y = np.max(bin_val[0] - 0.1 * np.max(bin_val[0])),
                         text = 'Median = {:,.2f}'.format(median_val),
                         showarrow = False),
                    dict(x = bin_val[1][-4],
                         y = np.max(bin_val[0]),
                         text = 'Total count = {:}'.format(len(values)),
                         showarrow = False)])
    return Figure(data = [trace], layout = layout)

def gen_histogram_attempts():
    counted_vals = Counter([r['attempts'] for r in adcollection_rmetrics.find()])
    keys = list(counted_vals.keys())
    vals = [counted_vals[i] for i in counted_vals]
    
    trace = Bar(
            x = keys,
            y = vals,
            opacity = 0.75,
            marker = dict(
                    color = '#92b4f2'))
    
    layout = Layout(bargap = 0.2,
                    title = 'Nr. of attempts per link',
                    xaxis = dict(
                            type = 'category',
                            title = 'Nr. of attempts'),
                    yaxis = dict(
                            title = 'Count'))
    return Figure(data = [trace], layout = layout)

def gen_histogram2():
    values1 = [r['pure time'] for r in adcollection_rmetrics.find()]
    values2 = [r['waits'] for r in adcollection_rmetrics.find()]
    
    trace1 = Histogram(
            x = values1,
            opacity = 0.75,
            name = 'pure time',
            xbins = dict(start = 0,
                         end = np.max([np.max(values1), np.max(values2)]),
                         size = int(np.max([np.max(values1), np.max(values2)])/30)),
            marker = dict(
                    color = '#92b4f2'))
    trace2 = Histogram(
            x = values2,
            opacity = 0.75,
            name = 'wait time',
            xbins = dict(start = 0,
                         end = np.max([np.max(values1), np.max(values2)]),
                         size = int(np.max([np.max(values1), np.max(values2)])/30)),
            marker = dict(
                    color = '#ffb653'))
    layout = Layout(barmode = 'overlay',
                    title = 'Pure time vs. wait time per link histogram',
                    showlegend = False,
                    xaxis = dict(
                            title = 'Time [s]'),
                    yaxis = dict(
                            title = 'Count'))
    
    return Figure(data = [trace1, trace2], layout = layout)

def gen_distplot():
    values1 = [r['pure time'] for r in adcollection_rmetrics.find()]
    values2 = [r['waits'] for r in adcollection_rmetrics.find()]
    
    labels =['pure time', 'wait time']
        
    fig = ff.create_distplot([values1, values2], labels, show_hist = False, colors = ['#92b4f2', '#ffb653'])
    fig['layout'].update(legend = Legend(orientation = 'h'), title = 'Pure time vs. wait time per link distplot')
    
    return fig

def gen_piechart():
    labels = ['pure time', 'wait time']
    values = [np.sum([r['pure time'] for r in adcollection_rmetrics.find()]), np.sum([r['waits'] for r in adcollection_rmetrics.find()])]
    
    trace = Pie(labels = labels, values = values, marker = dict(colors = ['#92b4f2', '#ffb653']))
    
    layout = Layout(
            showlegend = False,
            title = 'Overall wait time vs. pure time'
            
    )
    
    return Figure(data = [trace], layout = layout)

if __name__ == '__main__':
    app.run_server(debug = True)