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
from dash.dependencies import Input, Output, Event, State
import pymongo
import numpy as np
from collections import Counter
import pandas as pd
import datetime
import json

myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection_rmetrics = scrapedb['rmetrics']

app = dash.Dash(__name__)
#app.config['suppress_callback_exceptions'] = True
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

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
                    ], className = 'four columns'),
                    html.Div([
                            html.H5('X axis')
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
                ], className = 'four columns'),
                html.Div([
                    dcc.RadioItems(id = 'xaxis',
                            options = [{'label': 'Number', 'value':'nr'},
                                              {'label': 'Date', 'value':'date'}
                                              ],
                            value = 'date',
                            labelStyle = {'display':'inline-block'})
                ], className = 'four columns')
                
                
            ], className = 'row'),
            html.Div([
                    html.Div([
                        dcc.Graph(id = 'line_time')
                    ], className = 'six columns'),
                    html.Div([
                        dcc.Graph(id = 'area_time')
                    ], className = 'six columns'),
                    dcc.Interval(
                            id = 'tab2_interval',
                            interval = 2000,
                            n_intervals = 0)
            ], className = 'row'),
            html.Div([
                    html.Div([
                        dcc.Graph(id = 'line_attempts')
                    ], className = 'six columns'),
                    html.Div([
                        dcc.Graph(id = 'line_pure_wait_sum')
                    ], className = 'six columns')
                    
                    
            ], className = 'row'),
            html.Div([
                    html.Div([
                        html.Pre(id = 'relayed data', style = styles['pre'])
                    ], className = 'six columns'),
                    html.Div([
                        html.Pre(id = 'relayed data status', style = styles['pre'])        
                    ], className = 'six columns')
                    
                    
            ], className = 'row')
        ]),
        dcc.Tab(label='Tab three', children=[
            html.Div(id = 'tab3_content')
        ]),
    ])
])
                    
#app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
app.css.append_css({'external_url':'https://codepen.io/amyoshino/pen/jzXypZ.css'})

@app.callback(Output('line_attempts', 'figure'),
              [Input('xaxis', 'value'),
               Input('tab2_interval', 'n_intervals')])
def line_attempts(xtype, interval):
    x = [r['timestamp'] for r in adcollection_rmetrics.find()]
    x_range = [x[-1] - datetime.timedelta(minutes = 30), x[-1]]
    if xtype == 'nr':
        x = [i for i in range(0, len(x) + 1)]
        x_range = [x[0], x[-1]]
    y1 = [r['attempts'] for r in adcollection_rmetrics.find()]
    y2 = pd.Series(y1).expanding().mean()
    
    trace = Scatter(x = x,
                    y = y1,
                    name = 'Regular')
    trace2 = Scatter(x = x,
                     y = y2,
                     name = 'CA',
                     marker = dict(
                             color = '#fb2e01'))
    
    layout = dict(
            title = 'Number of attempts per link',
            xaxis = dict(title = 'Link nr.',
                         range = x_range),
            yaxis = dict(title = 'Nr. of attempts')
    )
            
    if xtype == 'date':
        layout['xaxis']['rangeselector'] = dict(
                buttons = list([dict(count = 1,
                                     label = '1d',
                                     step = 'day',
                                     stepmode = 'backward'),
                                dict(count = 1,
                                     label = '1h',
                                     step = 'hour',
                                     stepmode = 'backward'),
                                dict(count = 30,
                                     label = '30m',
                                     step = 'minute',
                                     stepmode = 'backward'),
                                dict(count = 10,
                                     label = '10m',
                                     step = 'minute',
                                     stepmode = 'backward'),
                                dict(step = 'all')
                        ]))
    
    return Figure(data = [trace, trace2], layout = layout)

@app.callback(Output('line_pure_wait_sum', 'figure'),
              [Input('xaxis', 'value'),
               Input('tab2_interval', 'n_intervals')])
