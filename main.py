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

#   change Store to query only new data https://dash.plot.ly/dash-core-components/store
#   not redraw chart but append only new data from store https://community.plot.ly/t/extend-or-append-data-instead-of-update/8898

#   link to rmetrics collection

if __name__ == '__main__':
    
    browser_list = scrape_useragents()
    proxy_list = scrape_proxies()
    proxy_pool = proxyPool(proxy_list, 10, 0.4)
    #pp = proxy_pool_test(proxy_pool, browser_list, 10)
    links = scrape_topreality_links(region = 'trenciansky kraj', pages_to_scrape = 40)
    for i, link in enumerate(links):
        print('Scraping link %d of %d' %(i, len(links)))
        ad = TopRealityAd(link, proxy_pool, browser_list)
        ad.scrape_all(savepics = False)
        proxy_pool = ad.proxy_pool
        proxy_pool.writetodb_poolmetrics(adcollection_poolmetrics, sum(ad.attempts))
        proxy_pool.writetodb_proxies(adcollection_proxies)
        ad.writetodb(adcollection)
        ad.writetodb_rmetrics(adcollection_rmetrics)