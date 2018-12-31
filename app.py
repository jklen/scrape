
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
import time


myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection_rmetrics = scrapedb['rmetrics']
adcollection_poolmetrics = scrapedb['poolmetrics']
adcollection_proxies = scrapedb['proxies']

app = dash.Dash(__name__)
app.css.append_css({'external_url':'https://codepen.io/amyoshino/pen/jzXypZ.css'})
app.config['suppress_callback_exceptions'] = True

styles = {
    'tab':{'backgroundColor':'#fdfdfd',
           'padding':'10px'},
    'selected_tab':{'backgroundColor':'#d9eefc',
                    'padding':'10px'}
}

def lay():
    return html.Div([
                html.Div(id = 'prompts', children = [
                        html.Div(id = 'all_tabs_prompts', children = [
                                html.Button(children = 'Stop refresh', id = 'interval_button', style = {'width':'100%', 'margin-top':'4px', 'margin-bottom':'20px'}),
                                html.Div(id = 'times_refreshed', style = {'font-weight':'bold'})
                        ]),
                        html.Div(id = 'tab23_prompts', style = {'display':'none'}, children = [
                                html.P('Moving average', style = {'font-weight':'bold'}),
                                dcc.Input(id = 'ma_input', type = 'number', value = 10, size = 3, step = 5, style = {'margin-bottom':'20px'}),
                                html.P('X axis type', style = {'font-weight':'bold'}),
                                dcc.RadioItems(id = 'xaxis', options = [{'label':'Number', 'value':'nr'},
                                                                        {'label':'Date', 'value':'date'}],
                                                value = 'date',
                                                labelStyle = {'display':'inline-block'}, style = {'margin-bottom':'20px'}),
                                dcc.Checklist(id = 'limit_check', options = [{'label':'Limit visible data', 'value':'limit'}],
                                              values = ['limit']),
                                dcc.Input(id = 'linput', type = 'number', value = 200, step = 50)
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
                ], className = 'one column'),
                html.Div(children = [
                    html.Div([
                            dcc.Tabs(id = 'tabs', value = 'tab1', children = [
                                    dcc.Tab(label = 'Links overall', value = 'tab1', style = styles['tab'], selected_style = styles['selected_tab'], children = [
                                            html.Div(id = 'content1')]),
                                    dcc.Tab(label = 'Links time window', value = 'tab2', style = styles['tab'], selected_style = styles['selected_tab'], children = [
                                            html.Div(id = 'content2')]),
                                    dcc.Tab(label = 'Bandits', value = 'tab3', style = styles['tab'], selected_style = styles['selected_tab'], children = [
                                            html.Div(id = 'content3')]),
                                    dcc.Tab(label = 'Proxies', value = 'tab4', style = styles['tab'], selected_style = styles['selected_tab'], children = [
                                            html.Div(id = 'content4')])
                            ])
                            
                    ]),
                    html.Div([
                            dcc.Interval(id = 'interval', interval = 2000, n_intervals = 0)
                    ])
                ], className = 'eleven columns'),
                html.Div([
                    html.Div(id = 'stored_clicks', style = {'display':'none'}, children = 0)
                ]),
                dcc.Store(id = 'store')
            
            
    ])

app.layout = lay()

@app.callback(Output('store', 'data'),
              [Input('tabs', 'value'),
               Input('interval', 'n_intervals')])
def store_data(tab, interval):
    print('to store', tab, interval, time.time())
    data = {}
    if tab in ['tab1', 'tab2']:
        
        data_first = list(adcollection_rmetrics.find({}, {'_id': False}))
        data['pure time'] = [r['pure time'] for r in data_first]
        data['waits'] = [r['waits'] for r in data_first]
        data['attempts'] = [r['attempts'] for r in data_first]
        data['time success'] = [r['time success'] for r in data_first]
        data['timestamp'] = [r['timestamp'] for r in data_first]
        data['tab'] = tab # even if data is return to store, if it is the same, modified_timestamp property will not be updated
        print('Store update with tab12 data', time.time())
        return data
    elif tab == 'tab3':
        data_first = list(adcollection_poolmetrics.find({}, {'_id': False}))
        data['bandit_means'] = [b['bandit_means'] for b in data_first]
        data['choosen_bandit'] = [b['choosen_bandit'] for b in data_first]
        data['timestamp_pool_update'] = [b['timestamp_pool_update'] for b in data_first]
        data['position_change'] = [b['position_change'] for b in data_first]
        data['tab'] = tab
        print('Store update with tab3 data', time.time())
        return data
    elif tab == 'tab4':
        bandit_data = list(adcollection_poolmetrics.find().limit(1).sort([('$natural',-1)]))[0]
        bandit_data = [[bandit_data['bandit_mins'][i], bandit_data['bandit_q1s'][i], bandit_data['bandit_q1s'][i], bandit_data['bandit_medians'][i], bandit_data['bandit_q3s'][i], bandit_data['bandit_q3s'][i], bandit_data['bandit_maxs'][i]] for i in range(0, len(bandit_data['bandit_means']))]        
        proxies = list(adcollection_proxies.find())
        data['bandit_data'] = bandit_data
        data['proxies'] = proxies
        data['tab'] = tab
        print('Store update with tab4 data', time.time())
        return data

@app.callback(Output('content1', 'children'),
              [Input('store', 'modified_timestamp')],
               [State('store', 'data'),
                State('tabs', 'value')])
def content1_children(ts, data, tab):
    print('content 1 tab', tab)
    if tab == 'tab1':
        return html.Div([
            html.Div([
                html.Div(id = 'tab1_chart1_div', children = [dcc.Graph(id = 'tab1_chart1', figure = tab1_chart1(data))], className = 'six columns'),
                html.Div(id = 'tab1_chart2_div', children = [dcc.Graph(id = 'tab1_chart2', figure = tab1_chart2(data))], className = 'six columns')
            ], className = 'row'),
            html.Div([
                html.Div(id = 'tab1_chart3_div', children = [dcc.Graph(id = 'tab1_chart3', figure = tab1_chart3(data))], className = 'six columns'),
                html.Div(id = 'tab1_chart4_div', children = [dcc.Graph(id = 'tab1_chart4', figure = tab1_chart4(data))], className = 'six columns')
            ], className = 'row')
        ])
        
@app.callback(Output('content2', 'children'),
              [Input('store', 'modified_timestamp'),
               Input('ma_input', 'value'),
               Input('xaxis', 'value'),
               Input('linput', 'value'),
               Input('limit_check', 'values')],
               [State('store', 'data'),
                State('tabs', 'value')])
def content2_children(ts, ma, xtype, linput, lcheck, data, tab):
    print('content 2 tab', tab)
    if tab == 'tab2':
        return html.Div([
                    html.Div([
                        html.Div(id = 'tab2_chart1_div', children = [dcc.Graph(id = 'tab2_chart1', figure = tab2_chart1(ma, xtype, linput, lcheck, data))], className = 'six columns'),
                        html.Div(id = 'tab2_chart2_div', children = [dcc.Graph(id = 'tab2_chart2', figure = tab2_chart2(ma, xtype, linput, lcheck, data))], className = 'six columns')
                        
                    ], className = 'row'),
                    html.Div([
                        html.Div(id = 'tab2_chart3_div', children = [dcc.Graph(id = 'tab2_chart3', figure = tab2_chart3(xtype, linput, lcheck, data))], className = 'six columns'),
                        html.Div(id = 'tab2_chart4_div', children = [dcc.Graph(id = 'tab2_chart4', figure = tab2_chart4(xtype, linput, lcheck, data))], className = 'six columns')
                        
                    ], className = 'row')
                ])

@app.callback(Output('content3', 'children'),
              [Input('store', 'modified_timestamp'),
               Input('ma_input', 'value'),
               Input('xaxis', 'value'),
               Input('linput', 'value'),
               Input('limit_check', 'values')],
               [State('store', 'data'),
                State('tabs', 'value')])
def content3_children(ts, ma, xtype, linput, lcheck, data, tab):
    print('content 3 tab', tab)
    if tab == 'tab3':
        return html.Div([
                    html.Div([
                        html.Div(id = 'tab3_chart1_div', children = [dcc.Graph(id = 'tab3_chart1', figure = tab3_chart1(linput, lcheck, data))], className = 'six columns'),
                        html.Div(id = 'tab3_chart2_div', children = [dcc.Graph(id = 'tab3_chart2', figure = tab3_chart2(data))], className = 'six columns')
                        
                    ], className = 'row'),
                    html.Div([
                        html.Div(id = 'tab3_chart3_div', children = [dcc.Graph(id = 'tab3_chart3', figure = tab3_chart3(ma, xtype, linput, lcheck, data))], className = 'tvelwe columns')
                        
                    ], className = 'row')
                ])

@app.callback(Output('content4', 'children'),
              [Input('store', 'modified_timestamp'),
               Input('proxy_window_input', 'value'),
               Input('proxy_radio', 'value'),
               Input('stored_clicks', 'children')],
               [State('store', 'data'),
                State('tabs', 'value')])
def content4_children(ts, window, pradio, clicked_bandit, data, tab):
    print('content 4 tab', tab)
    if tab == 'tab4':
        return html.Div([
                    html.Div([
                        html.Div(id = 'tab4_chart1_div', children = [dcc.Graph(id = 'tab4_chart1', figure = tab4_chart1(data))], className = 'six columns'),
                        html.Div(id = 'tab4_chart2_div', children = [dcc.Graph(id = 'tab4_chart2', figure = tab4_chart2(clicked_bandit, window, pradio, data))], className = 'six columns')
                        
                    ], className = 'row'),
                    html.Div([
                        html.Div(id = 'tab4_chart3_div', children = [dcc.Graph(id = 'tab4_chart3', figure = tab4_chart3(clicked_bandit, window, pradio, data))], className = 'tvelwe columns')
                        
                    ], className = 'row')
                ])

def tab2_chart1(ma, xtype, linput, lcheck, data):
    print('tab2 chart1')
    if data:        
        x = data['timestamp']
        x = pd.to_datetime(x)
        x_range = [x[-1] - datetime.timedelta(minutes = 30), x[-1]]
        if xtype == 'nr':
            x = [i for i in range(0, len(x) + 1)]
        y = data['time success']
        y_MA = pd.Series(y).rolling(ma).mean()
        
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
    else:
        raise PreventUpdate

def tab2_chart2(ma, xtype, linput, lcheck, data):
    print('tab2 chart2')
    if data:        
        x = data['timestamp']
        x = pd.to_datetime(x)
        x_range = [x[-1] - datetime.timedelta(minutes = 30), x[-1]]
        if xtype == 'nr':
            x = [i for i in range(0, len(x) + 1)]
        y1 = data['pure time']
        y2 = data['waits']
        
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
    else:
        raise PreventUpdate
        
def tab2_chart3(xtype, linput, lcheck, data):
    print('tab2 chart3')
    if data:        
        x = data['timestamp']
        x = pd.to_datetime(x)
        x_range = [x[-1] - datetime.timedelta(minutes = 30), x[-1]]
        if xtype == 'nr':
            x = [i for i in range(0, len(x) + 1)]
            x_range = [x[0], x[-1]]
        y1 = data['attempts']
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
    else:
        raise PreventUpdate
        
def tab2_chart4(xtype, linput, lcheck, data):
    print('tab2 chart4')
    if data:        
        x = data['timestamp']
        x = pd.to_datetime(x)
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
                         mode = 'lines')
                         
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
    else:
        raise PreventUpdate

def tab1_chart1(data):
    print('tab1 chart 1')
    #print('to chart', type(data), ts)
    if data:
            #print('to chart', len(data['timestamp']))
            values = data['time success']
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
    else:
        raise PreventUpdate

def tab1_chart2(data):
    print('tab1 chart 2')
    if data:
        counted_vals = Counter(data['attempts'])
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
    else:
        raise PreventUpdate
        
def tab1_chart3(data):
    print('tab1 chart3')
    if data:        
        values1 = data['pure time']
        values2 = data['waits']
        
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
    else:
        raise PreventUpdate
        
def tab1_chart4(data):
    print('tab1 chart4')
    if data:        
        values1 = data['pure time']
        values2 = data['waits']
        
        labels =['pure time', 'wait time']
        
        fig = ff.create_distplot([values1, values2], labels, show_hist = False, colors = ['#92b4f2', '#ffb653'])
        fig['layout']['margin'] = dict(l = 50, r = 50, t = 80, b = 50)
        fig['layout'].update(legend = dict(orientation = 'h'), title = 'Pure time vs. wait time per link distplot')
        
        return fig
    else:
        raise PreventUpdate
        
def tab3_chart1(linput, lcheck, data):
    print('tab3 chart1')
    if data:        
        meansdf = pd.DataFrame(data['bandit_means'])
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
    else:
        raise PreventUpdate
        
def tab3_chart2(data):
    counted_vals = Counter(data['choosen_bandit'])
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

def tab3_chart3(ma, xtype, linput, lcheck, data):
    if data:
        x = data['timestamp_pool_update']
        x = pd.to_datetime(x)
        x_range = [x[-1] - datetime.timedelta(minutes = 30), x[-1]]
        if xtype == 'nr':
            x = [i for i in range(0, len(x) + 1)]
            x_range = [x[0], x[-1]]
        y1 = data['position_change']
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
    
def tab4_chart1(data):
    print('tab4 chart1')
    if data:
        bandit_data = data['bandit_data']
        data = [Box(y = j, name = 'b' + str(i)) for i, j in enumerate(bandit_data)]
        
        layout= dict(
                title = 'Bandits proxies means',
                xaxis = dict(title = 'Bandit'),
                yaxis = dict(title = 'Proxies means [s]'),
                showlegend = False,
                margin = dict(l = 50, r = 50, t = 80, b = 50))
        
        return Figure(data = data, layout = layout)

def tab4_chart2(clicked_bandit, window, pradio, data):
    print('tab4 chart2')
    if data:
        proxies = data['proxies']
        
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

def tab4_chart3(clicked_bandit, window, pradio, data):
    print('tab4 chart3')
    if data:
        proxies = data['proxies']
        
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

@app.callback(Output('stored_clicks', 'children'),
              [Input('tab4_chart1', 'clickData')])
def stored_clicks_children(click):
    return int(click['points'][0]['x'][1:])

@app.callback(Output('interval', 'interval'),
              [Input('interval_button', 'n_clicks')])
def interval_interval(button):
    if button:
        if button % 2 == 1:
            return 600000
        else:
            return 5000
    else:
        return 5000

@app.callback(Output('interval_button', 'children'),
              [Input('interval', 'interval')])
def interval_button_children(interval):
    if interval:
        if interval == 5000:
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