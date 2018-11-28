# -*- coding: utf-8 -*-
"""
Created on Thu Aug 16 09:25:07 2018

@author: j.klen
"""

import pymongo

from myscraper import scrape_useragents, scrape_proxies, scrape_topreality_links, TopRealityAd
from proxypool import proxy_pool_test, proxyPool

myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection = scrapedb['ads']
adcollection_rmetrics = scrapedb['rmetrics']
adcollection_poolmetrics = scrapedb['poolmetrics']
adcollection_proxies = scrapedb['proxies']

# explore/exploit proxies

#   do not sample worst proxies
#   change epsilon-greedy, weighted exploration
#   thompson sampling
#   adapt wait() to proxies speed
#   why some responses have higher time than specified timeout???

#   streaming plots, some dashboard
#       histogram of all proxies response times within all bandits
#       bar chart 
#       mean change of proxies position within pool, overall, in some intervals
#       ratio successful request nr./all requests nr, overall, in some intervals
#       number of successful, unsuccesfull, total requests overall
#       number of links and pictures successfuly scraped
#       % of not usable proxies
#       proxy performance on map by countries, webs

#   minimum example af axes reset bug
#   initial state of inputbox and buttons bug
#   preserving state of custom chart buttons, zoom when interval present

#   nr. of links scraped, also %
#   nr. of deleted (not scraped) links
#   nr. of pictures scraped (saved) if any
#   map of which property triggers which callbacks
#   when I change a property with one callback will it trigger another?
#   limit amount of data and put it to hidden div, only few charts will query all data

#   proxies
#       1. bandits overall boxplots, 2. click on bandit -> all his proxies boxplots (custom button 'overall'/'window')
#       3. click on proxy boxplot -> line plot with proxy times (date/number x axis) 4. data for proxy including its
#           attributes in table below
#       proxy map (need to get also country, type- elite, transparent, ..., declared speed of proxy, server from which it was scraped)

#   one column with prompts:
#       data filter (calculations are from whole data), for example last 200 values
#       chart type for selected charts (line chart, boxplots)

#   link to rmetrics collection

if __name__ == '__main__':
    
    browser_list = scrape_useragents()
    proxy_list = scrape_proxies()
    proxy_pool = proxyPool(proxy_list, 10, 0.4, adcollection_proxies)
    #pp = proxy_pool_test(proxy_pool, browser_list, 10)
    links = scrape_topreality_links(region = 'bratislavsky kraj', pages_to_scrape = 5)
    for i, link in enumerate(links):
        print('Scraping link %d of %d' %(i, len(links)))
        ad = TopRealityAd(link, proxy_pool, browser_list)
        ad.scrape_all(savepics = True)
        proxy_pool = ad.proxy_pool
        proxy_pool.writetodb_poolmetrics(adcollection_poolmetrics, sum(ad.attempts))
        proxy_pool.writetodb_proxies(adcollection_proxies)
        ad.writetodb(adcollection)
        ad.writetodb_rmetrics(adcollection_rmetrics)