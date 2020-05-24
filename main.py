# -*- coding: utf-8 -*-
"""
Created on Thu Aug 16 09:25:07 2018

@author: j.klen
"""

import pymongo

from myscraper import scrape_useragents, scrape_proxies, scrape_topreality_links, TopRealityAd
from proxypool import proxy_pool_test, proxyPool
import pickle
import json

myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection = scrapedb['ads']
adcollection_rmetrics = scrapedb['rmetrics']
adcollection_poolmetrics = scrapedb['poolmetrics']
adcollection_proxies = scrapedb['proxies']

with open('browser_list.data', 'rb') as f:
    browser_list = pickle.load(f)
	
#proxy_list = scrape_proxies()
#proxy_pool = proxyPool(proxy_list, 10, 0.3)
with open('rotating_proxy.json', 'r') as f:
	proxy_pool = json.load(f)['rotating_proxy'] # proxy_pool as str with just one rotating proxy
#pp = proxy_pool_test(proxy_pool, browser_list, 10)
links_all = scrape_topreality_links(region = 'bratislava / bratislava', pages_to_scrape = 100) # is already shuffled

scrape_share = 0.5 # scrape % links
links = links_all[:int(scrape_share * len(links_all))]

for i, link in enumerate(links):
    print('Scraping link %d of %d' %(i, len(links)))
    ad = TopRealityAd(link, proxy_pool, browser_list)
    ad.scrape_all(savepics = False)
    if type(proxy_pool) == proxyPool:
		   proxy_pool = ad.proxy_pool
		   proxy_pool.writetodb_poolmetrics(adcollection_poolmetrics, sum(ad.attempts))
		   proxy_pool.writetodb_proxies(adcollection_proxies)
    ad.writetodb(adcollection)
    ad.writetodb_rmetrics(adcollection_rmetrics)