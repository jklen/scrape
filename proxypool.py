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
    """
    Function to test proxy pool class on httpbin.org. Used for testing if proxy pool updates its attributes correctly.
    
    Parameters
    ----------
    proxy_pool : class proxyPool
        Proxy pool to test.
    browser_list : list(str)
        List of browser user agents to send as headers in each request.
    requests_nr : int
        Number of requests to send. (default 100).
    
    Returns
    -------
    proxyPool
        Returns same proxy pool as in input of this function, but with updated attributes.
    """
    
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
    """
    A class representing pool of proxies.
    
    Attributes
    ----------
    proxies_in_bandit : int
        Number of proxies each bin (bandit) of the proxy pool should have.
    proxy_for_bandits : list(list(str))
        List of lists of proxies, which are assigned to each bandit.
    all_proxies : dict
        Dictonary of all proxies and all their metrics each time proxy pool was updated.
    bandits : list(int)
        List of integers, corresponding to ids of each bandit.
    eps : float
        Threshold used in the epsilon-greedy explore-exploit algorithm, when choosing the bandit and proxy.
    bandit_means : list(list(float))
        List of lists, which contain averages of proxies means of each bandit, each time the proxy pool is updated.
    bandit_mins : list(list(float))
        List of lists, which contain minimum values of proxies means of each bandit, each time the proxy pool is updated.
    bandit_q1s : list(list(float))
        List of lists, which contain values of 1st quartile of proxies means of each bandit, each time the proxy pool is updated.
    bandit_medians : list(list(float))
        List of lists, which contain median values of proxies means of each bandit, each time the proxy pool is updated.
    bandit_q3s : list(list(float))
        List of lists, which contain values of 3rd quartile of proxies means of each bandit, each time the proxy pool is updated.
    bandit_maxs : list(list(float))
        List of lists, which contain maximum values of proxies means of each bandit, each time the proxy pool is updated.
    update_times : list(datetime)
        List of timestamps when the proxy pool is updated.
    bandits_chosennr : list(int)
        List of bandit id's, which were chosen each time when choose_proxy method is called.
    chosed_proxies : list(str)
        List of proxies, which were chosen each time when choose_proxy method is called.
    ordered_proxies : list(str)
        List of sorted proxies according their response times mean in given window. Contains only proxy pool's current (not historical) values.        
    """
    
    def __init__(self, proxy_list, proxies_in_bandit, eps):
        """
        Parameters
        ----------
        proxy_list : list(str)
            List of proxies from which the proxy pool is created
        proxies_in_bandit : int
            Number of proxies each bandit should contain. For example if proxy_list is 100, proxies_in_bandit is 10, the proxy pool
            will contain 10 bandits with 10 proxies.
        eps : float
            Threshold which is used in the epsilon-greedy explore-exploit algorithm to choose bandit. (should have values between 0 an 1)
        """
        self.proxies_in_bandit = proxies_in_bandit # nr of proxies in bandit
        self.proxy_for_bandits = [proxy_list[i:i + proxies_in_bandit] for i in range(0, len(proxy_list), proxies_in_bandit)]
        self.nr_of_bandits = len(self.proxy_for_bandits)
        self.all_proxies = {proxy:{'response_times':[], 'response_timestamp':[],'mean':15.0, 'position':[i], 'position_change':[], 'bandit':[j for j, lst in enumerate(self.proxy_for_bandits) if proxy in lst]} for i, proxy in enumerate(proxy_list)}
        #self.bandits = {bandit:15 for bandit in range(self.nr_of_bandits)}
        self.bandits = [i for i in range(self.nr_of_bandits)]
        self.eps = eps
        
        self.bandit_means = []
        self.bandit_mins = []
        self.bandit_q1s = []
        self.bandit_medians = []
        self.bandit_q3s = []
        self.bandit_maxs = []
        
        self.update_times = []
        self.bandits_chosennr = []
        self.chosed_proxies = []
                
    def choose_proxy(self):
        """
        This method uses epsilon-greedy explore-exploit algorithm to choose a bandit and randomly one of it's proxies.
        If a randomly generated number (between 0 and 1) is greater than eps, best performing bandit is chosen, if not,
        randomly chosen bandit selected.
        
        Returns
        -------
        str
            Returns a proxy.
        
        """
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
        """
        Updates attributes of the proxy pool and its metrics.
        
        Parameters
        ----------
        proxy : str
            Proxy which was used to send request.
        response_time : float
            Response time of the proxy which was used to send request
        window : int
            Window from which is the mean of proxies calculated, since proxies can change performance over time.
            For example if set 10, last 10 values will be used for proxy mean calculation. This affects the oredering
            of proxies in the pool and corresponding bandit assignment.
        """
        print('Response time %d' % response_time)
        self.chosed_proxies.append(proxy)
        t = datetime.datetime.now()
        self.update_times.append(t)
        # sorting and assigning proxies
        self.all_proxies[proxy]['response_times'].append(response_time)
        self.all_proxies[proxy]['response_timestamp'].append(t)
        #self.all_proxies[proxy]['bandit'].append(self.bandits_chosennr[-1])
        self.all_proxies[proxy]['mean'] = np.mean(self.all_proxies[proxy]['response_times'][-window:]) # rolling window of proxies response times
        self.ordered_proxies = sorted(self.all_proxies, key = lambda k:self.all_proxies[k]['mean'])
        self.proxy_for_bandits = [self.ordered_proxies[i:i + self.proxies_in_bandit] for i in range(0, len(self.ordered_proxies), self.proxies_in_bandit)]
        # calculate new proxies bandits mean from self.all_proxies and tracking bandit        
        bandit_means = []
        bandit_mins = []
        bandit_q1s = []
        bandit_medians = []
        bandit_q3s = []
        bandit_maxs = []
        
        for bproxylist in self.proxy_for_bandits:
            prmeans_list = []
            for proxy in bproxylist:
                prmeans_list.append(self.all_proxies[proxy]['mean'])
            bandit_means.append(np.mean([i for i in prmeans_list if i != None]))
            bandit_mins.append(np.min([i for i in prmeans_list if i != None]))
            bandit_q1s.append(np.quantile([i for i in prmeans_list if i != None], 0.25))
            bandit_medians.append(np.median([i for i in prmeans_list if i != None]))
            bandit_q3s.append(np.quantile([i for i in prmeans_list if i != None], 0.75))
            bandit_maxs.append(np.max([i for i in prmeans_list if i != None]))
            
        self.bandit_means.append(bandit_means)
        self.bandit_mins.append(bandit_mins)
        self.bandit_q1s.append(bandit_q1s)
        self.bandit_medians.append(bandit_medians)
        self.bandit_q3s.append(bandit_q3s)
        self.bandit_maxs.append(bandit_maxs)
        print(('bandits means', bandit_means))
        # proxies position and position difference from previous request after sorting, and bandit
        for i, proxy in enumerate(self.ordered_proxies):
            self.all_proxies[proxy]['position'].append(i)
            self.all_proxies[proxy]['bandit'].append([j for j, lst in enumerate(self.proxy_for_bandits) if proxy in lst][0])
            if len(self.all_proxies[proxy]['position']) >= 2:
                d = i - self.all_proxies[proxy]['position'][-2]
                self.all_proxies[proxy]['position_change'].append(d)
                
    def writetodb_poolmetrics(self, dbcollection, nr_of_updates): # bude sum(ad.attempts)
        """
        Writes to mongodb collection all necessary proxy pool's metrics
        
        Parameters
        ----------
        dbcollection : mongodb collection
            Collection where the data should be saved.
        nr_of_updates : int
            To the collection will be saved last nr_of_updates of proxy pool's updates.
        """
        #   {'timestamp' self.update_times[-nr_of_updates], 'bandit_means': self.bandit_means[-nr_of_updates], '}
        ppos_change = [[self.all_proxies[p]['position_change'][-nr_of_updates:][i] for p in self.all_proxies.keys()] for i in range(0, len(self.all_proxies[list(self.all_proxies.keys())[0]]['position_change'][-nr_of_updates:]))]
        ppos_change_df = pd.DataFrame(ppos_change)
        position_change = (ppos_change_df.apply(lambda x: len(x[x == 0]), axis = 1)/ppos_change_df.shape[1]).tolist()

        try:
            #to_write = [{'timestamp_pool_update':self.update_times[i], 'bandit_means':self.bandit_means[i], 'choosen_bandit':self.bandits_chosennr[i], 'position_change':position_change[i]} for i in range(-nr_of_updates, 0)]
            to_write = [{'timestamp_pool_update':self.update_times[i], 'bandit_means':self.bandit_means[i], 'bandit_mins':self.bandit_mins[i], 'bandit_q1s':self.bandit_q1s[i], 'bandit_medians':self.bandit_medians[i], 'bandit_q3s':self.bandit_q3s[i], 'bandit_maxs':self.bandit_maxs[i], 'choosen_bandit':self.bandits_chosennr[i], 'position_change':position_change[i]} for i in range(-nr_of_updates, 0)]
            x = dbcollection.insert_many(to_write)
        except Exception as e:
            print('Not able to write bandits metrics to db. ' + str(e))
        else:
            pass
            
            
    def writetodb_proxies(self, dbcollection):
        """
        Writes to mongodb collection info about proxies in the pool.
        
        Parameters
        ----------
        dbcollection : mongodb collection
            
        """
        
        if dbcollection.count_documents({}) > 0:
            dbcollection.delete_many({})
        
        all_proxies_todb = [self.all_proxies[proxy] for proxy in list(self.all_proxies.keys())]
        
        for i in range(0, len(self.all_proxies)):
            all_proxies_todb[i]['_id'] = list(self.all_proxies.keys())[i]
        x = dbcollection.insert_many(all_proxies_todb)
