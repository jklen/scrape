# -*- coding: utf-8 -*-
"""
Created on Mon Sep 10 13:07:37 2018

@author: j.klen
"""

import random
import requests
import numpy as np
from myscraper import wait
import datetime
import pandas as pd
from bson.objectid import ObjectId

def proxy_pool_test(proxy_pool, browser_list, requests_nr = 100):
    url = 'https://httpbin.org/ip'
    proxy_pool = proxy_pool
    for i in range(requests_nr):
        print('Request nr. %d' % i)
        wait()
        proxy = proxy_pool.choose_proxy()
        user_agent = random.choice(browser_list)
        try:
            response = requests.get(url, proxies = {'http':proxy, 'https':proxy}, headers = {'User-Agent': user_agent}, timeout = 30)
        except:
            proxy_pool.update(proxy, 30)
        else:
            proxy_pool.update(proxy, response.elapsed.total_seconds())
    return proxy_pool

class proxyPool:
    def __init__(self, proxy_list, proxies_in_bandit, eps, dbcollection_proxies):
        self.proxies_in_bandit = proxies_in_bandit # nr of proxies in bandit
        self.proxy_for_bandits = [proxy_list[i:i + proxies_in_bandit] for i in range(0, len(proxy_list), proxies_in_bandit)]
        self.nr_of_bandits = len(self.proxy_for_bandits)
        self.all_proxies = {proxy:{'response_times':[], 'response_timestamp':[],'mean':15.0, 'position':[i], 'position_change':[], 'bandit':[j for j, lst in enumerate(self.proxy_for_bandits) if proxy in lst]} for i, proxy in enumerate(proxy_list)}
        #self.bandits = {bandit:15 for bandit in range(self.nr_of_bandits)}
        self.bandits = [i for i in range(self.nr_of_bandits)]
        self.eps = eps
        self.bandit_means = []
        self.update_times = []
        self.bandits_chosennr = []
        self.chosed_proxies = []
        
        # initial all proxies info to db
        all_proxies_initial = [self.all_proxies[proxy] for proxy in list(self.all_proxies.keys())]
        for i in range(0, len(self.all_proxies)):
            all_proxies_initial[i]['_id'] = list(self.all_proxies.keys())[i]
        x = dbcollection_proxies.insert_many(all_proxies_initial)
        
    def choose_proxy(self):
        p = random.random()
        if p < self.eps:
            #bandit = random.choice([i for i in self.bandits][1:]) # except the fastest bandit
            bandit = random.choice(self.bandits[1:])
        else:
            bandit = 0
        proxy = random.choice(self.proxy_for_bandits[bandit])
        print('Choosen bandit: %d and proxy: %s, chosen times %d and rolling mean %d' % (bandit, proxy, len(self.all_proxies[proxy]['response_times']), self.all_proxies[proxy]['mean']))
        self.bandits_chosennr.append(bandit)
        
        return proxy
        
        
    def update(self, proxy, response_time, window = 10):
        print('Response time %d' % response_time)
        self.chosed_proxies.append(proxy)
        t = datetime.datetime.now()
        self.update_times.append(t)
        # sorting and assigning proxies
        self.all_proxies[proxy]['response_times'].append(response_time)
        self.all_proxies[proxy]['response_timestamp'].append(t)
        self.all_proxies[proxy]['bandit'].append(self.bandits_chosennr[-1])
        self.all_proxies[proxy]['mean'] = np.mean(self.all_proxies[proxy]['response_times'][-window:]) # rolling window of proxies response times
        self.ordered_proxies = sorted(self.all_proxies, key = lambda k:self.all_proxies[k]['mean'])
        self.proxy_for_bandits = [self.ordered_proxies[i:i + self.proxies_in_bandit] for i in range(0, len(self.ordered_proxies), self.proxies_in_bandit)]
        # calculate new proxies bandits mean from self.all_proxies and tracking bandit        
        bandit_means = []
        for bproxylist in self.proxy_for_bandits:
            prmeans_list = []
            for proxy in bproxylist:
                prmeans_list.append(self.all_proxies[proxy]['mean'])
            bandit_means.append(np.mean([i for i in prmeans_list if i != None]))
        self.bandit_means.append(bandit_means)
        print(('bandits means', bandit_means))
        # proxies position and position difference from previous request after sorting
        for i, proxy in enumerate(self.ordered_proxies):
            self.all_proxies[proxy]['position'].append(i)
            if len(self.all_proxies[proxy]['position']) >= 2:
                d = i - self.all_proxies[proxy]['position'][-2]
                self.all_proxies[proxy]['position_change'].append(d)
                
    def writetodb_poolmetrics(self, dbcollection, nr_of_updates): # bude sum(ad.attempts)
        #   {'timestamp' self.update_times[-nr_of_updates], 'bandit_means': self.bandit_means[-nr_of_updates], '}
        ppos_change = [[self.all_proxies[p]['position_change'][-nr_of_updates:][i] for p in self.all_proxies.keys()] for i in range(0, len(self.all_proxies[list(self.all_proxies.keys())[0]]['position_change'][-nr_of_updates:]))]
        ppos_change_df = pd.DataFrame(ppos_change)
        position_change = (ppos_change_df.apply(lambda x: len(x[x == 0]), axis = 1)/ppos_change_df.shape[1]).tolist()

        try:
            to_write = [{'timestamp_pool_update':self.update_times[i], 'bandit_means':self.bandit_means[i], 'choosen_bandit':self.bandits_chosennr[i], 'position_change':position_change[i]} for i in range(-nr_of_updates, 0)]
        except Exception as e:
            print('Not able to create list to write bandits metrics to db. ' + str(e))
        else:
            x = dbcollection.insert_many(to_write)
            
    def writetodb_proxies(self, dbcollection, nr_of_updates):
        proxies = self.chosed_proxies[-nr_of_updates:]
        for proxy in proxies:
            print(proxy)
            dbcollection.update_one({'_id':proxy}, {'$push':{'position':self.all_proxies[proxy]['position'][-1]}})
            dbcollection.update_one({'_id':proxy}, {'$push':{'position_change':self.all_proxies[proxy]['position_change'][-1]}})
            dbcollection.update_one({'_id':proxy}, {'$push':{'response_times':self.all_proxies[proxy]['response_times'][-1]}})
            dbcollection.update_one({'_id':proxy}, {'$push':{'response_timestamp':self.all_proxies[proxy]['response_timestamp'][-1]}})
            dbcollection.update_one({'_id':proxy}, {'$push':{'bandit':self.all_proxies[proxy]['bandit'][-1]}})
            dbcollection.update_one({'_id':proxy}, {'$set':{'mean':self.all_proxies[proxy]['mean']}})
    
#   proxy:
#       mean . .
#       position [x] .
#       position change [] .
#       update_timestamp - NO, can be taken from timestamp_pool_update in poolmetrics
#       response times[] .
#       response_timestamp [] .
#       current bandit [x]
#       country
#       scraped from
            
#   adcollection_poolmetrics.update_one({'_id':ObjectId('5bdb3b8a430724117cbff243')},{'$push':{'bandit_means':6}})
#   access/update array in nested dictionary
