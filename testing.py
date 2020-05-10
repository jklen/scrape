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

# unique values for each of the property
