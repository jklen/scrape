# -*- coding: utf-8 -*-
"""
Created on Thu Aug 16 09:25:07 2018

@author: j.klen
"""

import os
import pymongo
from myscraper import scrape_useragents, scrape_proxies, scrape_topreality_links, TopRealityAd
from proxypool import proxy_pool_test, proxyPool

working_dir = 'C:\\Users\\j.klen\\PythonProjects\\scrape' # read from file
os.chdir(working_dir)

myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection = scrapedb['ads']

# explore/exploit proxies

#   do not sample worst proxies
#   change epsilon-greedy, weighted exploration
#   thompson sampling
#   measure proxies position channge, around 40% of proxies are not usable, so when change is minimal, explore these minimal
#   adapt wait() to proxies speed
#   why some responses have higher time than specified timeout???

#   track successful request time, number of attempts
#   streaming plots, some dashboard
#       histogram of all proxies response times within all bandits
#       line chart with bandit means
#       bar chart how many times each bandit was chosen
#       mean change of proxies position within pool, overall, in some intervals
#       ratio successful request nr./all requests nr, overall, in some intervals
#       number of successful, unsuccesfull, total requests overall
#       mean successful response time overall, in some intervals
#       


if __name__ == '__main__':
    
    browser_list = scrape_useragents()
    proxy_list = scrape_proxies()
    proxy_pool = proxyPool(proxy_list, 10, 0.4)
    #pp = proxy_pool_test(proxy_pool, browser_list, 10)
    links = scrape_topreality_links(region = 'bratislavsky kraj', pages_to_scrape = 3)
    for link in links:
        ad = TopRealityAd(link, proxy_pool, browser_list)
        ad.scrape_all()
        proxy_pool = ad.proxy_pool
        ad.writetodb(adcollection)