def line_pure_wait_sum(xtype, interval):
    x = [r['timestamp'] for r in adcollection_rmetrics.find()]
    x_range = [x[-1] - datetime.timedelta(minutes = 30), x[-1]]
    if xtype == 'nr':
        x = [i for i in range(0, len(x) + 1)]
        x_range = [x[0], x[-1]]
    y1 = pd.Series([r['pure time'] for r in adcollection_rmetrics.find()]).expanding().sum()
    y2 = pd.Series([r['waits'] for r in adcollection_rmetrics.find()]).expanding().sum()
    y3 = pd.Series([r['time success'] for r in adcollection_rmetrics.find()]).expanding().sum()
    y_trace5 = [0.5 for i in range(0, len(x))]
    y_trace6 = [1 for i in range(0, len(x))]
    
    trace = Scatter(x = x,
                    y = y1,
                    name = 'Pure time')
    trace2 = Scatter(x = x,
                     y = y2,
                     name = 'Wait time')
    trace3 = Scatter(x = x,
                     y = y3,
                     name = 'Total',
                     marker = dict(color = '#fb2e01'))
    trace4 = Scatter(x = x,
                     y = y2/y1,
                     name = 'Waits/Pure',
                     line = dict(dash = 'dash'),
                     yaxis = 'y2'
                     )
    trace5 = Scatter(x = x,
                     y = y_trace5,
                     line = dict(dash = 'dash'),
                     marker = dict(color = '#d7dbdd'),
                    yaxis = 'y2',
                    showlegend = False)
    trace6 = Scatter(x = x,
                     y = y_trace6,
                     line = dict(dash = 'dash'),
                     marker = dict(color = '#d7dbdd'),
                    yaxis = 'y2',
                    showlegend = False)
                     
    updatemenus = list([
        dict(type = 'buttons',
             active = -1,
             buttons = list([
                dict(label = 'H',
                     method = 'update',
                     args = [{'y':[y1/3600, y2/3600, y3/3600, y2/y1, y_trace5, y_trace6]}]),
                dict(label = 'M',
                     method = 'update',
                     args = [{'y':[y1/60, y2/60, y3/60, y2/y1, y_trace5, y_trace6]}]
                ),
                dict(label = 'S',
                     method = 'update',
                     args = [{'y':[y1, y2, y3, y2/y1, y_trace5, y_trace6]}]
                )
            ])
        )
    ])
    
    layout = dict(
            title = 'Cumulative sum of  times',
            xaxis = dict(title = 'Link nr.',
                         range = x_range),
            yaxis = dict(title = 'Time'),
            updatemenus = updatemenus,
            yaxis2 = dict(overlaying = 'y',
                          side = 'right',
                          title = 'Ratio')
    )
            
    if xtype == 'date':
        layout['xaxis']['rangeselector'] = dict(
            buttons = list([dict(count = 1,
                                 label = '1d',
                                 step = 'day',
                                 stepmode = 'backward'),
                            dict(count = 1,
                                 label = '1h',
                                 step = 'hour',
                                 stepmode = 'backward'),
                            dict(count = 30,
                                 label = '30m',
                                 step = 'minute',
                                 stepmode = 'backward'),
                            dict(count = 10,
                                 label = '10m',
                                 step = 'minute',
                                 stepmode = 'backward'),
                            dict(step = 'all')
                    ]))
    
    return Figure(data = [trace, trace2, trace3, trace4, trace5, trace6], layout = layout)

@app.callback(Output('relayed data status', 'children'),               
                [Input('xaxis', 'value')],
                [State('line_time', 'relayoutData')])
def display_relay_data_state(radio, r):
    return json.dumps(r, indent = 2)

@app.callback(Output('relayed data', 'children'),
              [Input('line_time', 'relayoutData')])
def display_relay_data(r):
    return json.dumps(r, indent = 2)

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

@app.callback(Output('line_time', 'figure'), [Input('tabs', 'value'), 
              Input('tab2_interval', 'n_intervals'), 
              Input('slider_MA_tab2', 'value'), 
              Input('interval_button', 'n_clicks'),
              Input('xaxis', 'value')])
def content_links_time_window(selected_tab, interval, slider, n_clicks, xaxis):
    to_return = gen_line1(slider, xaxis)
    
    return to_return

@app.callback(Output('area_time', 'figure'),
              [Input('tabs', 'value'),
               Input('tab2_interval', 'n_intervals'),
               Input('interval_button', 'n_clicks'),
               Input('xaxis', 'value'),
               Input('line_time', 'relayoutData')])
def content_links_area_chart(selected_tab, interval, n_clicks, xaxis, relay):
    to_return = gen_area1(xaxis, relay)       
    
    return to_return
    
