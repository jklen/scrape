# -*- coding: utf-8 -*-
"""
Created on Mon Sep 10 13:14:33 2018

@author: j.klen
"""

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import time
import requests
import shutil
import pymongo
import datetime
import scipy.stats
import base64
import random
import numpy as np

class TopRealityAd:
    def __init__(self, url, proxy_pool, useragents_list):
        self.url = url
        self.properties = {}
        self.text = None
        self.tags = []
        self.energycert = 'Nema'
        self.gallerylinks = []
        self.seller = {}
        self.mapcoord = {}
        self.proxy_pool = proxy_pool
        self.useragents_list = useragents_list
                
        success = False
        attempts = 0
        
        while success == False:
            wait()
            proxy = self.proxy_pool.choose_proxy()
            useragent = random.choice(self.useragents_list)
            try:
                response = requests.get(self.url, proxies={"http": proxy, "https": proxy}, headers = {'User-Agent': useragent}, timeout = 30)
            except:
                self.proxy_pool.update(proxy, 30)
                attempts += 1
            else:
                self.proxy_pool.update(proxy, response.elapsed.total_seconds())
                self.soup = BeautifulSoup(response.content, 'html.parser')
                success = True
        print('Top reality ad response successful, attempts: ' + str(attempts + 1))
    
    def scrape_properties(self):        
        i = 0

        for li in self.soup.find('div', {'class':'properties'}).ul.find_all('li'):
            key = li.span.text
            if key == '\xa0':
                key = 'empty' + str(i)
                i += 1
            self.properties[key] = li.strong.text
    
    def scrape_text(self):
        self.text = self.soup.find('p', {'itemprop':'description'}).text
    
    def scrape_tags(self):        
        try:
            for a in self.soup.find('div', {'class':'detail-keywords'}).find_all('a'):
                self.tags.append(a.text)
        except:
            pass
    
    def scrape_energycert(self):        
        try:
            self.energycert = self.soup.find('div', {'class':'energCert'}).div.span.text
        except:
            pass
    
    # put here check if picture is alrady downloaded
    def scrape_gallerylinks(self, save = True): # set timeout to request
        self.gallerylinks.append('https://topreality.sk' + self.soup.find('div', {'class':'gallery'}).a['href'])

        for li in self.soup.find('div', {'class':'gallery'}).ul.find_all('li'):
            self.gallerylinks.append('https://topreality.sk/' + li.a['href'])
        print('Number of pictures: ' + str(len(self.gallerylinks)))
        if save:
            if 'empty1' in self.properties:
                ad_id = re.search('id(\d*)', self.properties['empty1'])[1]
            else:
                ad_id = re.search('id(\d*)', self.properties['empty0'])[1] # cena dohodou
            self.gallery_dir = 'data/pics/topreality/' + ad_id
            gallery_dir = self.gallery_dir
            
            if not os.path.exists(gallery_dir):
                os.makedirs(gallery_dir)
                                    
            for i, pic_link in enumerate(self.gallerylinks):
                success = False
                attempts = 1
                while success == False:
                    wait()
                    proxy = self.proxy_pool.choose_proxy()
                    useragent = random.choice(self.useragents_list)
                    try:
                        response = requests.get(pic_link, stream = True, proxies={"http": proxy, "https": proxy}, headers = {'User-Agent': useragent}, timeout = 30)
                        
                    except:
                        self.proxy_pool.update(proxy, 30)
                        attempts += 1
                        #pass
                    else:
                        self.proxy_pool.update(proxy, response.elapsed.total_seconds())
                        with open(gallery_dir + '/' + 'img' + str(i) + '.jpg', 'wb') as out_file:
                            try:
                                shutil.copyfileobj(response.raw, out_file)
                            except:
                                print('Error saving picture')
                            else:
                                print('Picture %d saved successfuly, attempts: %d' %(i + 1, attempts))
                                success = True
    
    def scrape_seller(self):        
        try:
            self.seller['name'] = self.soup.find('div', {'class':'contact'}).a.strong.text
            seller_regex = re.search('<br/{0,1}>(.*)<br/{0,1}>(.*)<br/{0,1}><br/{0,1}><span>Registrovaný na TopReality.sk<br/>od (.*)</span>', str(self.soup.find('div', {'class':'contact'})))
            self.seller['street'] = seller_regex[1]
            self.seller['city'] = seller_regex[2]
            self.seller['since'] = seller_regex[3]
            self.seller['type'] = 'agency'
        except:
            self.seller['type'] = 'private'
            
    def scrape_mapcoords(self):
        try:
            map_div_for_regex = self.soup.find('div', {'id':'map_canvas'})['data-kml']
            ad_map_coord_regex = re.search('lon=(\d{1,3}\.\d{2,20})&lat=(\d{1,3}\.\d{2,20})', map_div_for_regex)
            self.mapcoord = {'lon':float(ad_map_coord_regex[1]),
                            'lat':float(ad_map_coord_regex[2])}
        except TypeError: # bacause map canvas might be not present
            pass
            
    def correct_values(self):
        
        self.properties['Cena'] = float(0) if self.properties['Cena'].strip() == 'cena dohodou' else float(self.properties['Cena'].split(',')[0].replace(' ', ''))
        if 'Hypotéka' in self.properties:
            self.properties['Hypotéka'] = float(self.properties['Hypotéka'].split(' ')[1])
        if 'Poschodie' in self.properties:
            self.properties['Počet poschodí'] = int(self.properties['Poschodie'].split('/')[1].strip())
            self.properties['Poschodie'] = int(self.properties['Poschodie'].split('/')[0].strip())
        self.properties['Cena za meter'] = float(0) if self.properties['Cena'] == 0 else float(self.properties['empty0'].split(' ')[0].replace(',', '.'))
        self.properties['Úžitková plocha v m2'] = float(self.properties['Úžitková plocha'].split(' ')[0])
        del(self.properties['Úžitková plocha'])
        self.properties['Link s id'] = self.properties.pop('empty1') if  'empty1' in self.properties else self.properties.pop('empty0')
        self.properties['Aktualizácia'] = datetime.datetime.strptime(self.properties['Aktualizácia'], '%d.%m.%Y %H:%M:%S')
        if 'empty0' in self.properties:
            del(self.properties['empty0'])
        if 'name' in self.seller:
            self.seller['name'] = self.seller['name'].strip(u'\u200b')
        if 'since' in self.seller:
            self.seller['since'] = datetime.datetime.strptime(self.seller['since'], '%d.%m.%Y')
        
        # put all info into one dictionary
        
        self.ad = {'properties':self.properties,
              'pictureslinks':self.gallerylinks,
              'text':self.text,
              'tags':self.tags,
              'seller':self.seller,
              'energycert':self.energycert,
              'mapcoord':self.mapcoord,
              'gallerydir':os.getcwd().replace('\\' ,'/') + '/' + self.gallery_dir}
    
    def scrape_all(self):
        self.scrape_properties()
        self.scrape_text()
        self.scrape_tags()
        self.scrape_energycert()
        self.scrape_gallerylinks()
        self.scrape_seller()
        self.scrape_mapcoords()
        self.correct_values()
    
    def writetodb(self, dbcollection):
        x = dbcollection.insert_one(self.ad)

