# -*- coding: utf-8 -*-
"""
Created on Mon Dec 31 19:49:10 2018

@author: Dell
"""

# scrape proxies
#   country prompt - multiselect dropdown
#   add wait times - checkbox with inputs for min, max, mean, std
#   check if proxy list is present in DB, with timestamp when scraped
# scrape user agents
#   type prompt - multiselect dropdown
#   add wait times
#   check if agents are already present in db
# scrape top reality ads
#   only flats
#   prompts:
#       region/city/area - multiselect dropdown
#       number of pages to scrape
#       savepics
#       number of proxies in bandit
#       threshold for proxy pool
#       proxy mean calculation window
#       add wait times

# preloaders https://icons8.com/preloaders/en/search/circle
# html progressbar https://www.w3schools.com/tags/tryit.asp?filename=tryhtml5_progress
# console output to dash https://stackoverflow.com/questions/52057540/redirecting-pythons-console-output-to-dash


import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, Event, State
from dash.exceptions import PreventUpdate
import time
import pymongo

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import re

import scipy.stats
import base64


myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection = scrapedb['ads']
adcollection_scraped_proxies = scrapedb['scraped_proxies']
adcollection_scraped_agents = scrapedb['scraped_agents']

app = dash.Dash(__name__)
app.css.append_css({'external_url':'https://codepen.io/amyoshino/pen/jzXypZ.css'})

proxy_countries = {'Slovakia':{'free-proxy':'SK', 'gatherproxy':'Slovak%20Republic'},
                   'Hungary':{'free-proxy':'HU', 'gatherproxy':'Hungary'},
                   'Czech Republic':{'free-proxy':'CZ', 'gatherproxy':'Czech%20Republic'}}

'''
def lay():
    return html.Div([
            html.Button(id = 'button_proxies', children = 'Scrape proxies'),
            html.Img(id = 'preloader', src = app.get_asset_url('42.gif')),
            html.Img(id = 'preloader2', src = app.get_asset_url('39.gif')),
            html.Progress(id = 'progress', value = '40', max = '100', style = {'height':'5px', 'width':'150px'}), # nr. of links will be known, compare to what is in the DB and check for new ones
            html.P(id = 'p')])
'''
def lay():
    return html.Div([
                html.Div([
                        html.Div([
                                html.H2('Proxies', style = {'text-align':'center'})
                        ], className = 'row'),
                        html.Div([
                                dcc.Dropdown(options = [{'label':country, 'value':country} for country in proxy_countries],
                                             multi = True, value = ['Slovakia', 'Hungary'])
                        ], className = 'row'),
                        html.Div([
                                html.P('Wait times:', style = {'font-weight':'bold', 'display':'inline-block', 'margin-right':'10px'}),
                                html.P('Min', style = {'display':'inline-block', 'margin-right':'10px'}),
                                dcc.Input(id = 'wait_min', type = 'number', value = 0.5, step = 0.1, style = {'display':'inline-block', 'width':80, 'margin-right':'10px'}),
                                html.P('Avg', style = {'display':'inline-block', 'margin-right':'10px'}),
                                dcc.Input(id = 'wait_avg', type = 'number', value = 2.5, step = 0.1, style = {'display':'inline-block', 'width':80, 'margin-right':'10px'}),
                                html.P('Std', style = {'display':'inline-block', 'margin-right':'10px'}),
                                dcc.Input(id = 'wait_std', type = 'number', value = 2.7, step = 0.1, style = {'display':'inline-block', 'width':80, 'margin-right':'10px'}),
                                html.P('Max', style = {'display':'inline-block', 'margin-right':'10px'}),
                                dcc.Input(id = 'wait_max', type = 'number', value = 20, step = 0.1, style = {'display':'inline-block', 'width':80})
                        ], className = 'row', style = {'margin-top':'15px'}),
                        html.Div([
                            html.Div(id = 'proxies_last_scraped_div', children = [
                                    html.P('Last scraped: 2.1.2019 22:00:15'),
                                    html.Div([
                                            html.Img(id = 'preloader', src = app.get_asset_url('42.gif'), style = {'margin-top':'50px', 'margin-bottom':'20px'})
                                    ]),
                                    html.Button(children = 'Run', id = 'proxy_button', style = {'margin-top':'20px', 'margin-bottom':'20px'}),

                                    
                            ], className = 'six columns'),
                            html.Div([
                                    html.Pre('Info output', style = {'border': 'thin lightgrey solid', 'overflowX': 'scroll'})
                            ], className = 'six columns')
                        ], className = 'row', style = {'margin-top':'25px'})
                ], className = 'four columns'),
                html.Div([
                        html.Div([
                                html.H2('User agents', style = {'text-align':'center'})
                        ], className = 'row')
                ], className = 'four columns'),
                html.Div([
                        html.Div([
                                html.H2('Ads', style = {'text-align':'center'})
                        ], className = 'row')
                ], className = 'four columns'),
    ])

app.layout = lay()

if __name__ == '__main__':
    app.run_server(debug = True)