def gen_line1(slider, xtype):
    x = [r['timestamp'] for r in adcollection_rmetrics.find()]
    x_range = [x[-1] - datetime.timedelta(minutes = 30), x[-1]]
    if xtype == 'nr':
        x = [i for i in range(0, len(x) + 1)]
    y = [r['time success'] for r in adcollection_rmetrics.find()]
    y_MA = pd.Series(y).rolling(slider).mean()    
    
    trace = Scatter(x = x,
                    y = y,
                    name = 'Regular')
    trace_cummean = Scatter(
            x = x,
            y = pd.Series(y).expanding().mean(),
            name = 'CA',
            visible = False)
    trace_cummedian = Scatter(
            x = x,
            y = pd.Series(y).expanding().median(),
            name = 'CM',
            visible = False)
    trace_cum1q = Scatter(
            x = x,
            y = pd.Series(y).expanding().quantile(0.25),
            name = 'C1Q',
            visible = False,
            line = dict(dash = 'dash'))
    trace_cum3q = Scatter(
            x = x,
            y = pd.Series(y).expanding().quantile(0.75),
            name = 'C3Q',
            visible = False,
            line = dict(dash = 'dash'))    
    trace_MA = Scatter(x = x,
                       y = y_MA,
                       marker = {'color':'#fb2e01'},
                        name = 'MA')
    
    updatemenus = list([
        dict(type = 'buttons',
             active = -1,
             buttons = list([
                dict(label = 'CAMQ',
                     method = 'update',
                     args = [{'visible':[False, True, True, True, True, False]},
                             {'title':'Whole time to process link - cum. statistics'}]
                ),
                dict(label = 'Reset',
                     method = 'update',
                     args = [{'visible':[True, False, False, False, False, True]},
                              {'title':'Whole time to process link'}]
                )
            ])
        )
    ])
    
    layout = dict(
            title = 'Whole time to process links',
            xaxis = dict(title = 'Link nr.',
                         rangeslider=dict(visible = True)),
            yaxis = dict(title = 'Time [s]'),
            updatemenus = updatemenus
    )
            
    if xtype == 'date':
        layout['xaxis']['rangeselector'] = dict(
                buttons = list([dict(count = 1,
                                     label = '1d',
                                     step = 'day',
                                     stepmode = 'backward'),
                                dict(count = 1,
                                     label = '1h',
                                     step = 'hour',
                                     stepmode = 'backward'),
                                dict(count = 30,
                                     label = '30m',
                                     step = 'minute',
                                     stepmode = 'backward'),
                                dict(count = 10,
                                     label = '10m',
                                     step = 'minute',
                                     stepmode = 'backward'),
                                dict(step = 'all')
                        ]))
        layout['xaxis']['range'] = x_range
    elif xtype == 'nr':
        layout['xaxis']['range'] = [x[0], x[-1]]
    
    return Figure(data = [trace, trace_cummean, trace_cummedian, trace_cum1q, trace_cum3q, trace_MA], layout = layout)

def gen_area1(xtype, relay):
    x = [r['timestamp'] for r in adcollection_rmetrics.find()]
    x_range = [x[-1] - datetime.timedelta(minutes = 30), x[-1]]
    if xtype == 'nr':
        x = [i for i in range(0, len(x) + 1)]
        x_range = [x[0], x[-1]]
        
    if 'xaxis.range[0]' in relay and 'xaxis.range[1]' in relay:
        x_range = [relay['xaxis.range[0]'], relay['xaxis.range[1]']]
    elif 'xaxis.range' in relay:
        x_range = [relay['xaxis.range'][0], relay['xaxis.range'][1]]
        
    y1 = [r['pure time'] for r in adcollection_rmetrics.find()]
    y2 = [r['waits'] for r in adcollection_rmetrics.find()]
    
    trace1 = Scatter(
            x = x,
            y = y1,
            name = 'Pure time')
    trace1_cummean = Scatter(
            x = x,
            y = pd.Series(y1).expanding().mean(),
            name = 'Pure time',
            visible = False)
    trace1_cummedian = Scatter(
            x = x,
            y = pd.Series(y1).expanding().median(),
            name = 'Pure time',
            visible = False)
    
    trace2 = Scatter(
            x = x,
            y = y2,
            name = 'Wait time')
    
    trace2_cummean = Scatter(
            x = x,
            y = pd.Series(y2).expanding().mean(),
            name = 'Wait time',
            visible = False)
    trace2_cummedian = Scatter(
            x = x,
            y = pd.Series(y2).expanding().median(),
            name = 'Wait time',
            visible = False)
            
    updatemenus = list([
        dict(type = 'buttons',
             active = -1,
             buttons = list([
                dict(label = 'CA',
                     method = 'update',
                     args = [{'visible':[False, True, False, False, True, False]},
                             {'title':'Time to process link - cumulative average'}]
                ),
                dict(label = 'CM',
                     method = 'update',
                     args = [{'visible':[False, False, True, False, False, True]},
                             {'title':'Time to process link - cumulative median'}]
                ),
                dict(label = 'Reset',
                     method = 'update',
                     args = [{'visible':[True, False, False, True, False, False]},
                              {'title':'Pure vs. wait time'}]
                )
            ])
        )
    ])
    
    layout = dict(
            title = 'Pure vs. wait time',
            xaxis = dict(title = 'Link nr.',
                         range = x_range),
            yaxis = dict(title = 'Time [s]'),
            updatemenus = updatemenus)
    
    
    
    if xtype == 'date':
        layout['xaxis']['rangeselector'] = dict(
                buttons = list([dict(count = 1,
                                     label = '1d',
                                     step = 'day',
                                     stepmode = 'backward'),
                                dict(count = 1,
                                     label = '1h',
                                     step = 'hour',
                                     stepmode = 'backward'),
                                dict(count = 30,
                                     label = '30m',
                                     step = 'minute',
                                     stepmode = 'backward'),
                                dict(count = 10,
                                     label = '10m',
                                     step = 'minute',
                                     stepmode = 'backward'),
                                dict(step = 'all')
                        ]))
    
    return Figure(data = [trace1, trace1_cummean, trace1_cummedian, trace2, trace2_cummean, trace2_cummedian], layout = layout)


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