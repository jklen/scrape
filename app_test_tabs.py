import dash
import dash_html_components as html
import dash_core_components as dcc
from plotly.graph_objs import Bar, Figure, Scatter
import pandas as pd
import datetime

from dash.dependencies import Input, Output, State, Event

app = dash.Dash()

app.layout = html.Div([
    dcc.Tabs(id="tabs", children=[
        dcc.Tab(label='Tab one', children=[
            html.Div([html.Div(id = 'tab1_content'), 
                    dcc.Interval(
                            id = 'tab1_interval',
                            interval = 2000,
                            n_intervals = 0)])
        ]),
        dcc.Tab(label='Tab two', children=[
            html.Div([
                dcc.Slider(
                        id = 'slider_tab2',
                        min = 2,
                        max = 10,
                        value = 5,
                        step = 1)]),
            html.Div([
                    html.Div(id = 'tab2_content'),
                    dcc.Interval(
                            id = 'tab2_interval',
                            interval = 2000,
                            n_intervals = 0)
            ])
        ]),
        dcc.Tab(label='Tab three', children=[
            dcc.RadioItems(id = 'xaxis',
                            options = [{'label': 'Number', 'value':'nr'},
                                              {'label': 'Date', 'value':'date'}
                                              ],
                            value = 'date',
                            labelStyle = {'display':'inline-block'}),
            html.Div(id = 'tab3_content')
        ]),
    ])
])
            
@app.callback(Output('tab3_content', 'children'),
              [Input('tabs', 'value'),
               Input('xaxis', 'value')])
def gen_ch3(tab, xtype):
    if xtype == 'nr':
        x = [i for i in range(0,100)]
        y = [i for i in range(0,100)]
        x_range = [x[0], x[-1]]
    elif xtype == 'date':
        x = pd.date_range(pd.datetime.today(), periods = 100).tolist()
        x = [i.to_pydatetime() for i in x]
        y = [i for i in range(0,100)]
        x_range = [x[-1] - datetime.timedelta(days = 10), x[-1]]
    
    trace = Scatter(x = x,
                    y = y)
    layout = dict(xaxis = dict(range = x_range))
    
    to_return = html.Div([
            dcc.Graph(id = 'graph_tab3', figure = Figure(data = [trace], layout = layout))])
    
    return to_return

@app.callback(Output('tab1_content', 'children'), [Input('tabs', 'value'), Input('tab1_interval', 'n_intervals')])
def gen_tab1(tab, interval):
    to_return = html.Div([
                    html.H1('h1 tag ' + str(interval)),
                    dcc.Graph(id = 'graph_tab1', figure = Figure(data = [Bar(x = ['cat1', 'cat2', 'cat3'],
                                                              y = [1,2,interval])]))       
    ])
    return to_return

@app.callback(Output('tab2_content', 'children'), [Input('tabs', 'value'), Input('slider_tab2', 'value'), Input('tab2_interval', 'n_intervals')])
def gen_tab2(tab, slider, interval):
    to_return = html.Div([
                    html.H1('Slider value: ' + str(slider)),
                    html.H1('Interval tab2: ' + str(interval)),
                    dcc.Graph(id = 'graph_tab1', figure = Figure(data = [Bar(x = ['cat1', 'cat2', 'cat3'],
                                                              y = [slider,interval,1])]))       
    ])
    return to_return
'''
@app.callback(Output('tab3_content', 'children'), [Input('tabs', 'value')])
def gen_tab3(tab):
    to_return = html.Div([
                    dcc.Graph(id = 'graph_tab1', figure = Figure(data = [Bar(x = ['cat1', 'cat2', 'cat3'],
                                                              y = [3,3,3])]))       
    ])
    return to_return
'''
if __name__ == '__main__':
    app.run_server(debug=True)