# -*- coding: utf-8 -*-
"""
Created on Mon Sep 10 13:07:37 2018

@author: j.klen
"""

import random
import requests
import numpy as np
from myscraper import wait

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
    def __init__(self, proxy_list, proxies_in_bandit, eps):
        self.proxies_in_bandit = proxies_in_bandit # nr of proxies in bandit
        self.proxy_for_bandits = [proxy_list[i:i + proxies_in_bandit] for i in range(0, len(proxy_list), proxies_in_bandit)]
        self.nr_of_bandits = len(self.proxy_for_bandits)
        self.all_proxies = {proxy:{'response_times':[], 'mean':15.0, 'position':[i], 'position_change':[]} for i, proxy in enumerate(proxy_list)}
        self.bandits = {bandit:15 for bandit in range(self.nr_of_bandits)}
        self.eps = eps
        self.bandit_means = []
        
    def choose_proxy(self):
        p = random.random()
        if p < self.eps:
            bandit = random.choice([i for i in self.bandits][1:]) # except the fastest bandit
        else:
            bandit = 0
        proxy = random.choice(self.proxy_for_bandits[bandit])
        print('Choosen bandit: %d and proxy: %s, chosen times %d and rolling mean %d' % (bandit, proxy, len(self.all_proxies[proxy]['response_times']), self.all_proxies[proxy]['mean']))
        
        return proxy
        
        
    def update(self, proxy, response_time, window = 10):
        print('Response time %d' % response_time)
        # sorting and assigning proxies
        self.all_proxies[proxy]['response_times'].append(response_time)
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