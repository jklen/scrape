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

myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection_rmetrics = scrapedb['rmetrics']

app = dash.Dash(__name__)

app.layout = html.Div([
        html.Div([
            dcc.Tabs(id = 'tabs', value = 'requests', children = [
                    dcc.Tab(label = 'Requests', value = 'requests', children = [
                        dcc.Tabs(id = 'tabs_requests',  children = [
                                dcc.Tab(label = 'Overall', value = 'overall'),
                                dcc.Tab(label = 'Time window', value = 'time_window')
                        ])        
                    ]),
                    dcc.Tab(label = 'Proxies', value = 'proxies')
            ]),
            html.Div(id = 'tabs_content'),
            dcc.Interval(
                id='interval-component',
                interval=1*5000, # in milliseconds
                n_intervals=0
            )
        ])
    ])
            
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

@app.callback(Output('tabs_content', 'children'), [Input('tabs', 'value'), Input('tabs_requests', 'value'), Input('interval-component', 'n_intervals')])
def display_content(selected_tab, selected_req_tab, interval):
    if selected_tab == 'requests' and selected_req_tab == 'overall':
        to_return = html.Div([
                        html.Div([
                            html.Div([
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