def scrape_useragents(agents = ['chrome', 'firefox', 'opera']):
    
    driver = webdriver.Firefox()
    useragents_list = []
    very_common = True 
        
    for agent in agents:
        page_nr = 1
        very_common = True # scrape only very common agent names
        while very_common:
            wait()
            url = 'https://developers.whatismybrowser.com/useragents/explore/software_name/' + agent + '/' + str(page_nr)
            driver.get(url)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            for tr in soup.find('tbody').find_all('tr'):
                if tr.find_all('td')[4].text == 'Very common':
                    useragents_list.append(tr.td.a.text)
                else:
                    very_common = False
                    break
            page_nr += 1
    
    driver.close()
    
    return useragents_list
    

def scrape_proxies():
    
    proxy_list = []
    
    # free-proxy.cz
    driver = webdriver.Firefox()
    driver.set_page_load_timeout(20)
    time.sleep(4)
    try:
        driver.get('http://free-proxy.cz/en/proxylist/country/SK/https/ping/level1')
    except:
        print('free-proxy.cz not available')
    else:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        for tr in soup.find('tbody').find_all('tr'):
            try:
                proxy_ip = base64.b64decode(re.search('Base64.decode\((.*)\)\)</script', str(tr.td))[1]).decode('unicode_escape')
                proxy_port = tr.find_all('td')[1].text
                proxy_list.append(proxy_ip + ':' + proxy_port)
            except:
                pass
        print('Scraping free-proxy successful')
    
    # http://www.gatherproxy.com
    urls = ['http://www.gatherproxy.com/proxylist/country/?c=Czech%20Republic',
            'http://www.gatherproxy.com/proxylist/country/?c=Slovak%20Republic',
            'http://www.gatherproxy.com/proxylist/country/?c=Hungary']
    for url in urls:
        wait()
        try:
            driver.get(url)
        except:
            print('%s not available.' % url)
        else:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            for tr in soup.find_all('tr', {'type':'Elite'}):
                proxy_list.append(tr['prx'])
            print('Scraping %s successful' % url)
    
    # http://spys.one/free-proxy-list/SK/
    try:
        driver.get('http://spys.one/free-proxy-list/SK/')
    except:
        print('spys.one not available')
    else:
        select_proxy_type = Select(driver.find_element_by_id('xf1'))
        select_proxy_type.select_by_value('4')  # high anonymous proxy
        wait()
        select_ssl = Select(driver.find_element_by_id('xf2'))
        select_ssl.select_by_value('1') # https
        wait()
        select_http = Select(driver.find_element_by_id('xf5'))
        select_http.select_by_value('1') 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        for tr in soup.find_all('tr', {'class':['spy1x', 'spy1xx']})[2:]:
            soup = tr.td.find_all('font')[1]
            proxy_regex = re.search('class="spy14">(\d{1,3}\.\d{1,3}\.\d{1,3}).*class="spy2">:</font>(\d{1,5})', str(soup))
            proxy_ip_port = proxy_regex[1] + ':' + proxy_regex[2]
            proxy_list.append(proxy_ip_port)
        print('Scraping spys.one successful')
    
    proxy_list = list(set((proxy_list)))
    driver.close()
    
    return proxy_list

