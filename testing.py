# -*- coding: utf-8 -*-
"""
Created on Fri May  8 11:24:57 2020

@author: User
"""

from pymongo import MongoClient
from bson.objectid import ObjectId
import re
import datetime

client = MongoClient('localhost', 27017)
scrape_db = client.scrapedb
ads = scrape_db.ads

ad1 = ads.find_one({'_id':ObjectId('5eaee00e0895b401c5203aca')})
ad1_properties = ad1['properties']

# unique keys in the properties
properties_all = list(ads.find({}, {'properties':1, '_id':0}))
unique_keys = list()
for p in properties_all:
	unique_keys.extend(p['properties'].keys())
unique_keys = set(unique_keys)

# unique values for each of the keys (properties)
unique_properties_vals = {}
for p in unique_keys:
	unique_properties_vals[p] = list(set([ad['properties'][p] for ad in properties_all if p in ad['properties'].keys()]))

# aktualizacia - convert to datetime
t = unique_properties_vals['Aktualizácia'][0]
tt = datetime.datetime.strptime(t, '%d.%m.%Y %H:%M:%S')

# cena/cena bez provizie/cena vratane provizie - convert string with EUR to numeric
t = unique_properties_vals['Cena'][0] # 'Cena' can be ' cena dohodou
r = re.search('([^€]{1,8}) (€)', t)
tt = r.group(1)
tt = int(tt.replace(' ', ''))

# hypoteka - dorobit nech scrapeuje span s id= 'moneytooMonthlyPayment'  text

# kategoria
t = unique_properties_vals['Kategória'][0]
r = re.search('([^/]*)/ predaj',t)
tt = r.group(1).replace('\n', '').rstrip()

# poschodie
t = unique_properties_vals['Poschodie'][0]
r = re.search('(^\d{1,2})', t)
tt = int(r.group(1))

# + celkovy pocet poschodi
t = unique_properties_vals['Poschodie'][0]
r = re.search('(\d{1,2}$)', t)
tt = int(r.group(1))

# zastavana plocha
t = unique_properties_vals['Zastavaná plocha'][0]
r = re.search('(\d{2,3}) m2', t)
tt = int(r.group(1))

# empty1 - cena za meter stvorcovy - je aj 0,00, alebo 393,03 tj dat to try except

t = unique_properties_vals['empty1'][0]
r = re.search('([^€]*) (€/m2)', t)
tt = int(r.group(1).replace(' ',''))

# pozemok

t = unique_properties_vals['pozemok'][0]
r = re.search('(^\d{2,4})', t)
tt = int(r.group(1))

# '\xa0' - to je link

# uzitkova plocha
t = unique_properties_vals['Úžitková plocha'][0]
r = re.search('(^\d{2,4})', t)
tt = int(r.group(1))

# proxy testing

import requests

# profile info
r = requests.get("https://proxy.webshare.io/api/profile/", headers={"Authorization": "Token 367b79438ef3df413c85c749149ded2f28aff639"})
r.json()

# subscription
r = requests.get("https://proxy.webshare.io/api/subscription/", headers={"Authorization": "Token 367b79438ef3df413c85c749149ded2f28aff639"})
r.json()

# proxy config
r = requests.get("https://proxy.webshare.io/api/proxy/config/", headers={"Authorization": "Token 367b79438ef3df413c85c749149ded2f28aff639"})
r.json()

# list proxies
r_list = requests.get("https://proxy.webshare.io/api/proxy/list/", headers={"Authorization": "Token 367b79438ef3df413c85c749149ded2f28aff639"})
r_list_json = r_list.json()

# proxy stats
r = requests.get("https://proxy.webshare.io/api/proxy/stats/", headers={"Authorization": "Token 367b79438ef3df413c85c749149ded2f28aff639"})
r.json()

# test proxy
import pickle
with open('browser_list.data', 'rb') as f:
    browser_list = pickle.load(f)
	
r = requests.get('https://api.ipify.org?format=json', 
				 proxies={"http": 'http://kdpfnrzk-10:w2kti3syhc5f@85.209.129.161:20009', "https": 'https://kdpfnrzk-10:w2kti3syhc5f@85.209.129.161:20009'}, 
				 headers = {'User-Agent': browser_list[0]}, 
				 timeout = 30, 
				 allow_redirects = False)
r.content

# test on local simple http server to see the request
r = requests.get('http://127.0.0.1:8000', 
				 headers = {'User-Agent': browser_list[0]}, 
				 timeout = 30, 
				 allow_redirects = False)
r.content
r.url
r.text
r.encoding
r.raw
r.status_code
r.headers
r.cookies
r.history

# test to webhook.site
r = requests.get('https://webhook.site/0882e9a7-3d32-4243-a8e4-113a1d5948e5',
				 proxies={"http": 'http://kdpfnrzk-10:w2kti3syhc5f@85.209.129.161:20009', "https": 'https://kdpfnrzk-10:w2kti3syhc5f@85.209.129.161:20009'}, 
				 headers = {'User-Agent': browser_list[0]}, 
				 timeout = 30, 
				 allow_redirects = False)
r.content

# test rotating proxy
r = requests.get('https://webhook.site/0882e9a7-3d32-4243-a8e4-113a1d5948e5',
				 proxies={"https": 'http://kdpfnrzk-rotate:w2kti3syhc5f@p.webshare.io'}, 
				 headers = {'User-Agent': browser_list[0]}, 
				 timeout = 30, 
				 allow_redirects = True)
r.content

# create json file with rotating proxy login
import json

with open('rotating_proxy.json', 'w') as f:
	json.dump({'rotating_proxy':'http://kdpfnrzk-rotate:w2kti3syhc5f@p.webshare.io'}, f)

# MONGO tests
import pymongo
myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection = scrapedb['ads']

# delete documents matching a condition
result = adcollection.delete_many({'scraped timestamp':{'$lt':datetime.strptime('2020-05-04', '%Y-%m-%d')}})
result.deleted_count


