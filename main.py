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

#   minimum example af axes reset bug
#   initial state of inputbox and buttons bug
#   clickData, relayoutData with boxplot only possible when another scatter is present on page/tab
#       click callback from boxplot does not fire when previous tab was Pool or Links time window,
#       when reclicking to first tab and back to Proxies tab, it works
#       similar behaviour with relayed data on Links time window tab, first chart

#   change Store to query only new data https://dash.plot.ly/dash-core-components/store
#   not redraw chart but append only new data from store https://community.plot.ly/t/extend-or-append-data-instead-of-update/8898

#   one column with prompts:
#       data filter (calculations are from whole data), for example last 200 values

#   proxies - option to see stats for last n values or whole

#   link to rmetrics collection

'''
time_start = time.time()
last5 = list(adcollection.find().sort('$natural',-1).limit(5))
last5.reverse()
whole.extend(last5)
time_end = time.time()
last5_time = time_end - time_start
print('last5', last5_time)

time_start = time.time()
whole = list(adcollection.find())
time_end = time.time()
whole_time = time_end - time_start
print('whole', whole_time)
print('whole/last5', whole_time/last5_time)
'''

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