def wait(minval = 0.5, maxval = 20, meanval = 2.5, std = 2.7):
    dist = scipy.stats.truncnorm((minval - meanval) / std, (maxval - meanval) / std, loc = meanval, scale = std)
    value = dist.rvs()
    print('Waiting ' + str(value) + ' s.')
    time.sleep(value)

def scrape_topreality_links(region = None, pages_to_scrape = 5):
    
    driver = webdriver.Firefox()
    time.sleep(4)
    driver.get('https://topreality.sk')
    
    dropdown_type = Select(driver.find_element_by_id('n_srch_typ'))
    dropdown_type.select_by_value('1') # typ: predaj
    
    # ---
    button_druh = driver.find_element_by_class_name('ui-multiselect.ui-widget.ui-state-default.ui-corner-all')
    button_druh.click() # vyvolat popup s druhom nehnutelnosti
    
    time.sleep(4)
    select_byt = driver.find_element_by_xpath("//ul[@class='ui-multiselect-checkboxes ui-helper-reset']/li[1]")
    select_byt.click() # druh nehnutelnosti - byty
    # ---
    # ---
    time.sleep(1)
    hover = ActionChains(driver).move_to_element(select_byt) # hover away from the popup
    hover.perform()
    time.sleep(2)
    
    if region != None:
        select_lokalita = driver.find_element_by_xpath("//div[@id='n_srch_obec_suggest']/div[@class='ms-sel-ctn']/input[@placeholder='Okres, obec, ulica']")
        select_lokalita.click()
        time.sleep(1)
        select_lokalita.send_keys(region)
        time.sleep(2)
        select_lokalita2 = driver.find_element_by_xpath("//div[@class='ms-res-ctn dropdown-menu']")
        hover = ActionChains(driver).move_to_element(select_lokalita2)
        hover.perform()
        time.sleep(1)
        select_lokalita3 = driver.find_element_by_xpath("//div[@class='ms-res-item ms-res-item-active']//li[1]")
        select_lokalita3.click()
    # ---
    
    results = driver.find_element_by_xpath("//span[@id='foundresults']/strong")
    results_nr = int(results.text.replace(' ', ''))
    results_nr_on_page = 15
    
    if results_nr % results_nr_on_page == 0:
        pages_nr = results_nr/results_nr_on_page
    else:
        pages_nr = results_nr//results_nr_on_page + 1
    
    if pages_to_scrape == 'all':
        pages = int(pages_nr + 1)
    else:
        if pages_nr >= pages_to_scrape:
            pages = int(pages_to_scrape + 1)
        else:
            pages = int(pages_nr + 1)
    
    button_search = driver.find_element_by_name('n_search') # 'vyhladat' button
    button_search.click()
    
    # close 'zasielat ponuky e-mailom'
    
    time.sleep(2)
    button_close = driver.find_element_by_xpath("//button[@title='Close']")
    button_close.click()
    
    # get links on a page - 15 real estate ads
    links = []
    
    for i in range(1, pages):
        if i >= 2:
            button_page = driver.find_element_by_xpath("//div[@class='paginatorContainer']//div[@class='paginator']//a[text()='" + str(i) + "']")
            button_page.click()
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        listing_container = soup.find('div', {'class':'listing'})
        for d in listing_container.find_all('div', {'class':re.compile(r'^estate')}):
            links.append(d.find('div', {'class':'thumb'}).a['href'])
        print('Page ' + str(i) + '/' + str(pages - 1) + ' done')
        wait(minval = 1.5, maxval = 10, meanval = 2.5, std = 2)
    
    driver.close()
    
    return links
