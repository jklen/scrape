# -*- coding: utf-8 -*-
"""
Created on Tue Sep 18 20:59:57 2018

@author: j.klen
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

myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection_rmetrics = scrapedb['rmetrics']
adcollection_poolmetrics = scrapedb['poolmetrics']
adcollection_proxies = scrapedb['proxies']

app = dash.Dash(__name__)
app.config['suppress_callback_exceptions'] = True
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'},
    'tab':{'backgroundColor':'#fdfdfd',
           'padding':'6px'},
    'selected_tab':{'backgroundColor':'#d9eefc',
                    'padding':'6px'}
}

app.layout = html.Div([
    html.Div([
            html.H3('Scraper'),
            html.Button(children = 'Stop refresh', id = 'interval_button'),
            html.Div(id = 'times_refreshed'),
            html.Div(id = 'tab_prompts', style = {'display':'none'}, children = [
                html.H5('Moving average'),
                html.Button(id = 'ma_down', children = '<', n_clicks = 0, n_clicks_timestamp = -1),
                dcc.Input(id = 'ma_input', value = '5', type = 'text', size = 3),
                html.Button(id = 'ma_up', children = '>', n_clicks = 0, n_clicks_timestamp = -1),
                html.H5('X axis type'),
                html.Div([
                    dcc.RadioItems(id = 'xaxis',
                                options = [{'label': 'Number', 'value':'nr'},
                                                  {'label': 'Date', 'value':'date'}
                                                  ],
                                value = 'date',
                                labelStyle = {'display':'inline-block'})
                ]),
                html.Div([
                    dcc.Checklist(
                            id = 'limit_check',
                            options = [{'label':'Limit visible data', 'value':'limit'}],
                            values = ['limit'])
                ]),
                    
                dcc.Input(id = 'linput',
                          type = 'text',
                          value = '200',
                          style = {'display':'inline-block'})
            ]),
            html.Div(id = 'proxy_prompts', style = {'display':'none'}, children = [
                dcc.RadioItems(id = 'proxy_radio',
                               options = [{'label':'All proxy data', 'value':'all'},
                                          {'label':'Window data', 'value':'window'}],
                                value = 'all'),
                dcc.Input(id = 'proxy_window_input',
                          type = 'text',
                          value = '10')
            ])
    ], className = 'two columns'),
    html.Div([
        dcc.Tabs(id="tabs", children=[
            dcc.Tab(label='Links overall', value = 'links_overall', style = styles['tab'], selected_style = styles['selected_tab'], children=[
                html.Div(id = 'overall_content'), 
                        dcc.Interval(
                                id = 'tab1_interval',
                                interval = 2000,
                                n_intervals = 0)
            ]),
            dcc.Tab(label='Links time window', value = 'links_time', style = styles['tab'], selected_style = styles['selected_tab'],  children=[
                html.Div(id = 'links_time_charts', children = [
                    html.Div([
                            html.Div([
                                dcc.Graph(id = 'line_time')
                            ], className = 'six columns'),
                            html.Div([
                                dcc.Graph(id = 'area_time')
                            ], className = 'six columns')
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
                            
                            
                    ], className = 'row'),
                    dcc.Interval(
                            id = 'tab2_interval',
                            interval = 2000,
                            n_intervals = 0)
                ])
            ]),
            dcc.Tab(label='Pool', value = 'pool', style = styles['tab'], selected_style = styles['selected_tab'], children=[
                html.Div(id = 'pool_charts', children = [
                    html.Div([
                            html.Div([
                                    dcc.Graph(id = 'line_bandit_means')
                            ], className = 'six columns'),
                            html.Div([
                                    dcc.Graph(id = 'bar_bandit_chosennr')
                            ], className = 'six columns')
                            
                    ], className = 'row'),
                    html.Div([
                            html.Div([
                                    dcc.Graph(id = 'line_position_change')                            
                            ], className = 'twelve columns')
                            
                    ], className = 'row'),
                    dcc.Interval(
                            id = 'tab3_interval',
                            interval = 2000,
                            n_intervals = 0)
                ])
            ]),
            dcc.Tab(label = 'Proxies', value = 'proxies', style = styles['tab'], selected_style = styles['selected_tab'], children = [
                html.Div(id = 'proxies_charts', children = [
                    html.Div([
                            html.Div([
                                    dcc.Graph(id = 'boxplot_bandits')
                            ], className = 'six columns'),
                            html.Div([
                                    dcc.Graph(id = 'boxplot_proxies')
                            ], className = 'six columns')
                    ], className = 'row'),
                    html.Div([
                            html.Div([
                                    dcc.Graph(id = 'scatter_proxies')
                            ], className = 'twelve columns')
                            
                    ], className = 'row'),
                    html.Div([
                            html.Div([
                                html.Pre(id = 'bandit_click', style = styles['pre'])
                            ], className = 'six columns'),
                            html.Div([
                                html.Pre(id = 'proxy_click', style = styles['pre'])
                            ], className = 'six columns')
                            
                            
                    ], className = 'row'),
                    dcc.Interval(
                            id = 'tab4_interval',
                            interval = 2000,
                            n_intervals = 0)
                ])
            ])
        ])
    
    ])
])
                    
#app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
app.css.append_css({'external_url':'https://codepen.io/amyoshino/pen/jzXypZ.css'})

@app.callback(Output('times_refreshed', 'children'),
              [Input('tabs', 'value'),
               Input('tab1_interval', 'n_intervals'),
               Input('tab2_interval', 'n_intervals'),
               Input('tab3_interval', 'n_intervals'),
               Input('tab4_interval', 'n_intervals')])
def times_refreshed(tab, int1, int2, int3, int4):
    if tab == 'links_overall':
        to_return = html.H5('Times refreshed: ' + str(int1))
    elif tab == 'links_time':
        to_return = html.H5('Times refreshed: ' + str(int2))
    elif tab == 'pool':
        to_return = html.H5('Times refreshed: ' + str(int3))
    elif tab == 'proxies':
        to_return = html.H5('Times refreshed: ' + str(int4))
    
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

@app.callback(Output('bandit_click', 'children'),
              [Input('boxplot_bandits', 'clickData')])
def display_bandit_click(r):
    return json.dumps(r, indent = 2)

@app.callback(Output('proxy_click', 'children'),
              [Input('boxplot_proxies', 'clickData')])
def display_proxy_click(r):
    return json.dumps(r, indent = 2)

@app.callback(Output('boxplot_proxies', 'figure'),
              [Input('tab4_interval','n_intervals'),
               Input('boxplot_bandits', 'clickData'),
               Input('proxy_window_input', 'value'),
               Input('proxy_radio', 'value')])
def boxplot_proxies(interval, clicked_bandit, window, pradio):
    proxies = [i for i in adcollection_proxies.find()]
    try:
        clicked_bandit = clicked_bandit['points'][0]['curveNumber']
    except:
        clicked_bandit = 0
    else:
        pass
    
    if pradio == 'all':
        proxy_data = [{'y':proxy['response_times']} for proxy in proxies if proxy['bandit'][-1] == clicked_bandit and len(proxy['response_times']) > 0]
    elif pradio == 'window':
        window = int(window)
        proxy_data = [{'y':proxy['response_times'][-window:]} for proxy in proxies if proxy['bandit'][-1] == clicked_bandit and len(proxy['response_times']) > 0]

    data = [Box(y = proxy['y'], name = 'p' + str(i)) for i, proxy in enumerate(proxy_data)]
    data0 = Scatter(x = ['p' + str(i) for i in range(0, len(proxy_data))],
                    y = [len(i['y']) for i in proxy_data],
                    yaxis = 'y2',
                    line = dict(width = 1),
                    opacity = 0.5)
    data.append(data0)
    
    layout = dict(showlegend = False, title = 'Proxies response times in bandit ' + str(clicked_bandit),
                  xaxis = dict(title = 'Proxy'),
                  yaxis = dict(title = 'Proxies reposne times [s]'),
                  yaxis2 = dict(overlaying = 'y',
                                side = 'right',
                                title = 'Nr. of times used'),
                    margin = dict(l = 50, r = 80, t = 80, b = 50))
    
    return Figure(data = data, layout = layout)

@app.callback(Output('scatter_proxies', 'figure'),
              [Input('tab4_interval', 'n_intervals'),
               Input('boxplot_bandits', 'clickData'),
               Input('proxy_window_input', 'value'),
               Input('proxy_radio', 'value')])
def scatter_proxies(interval, clicked_bandit, window, pradio):
    proxies = [i for i in adcollection_proxies.find()]
    try:
        clicked_bandit = clicked_bandit['points'][0]['curveNumber']
    except:
        clicked_bandit = 0
    else:
        pass
    
    if pradio == 'all':
        proxy_data = [{'x':proxy['response_timestamp'], 'y':proxy['response_times'], 'name':proxy['_id']} for proxy in proxies if proxy['bandit'][-1] == clicked_bandit]
    elif pradio == 'window':
        window = int(window)
        proxy_data = [{'x':proxy['response_timestamp'][-window:], 'y':proxy['response_times'][-window:], 'name':proxy['_id']} for proxy in proxies if proxy['bandit'][-1] == clicked_bandit]

    data = [Scatter(x = proxy['x'], y = proxy['y'], name = proxy['name'], line = {'width':1}, marker = {'size':5}, mode = 'lines+markers') for proxy in proxy_data]
    layout = dict(title = 'Proxies response times in bandit ' + str(clicked_bandit),
                  yaxis = dict(title = 'Response time [s]'),
                  margin = dict(l = 50, r = 80, t = 80, b = 50))
    
    return Figure(data = data, layout = layout)

@app.callback(Output('boxplot_bandits', 'figure'),
              [Input('tab4_interval', 'n_intervals')])
def boxplot_bandits(interval):
    bandit_data = list(adcollection_poolmetrics.find().limit(1).sort([('$natural',-1)]))[0]
    bandit_data = [[bandit_data['bandit_mins'][i], bandit_data['bandit_q1s'][i], bandit_data['bandit_q1s'][i], bandit_data['bandit_medians'][i], bandit_data['bandit_q3s'][i], bandit_data['bandit_q3s'][i], bandit_data['bandit_maxs'][i]] for i in range(0, len(bandit_data['bandit_means']))]
    
    data = [Box(y = j, name = 'b' + str(i)) for i, j in enumerate(bandit_data)]
    
    layout= dict(
            title = 'Bandits proxies means',
            xaxis = dict(title = 'Bandit'),
            yaxis = dict(title = 'Proxies means [s]'),
            showlegend = False,
            margin = dict(l = 50, r = 50, t = 80, b = 50))
    
    return Figure(data = data, layout = layout)

@app.callback(Output('ma_input', 'value'),
              [Input('ma_up', 'n_clicks'),
               Input('ma_up', 'n_clicks_timestamp'),
               Input('ma_down', 'n_clicks'),
               Input('ma_down', 'n_clicks_timestamp')],
              [State('ma_input', 'value')])
def ma_input(click_up, click_up_ts, click_down, click_down_ts, ma_state):
    if click_up_ts > click_down_ts:
        if click_down_ts == -1 and click_up_ts == 0:
            to_return = str(6)
        else:
            to_return = str(int(ma_state) + 1)
    elif click_up_ts < click_down_ts:
        if click_down_ts == 0 and click_up_ts == -1:
            to_return = str(4)
        else:
            to_return = str(int(ma_state) - 1) if int(ma_state) > 2 else str(2)
    
    return to_return

@app.callback(Output('proxy_prompts', 'style'),
              [Input('tabs', 'value')])
def proxy_prompts(tab):
    if tab == 'proxies':
        to_return = {'display':'inline-block'}
    else:
        to_return = {'display':'none'}
    
    return to_return

@app.callback(Output('tab_prompts', 'style'),
              [Input('tabs', 'value')])
def tab_prompts(tab):
    if tab in ['links_time', 'pool']:
        to_return = {'display':'inline-block'}
    else:
        to_return = {'display':'none'}
    return to_return

@app.callback(Output('line_position_change', 'figure'),
              [Input('tab3_interval', 'n_intervals'),
               Input('xaxis', 'value'),
               Input('ma_input', 'value'),
               Input('linput', 'value'),
               Input('limit_check', 'values')])
def line_position_change(interval, xtype, ma, linput, lcheck):
    ma = int(ma)
    x = [r['timestamp_pool_update'] for r in adcollection_poolmetrics.find()]
    x_range = [x[-1] - datetime.timedelta(minutes = 30), x[-1]]
    if xtype == 'nr':
        x = [i for i in range(0, len(x) + 1)]
        x_range = [x[0], x[-1]]
    y1 = [r['position_change'] for r in adcollection_poolmetrics.find()]
    y2 = pd.Series(y1).rolling(ma).mean()
    y3 = pd.Series(y1).expanding().mean()
    
    try:
        lcheck = lcheck[0]
    except:
        lcheck = False
    else:
        lcheck = True
        linput = int(linput)
        x = x[-linput:]
        x_range[0] = x[0]
    
    trace = Scatter(x = x,
                    y = y1[-linput:] if lcheck else y1,
                    name = 'Position change',
                    marker = dict(color = '#92b4f2'),
                    line = dict( width = 1),
                    mode = 'lines')
    trace2 = Scatter(x = x,
                     y = y2[-linput:] if lcheck else y2,
                     name = 'MA',
                     marker = dict(
                             color = '#fb2e01'),
                    line = dict(width = 1.5),
                    mode = 'lines')
                             
    trace3 = Scatter(x = x,
                     y = y3[-linput:] if lcheck else y3,
                     name = 'CA',
                     marker = dict(
                             color = '#0d3592'),
                    line = dict(dash = 'dash',
                                width = 1.5),
                    yaxis = 'y2',
                    mode = 'lines')
    
    layout = dict(
            title = 'Proxies position change',
            xaxis = dict(title = 'Request nr.',
                         range = x_range),
            yaxis = dict(title = 'Ratio',
                         range = [0,1.1]),
            yaxis2 = dict(overlaying = 'y',
                          side = 'right',
                          range = [0,1.1]),
            margin = dict(l = 50, r = 50, t = 80, b = 50)
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
    
    return Figure(data = [trace, trace2, trace3], layout = layout)

@app.callback(Output('bar_bandit_chosennr', 'figure'),
              [Input('tab3_interval', 'n_intervals'),
               Input('xaxis', 'value')])
def bar_bandit_chosennr(interval, val):
    counted_vals = Counter([b['choosen_bandit'] for b in adcollection_poolmetrics.find()])
    counted_vals_sorted = sorted(counted_vals.items(), key = itemgetter(0))
    keys = [i[0] for i in counted_vals_sorted]
    vals = [i[1] for i in counted_vals_sorted]
    
    trace = Bar(
            x = keys,
            y = vals,
            opacity = 0.75,
            marker = dict(
                    color = '#92b4f2'))
    
    layout = dict(bargap = 0.2,
                    title = 'How much each bandit was chosen',
                    xaxis = dict(
                            type = 'category',
                            title = 'Bandit'),
                    yaxis = dict(
                            title = 'Count'),
                    margin = dict(l = 50, r = 50, t = 80, b = 50))
    return Figure(data = [trace], layout = layout)

@app.callback(Output('line_bandit_means', 'figure'),
              [Input('tab3_interval', 'n_intervals'),
               Input('linput', 'value'),
               Input('limit_check', 'values')])
def line_bandit_means(interval, linput, lcheck):
    meansdf = pd.DataFrame([b['bandit_means'] for b in adcollection_poolmetrics.find()])
    x = [i for i in range(0, len(meansdf) + 1)]
    
    try:
        lcheck = lcheck[0]
    except:
        lcheck = False
    else:
        lcheck = True
        linput = int(linput)
        x = x[-linput:]
    
    data = [Scatter(x = x, y = meansdf[i][-linput:] if lcheck else meansdf[i], name = str(i), line = dict(width = 1)) for i in list(meansdf)]
    layout= dict(
            title = 'Bandits cumulative mean',
            xaxis = dict(title = 'Request nr.'),
            yaxis = dict(title = 'Time [s]'),
            margin = dict(l = 50, r = 50, t = 80, b = 50))
    
    return Figure(data = data, layout = layout)

@app.callback(Output('line_attempts', 'figure'),
              [Input('xaxis', 'value'),
               Input('tab2_interval', 'n_intervals'),
               Input('linput', 'value'),
               Input('limit_check', 'values')])
def line_attempts(xtype, interval, linput, lcheck):
    x = [r['timestamp'] for r in adcollection_rmetrics.find()]
    x_range = [x[-1] - datetime.timedelta(minutes = 30), x[-1]]
    if xtype == 'nr':
        x = [i for i in range(0, len(x) + 1)]
        x_range = [x[0], x[-1]]
    y1 = [r['attempts'] for r in adcollection_rmetrics.find()]
    y2 = pd.Series(y1).expanding().mean()
    
    try:
        lcheck = lcheck[0]
    except:
        lcheck = False
    else:
        lcheck = True
        linput = int(linput)
        x = x[-linput:]
        x_range[0] = x[0]
    
    trace = Scatter(x = x,
                    y = y1[-linput:] if lcheck else y1,
                    name = 'Regular',
                    line = dict(width = 1),
                    marker = {'color':'#92b4f2'},
                    mode = 'lines')
    trace2 = Scatter(x = x,
                     y = y2[-linput:] if lcheck else y2,
                     name = 'CA',
                     marker = dict(
                             color = '#fb2e01'),
                    line = dict(width = 1.5),
                    mode = 'lines')
    
    layout = dict(
            title = 'Number of attempts per link',
            xaxis = dict(title = 'Link nr.',
                         range = x_range),
            yaxis = dict(title = 'Nr. of attempts'),
            margin = dict(l = 50, r = 50, t = 80, b = 50)
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
               Input('tab2_interval', 'n_intervals'),
               Input('linput', 'value'),
               Input('limit_check', 'values')])
def line_pure_wait_sum(xtype, interval, linput, lcheck):
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
    
    try:
        lcheck = lcheck[0]
    except:
        lcheck = False
    else:
        lcheck = True
        linput = int(linput)
        x = x[-linput:]
        x_range[0] = x[0]
    
    trace = Scatter(x = x,
                    y = y1[-linput:] if lcheck else y1,
                    name = 'Pure time',
                    line = dict(width = 1),
                    marker = {'color':'#92b4f2'},
                    mode = 'lines')
    trace2 = Scatter(x = x,
                     y = y2[-linput:] if lcheck else y2,
                     name = 'Wait time',
                    line = dict(width = 1),
                    mode = 'lines')
    trace3 = Scatter(x = x,
                     y = y3[-linput:] if lcheck else y3,
                     name = 'Total',
                     marker = dict(color = '#fb2e01'),
                    line = dict(width = 1),
                    mode = 'lines')
    trace4 = Scatter(x = x,
                     y = (y2/y1)[-linput:] if lcheck else y2/y1,
                     name = 'Waits/Pure',
                     line = dict(dash = 'dash',
                                 width = 1),
                     yaxis = 'y2',
                     mode = 'lines'
                     )
    trace5 = Scatter(x = x,
                     y = y_trace5[-linput:] if lcheck else y_trace5,
                     line = dict(dash = 'dash'),
                     marker = dict(color = '#d7dbdd'),
                    yaxis = 'y2',
                    showlegend = False,
                    mode = 'lines')
    trace6 = Scatter(x = x,
                     y = y_trace6[-linput:] if lcheck else y_trace6,
                     line = dict(dash = 'dash'),
                     marker = dict(color = '#d7dbdd'),
                    yaxis = 'y2',
                    showlegend = False,
                    mode = 'lines')
                     
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
            title = 'Cumulative sum of times',
            xaxis = dict(title = 'Link nr.',
                         range = x_range),
            yaxis = dict(title = 'Time'),
            updatemenus = updatemenus,
            yaxis2 = dict(overlaying = 'y',
                          side = 'right',
                          title = 'Ratio'),
            margin = dict(l = 50, r = 50, t = 80, b = 50)
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
    if clicks:
        if clicks % 2 == 1:
            return 'Start refresh'
        elif clicks % 2 == 0:
            return 'Stop refresh'
    else:
        return 'Stop refresh'

@app.callback(Output('tab1_interval', 'interval'), [Input('interval_button', 'n_clicks')])
def stop_interval(clicks):
    if clicks != None:
        if clicks % 2 == 1:
            return 600000
        elif clicks % 2 == 0:
            return 2000
    else:
        return 2000

@app.callback(Output('tab2_interval', 'interval'), [Input('interval_button', 'n_clicks')])
def stop_interval2(clicks):
    if clicks:
        if clicks % 2 == 1:
            return 600000
        elif clicks % 2 == 0:
            return 2000
    else:
        return 2000

@app.callback(Output('tab3_interval', 'interval'), [Input('interval_button', 'n_clicks')])
def stop_interval3(clicks):
    if clicks:
        if clicks % 2 == 1:
            return 600000
        elif clicks % 2 == 0:
            return 2000
    else:
        return 2000

@app.callback(Output('tab4_interval', 'interval'), [Input('interval_button', 'n_clicks')])
def stop_interval4(clicks):
    if clicks:
        if clicks % 2 == 1:
            return 600000
        elif clicks % 2 == 0:
            return 2000
    else:
        return 2000

@app.callback(Output('overall_content', 'children'), [Input('tabs', 'value'), Input('tab1_interval', 'n_intervals')])
def content_links_overall(selected_tab, interval):
    to_return = html.Div([
                    html.Div([
                        html.Div([
                                dcc.Graph(id='histogram_time', figure=gen_histogram1(), config = {'displayModeBar':False})
                        ], className = 'six columns'),
                        html.Div([
                                dcc.Graph(id = 'histogram_attempts', figure = gen_histogram_attempts(), config = {'displayModeBar':False})
                        ], className = 'six columns')
                    ], className = 'row'),
                    html.Div([
                        html.Div([
                                dcc.Graph(id = 'histogram_pure_wait', figure = gen_histogram2(), config = {'displayModeBar':False})                
                        ], className = 'four columns'),
                        html.Div([
                                dcc.Graph(id = 'density_pure_wait', figure = gen_distplot(), config = {'displayModeBar':False})                
                        ], className = 'four columns'),        
                        html.Div([
                                dcc.Graph(id = 'pie_chart', figure = gen_piechart(), config = {'displayModeBar':False})                
                        ], className = 'four columns')            
                    ], className = 'row')
                ])
        
    return to_return

@app.callback(Output('line_time', 'figure'),
              [Input('tabs', 'value'), 
              Input('tab2_interval', 'n_intervals'), 
              Input('ma_input', 'value'), 
              Input('interval_button', 'n_clicks'),
              Input('xaxis', 'value'),
              Input('linput', 'value'),
              Input('limit_check', 'values')])
def content_links_time_window(selected_tab, interval, ma, n_clicks, xaxis, linput, lcheck):
    to_return = gen_line1(int(ma), xaxis, linput, lcheck)
    
    return to_return

@app.callback(Output('area_time', 'figure'),
              [Input('tabs', 'value'),
               Input('tab2_interval', 'n_intervals'),
               Input('interval_button', 'n_clicks'),
               Input('xaxis', 'value'),
               Input('line_time', 'relayoutData'),
               Input('ma_input', 'value'),
               Input('linput', 'value'),
               Input('limit_check', 'values')])
def content_links_area_chart(selected_tab, interval, n_clicks, xaxis, relay, ma, linput, lcheck):
    to_return = gen_area1(xaxis, relay, int(ma), linput, lcheck)       
    
    return to_return
    
def gen_line1(slider, xtype, linput, lcheck):
    x = [r['timestamp'] for r in adcollection_rmetrics.find()]
    x_range = [x[-1] - datetime.timedelta(minutes = 30), x[-1]]
    if xtype == 'nr':
        x = [i for i in range(0, len(x) + 1)]
    y = [r['time success'] for r in adcollection_rmetrics.find()]
    y_MA = pd.Series(y).rolling(slider).mean()
    
    try:
        lcheck = lcheck[0]
    except:
        lcheck = False
    else:
        lcheck = True
        linput = int(linput)
        x = x[-linput:]
        x_range[0] = x[0]
    
    trace = Scatter(x = x,
                    y = y[-linput:] if lcheck else y,
                    name = 'Regular',
                    line = dict(width = 1),
                    marker = {'color':'#92b4f2'},
                    mode = 'lines')
    trace_cummean = Scatter(
            x = x,
            y = pd.Series(y).expanding().mean()[-linput:] if lcheck else pd.Series(y).expanding().mean(),
            name = 'CA',
            visible = False,
            line = dict(width = 1),
            mode = 'lines')
    trace_cummedian = Scatter(
            x = x,
            y = pd.Series(y).expanding().median()[-linput:] if lcheck else pd.Series(y).expanding().median(),
            name = 'CM',
            visible = False,
            line = dict(width = 1),
            mode = 'lines')
    trace_cum1q = Scatter(
            x = x,
            y = pd.Series(y).expanding().quantile(0.25)[-linput:] if lcheck else pd.Series(y).expanding().quantile(0.25),
            name = 'C1Q',
            visible = False,
            line = dict(dash = 'dash',
                        width = 1),
            mode = 'lines')
    trace_cum3q = Scatter(
            x = x,
            y = pd.Series(y).expanding().quantile(0.75)[-linput:] if lcheck else pd.Series(y).expanding().quantile(0.75),
            name = 'C3Q',
            visible = False,
            line = dict(dash = 'dash',
                        width = 1),
            mode = 'lines')    
    trace_MA = Scatter(x = x,
                       y = y_MA[-linput:] if lcheck else y_MA,
                       marker = {'color':'#fb2e01'},
                        name = 'MA',
                        line = dict(width = 1),
                        mode = 'lines')
    
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
            xaxis = dict(title = 'Link nr.'),
            yaxis = dict(title = 'Time [s]'),
            updatemenus = updatemenus,
            margin = dict(l = 50, r = 50, t = 80, b = 50)
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

def gen_area1(xtype, relay, ma, linput, lcheck):
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
    
    try:
        lcheck = lcheck[0]
    except:
        lcheck = False
    else:
        lcheck = True
        linput = int(linput)
        x = x[-linput:]
        x_range[0] = x[0]
    
    trace1 = Scatter(
            x = x,
            y = y1[-linput:] if lcheck else y1,
            name = 'Pure time',
            line = dict(width = 1),
            marker = {'color':'#92b4f2'},
            mode = 'lines')
    trace1_cummean = Scatter(
            x = x,
            y = pd.Series(y1).expanding().mean()[-linput:] if lcheck else pd.Series(y1).expanding().mean(),
            name = 'Pure time',
            visible = False,
            line = dict(width = 1),
            marker = {'color':'#92b4f2'},
            mode = 'lines')
    trace1_cummedian = Scatter(
            x = x,
            y = pd.Series(y1).expanding().median()[-linput:] if lcheck else pd.Series(y1).expanding().median(),
            name = 'Pure time',
            visible = False,
            line = dict(width = 1),
            marker = {'color':'#92b4f2'},
            mode = 'lines')
    trace1_ma = Scatter(
            x = x,
            y = pd.Series(y1).rolling(ma).mean()[-linput:] if lcheck else pd.Series(y1).rolling(ma).mean(),
            name = 'Pure time MA',
            visible = True,
            line = dict(width = 1.5, dash = 'dash'),
            marker = dict(color = '#0d3592'),
            mode = 'lines')
    
    trace2 = Scatter(
            x = x,
            y = y2[-linput:] if lcheck else y2,
            name = 'Wait time',
            line = dict(width = 1),
            marker = dict(color = '#ffb653'),
            mode = 'lines')
    
    trace2_cummean = Scatter(
            x = x,
            y = pd.Series(y2).expanding().mean()[-linput:] if lcheck else pd.Series(y2).expanding().mean(),
            name = 'Wait time',
            visible = False,
            line = dict(width = 1),
            mode = 'lines')
    trace2_cummedian = Scatter(
            x = x,
            y = pd.Series(y2).expanding().median()[-linput:] if lcheck else pd.Series(y2).expanding().median(),
            name = 'Wait time',
            visible = False,
            line = dict(width = 1),
            mode = 'lines')
    trace2_ma = Scatter(
            x = x,
            y = pd.Series(y2).rolling(ma).mean()[-linput:] if lcheck else pd.Series(y2).rolling(ma).mean(),
            name = 'Wait time MA',
            visible = True,
            line = dict(width = 1.5, dash = 'dash'),
            marker = dict(color = '#e46406'),
            mode = 'lines')
            
    updatemenus = list([
        dict(type = 'buttons',
             active = -1,
             buttons = list([
                dict(label = 'CA',
                     method = 'update',
                     args = [{'visible':[False, True, False, False, False, True, False, False]},
                             {'title':'Time to process link - cumulative average'}]
                ),
                dict(label = 'CM',
                     method = 'update',
                     args = [{'visible':[False, False, True, False, False, False, True, False]},
                             {'title':'Time to process link - cumulative median'}]
                ),
                dict(label = 'Reset',
                     method = 'update',
                     args = [{'visible':[True, False, False, True, True, False, False, True]},
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
            updatemenus = updatemenus,
            margin = dict(l = 50, r = 50, t = 80, b = 50))
    
    
    
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
    
    return Figure(data = [trace1, trace1_cummean, trace1_cummedian, trace1_ma, trace2, trace2_cummean, trace2_cummedian, trace2_ma], layout = layout)


def gen_histogram1():
        
    values = [r['time success'] for r in adcollection_rmetrics.find()]
    avg_val = np.mean(values)
    median_val = np.median(values)
    bin_val = np.histogram(values, bins = 20)
    
    trace = Bar(x = bin_val[1],
                y = bin_val[0],
                marker = {'color':'#92b4f2'},
                opacity = 0.75)

    layout = dict(
            title = 'Time per link histogram',
            margin = dict(l = 50, r = 50, t = 80, b = 50),
            xaxis = dict(
                    title = 'Time [s]'),
            yaxis = dict(
                    title = 'Count'),
            shapes= [dict(type =  'line',
                     line = dict(dash = 'dash',
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
                    line = dict(dash = 'dash',
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
    counted_vals_sorted = sorted(counted_vals.items(), key = itemgetter(0))
    keys = [i[0] for i in counted_vals_sorted]
    vals = [i[1] for i in counted_vals_sorted]
    
    trace = Bar(
            x = keys,
            y = vals,
            opacity = 0.75,
            marker = dict(
                    color = '#92b4f2'))
    
    layout = dict(bargap = 0.2,
                    title = 'Nr. of attempts per link',
                    xaxis = dict(
                            type = 'category',
                            title = 'Nr. of attempts'),
                    yaxis = dict(
                            title = 'Count'),
                    margin = dict(l = 50, r = 50, t = 80, b = 50))
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
    layout = dict(barmode = 'overlay',
                    title = 'Pure time vs. wait time per link histogram',
                    showlegend = False,
                    xaxis = dict(
                            title = 'Time [s]'),
                    yaxis = dict(
                            title = 'Count'),
                    margin = dict(l = 50, r = 50, t = 80, b = 50))
    
    return Figure(data = [trace1, trace2], layout = layout)

def gen_distplot():
    values1 = [r['pure time'] for r in adcollection_rmetrics.find()]
    values2 = [r['waits'] for r in adcollection_rmetrics.find()]
    
    labels =['pure time', 'wait time']
        
    fig = ff.create_distplot([values1, values2], labels, show_hist = False, colors = ['#92b4f2', '#ffb653'])
    fig['layout']['margin'] = dict(l = 50, r = 50, t = 80, b = 50)
    fig['layout'].update(legend = dict(orientation = 'h'), title = 'Pure time vs. wait time per link distplot')
    
    return fig

def gen_piechart():
    labels = ['pure time', 'wait time']
    values = [np.sum([r['pure time'] for r in adcollection_rmetrics.find()]), np.sum([r['waits'] for r in adcollection_rmetrics.find()])]
    
    trace = Pie(labels = labels, values = values, marker = dict(colors = ['#92b4f2', '#ffb653']))
    
    layout = dict(
            showlegend = False,
            title = 'Overall wait time vs. pure time',
            margin = dict(l = 50, r = 50, t = 80, b = 50)
            
    )
    
    return Figure(data = [trace], layout = layout)

if __name__ == '__main__':
    app.run_server(debug = True)