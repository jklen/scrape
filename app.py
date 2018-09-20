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
from dash.dependencies import Input, Output
import pymongo
import numpy as np

myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection_rmetrics = scrapedb['rmetrics']

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        dcc.Graph(id='main_histogram')
    ], className = 'row'),
        
    html.Div([
        html.Div([
                dcc.Graph(id = 'histogram_pure_wait')                
        ], className = 'four columns'),
        html.Div([
                dcc.Graph(id = 'density_pure_wait')                
        ], className = 'four columns'),        
        html.Div([
                dcc.Graph(id = 'pie_chart')                
        ], className = 'four columns')            
    ], className = 'row'),
        
    dcc.Interval(
        id='interval-component',
        interval=1*5000, # in milliseconds
        n_intervals=0
    )
])
    
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

@app.callback(Output('main_histogram', 'figure'),
              [Input('interval-component', 'n_intervals')])
def gen_histogram1(interval):
        
    values = [r['time success'] for r in adcollection_rmetrics.find()]
    avg_val = np.mean(values)
    median_val = np.median(values)
    bin_val = np.histogram(values, bins = 30)
    
    trace = Bar(x = bin_val[1],
                y = bin_val[0],
                marker = {'color':'#92b4f2'},
                opacity = 0.75)

    layout = Layout(
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

@app.callback(Output('histogram_pure_wait', 'figure'),
              [Input('interval-component', 'n_intervals')])
def gen_histogram2(interval):
    values1 = [r['pure time'] for r in adcollection_rmetrics.find()]
    values2 = [r['waits'] for r in adcollection_rmetrics.find()]
    
    trace1 = Histogram(
            x = values1,
            opacity = 0.75,
            name = 'pure time',
            xbins = dict(start = 0,
                         end = np.max([np.max(values1), np.max(values2)]),
                         size = int(np.max([np.max(values1), np.max(values2)])/30)))
    trace2 = Histogram(
            x = values2,
            opacity = 0.75,
            name = 'wait time',
            xbins = dict(start = 0,
                         end = np.max([np.max(values1), np.max(values2)]),
                         size = int(np.max([np.max(values1), np.max(values2)])/30)))
    layout = Layout(barmode = 'overlay',
                    legend = Legend(orientation = 'h'))
    
    return Figure(data = [trace1, trace2], layout = layout)

@app.callback(Output('density_pure_wait', 'figure'),
              [Input('interval-component', 'n_intervals')])
def gen_densityplot(interval):
    values1 = [r['pure time'] for r in adcollection_rmetrics.find()]
    values2 = [r['waits'] for r in adcollection_rmetrics.find()]
    
    labels =['pure time', 'wait time']
        
    fig = ff.create_distplot([values1, values2], labels, show_hist = False)
    fig['layout'].update(legend = Legend(orientation = 'h'))
    
    return fig

@app.callback(Output('pie_chart', 'figure'),
              [Input('interval-component', 'n_intervals')])
def gen_piechart(interval):
    labels = ['pure time', 'wait time']
    values = [np.sum([r['pure time'] for r in adcollection_rmetrics.find()]), np.sum([r['waits'] for r in adcollection_rmetrics.find()])]
    
    trace = Pie(labels = labels, values = values)
    
    layout = Layout(
            legend = Legend(
                    orientation = 'h'
            )
            
    )
    
    return Figure(data = [trace], layout = layout)

if __name__ == '__main__':
    app.run_server(debug = True)