# -*- coding: utf-8 -*-
"""
Created on Mon Aug  6 15:06:42 2018

@author: j.klen
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
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

working_dir = 'C:\\Users\\j.klen\\PythonProjects\\scrape'
os.chdir(working_dir)

url = 'https://topreality.sk'

myclient = pymongo.MongoClient('mongodb://localhost:27017')
scrapedb = myclient['scrapedb']
adcollection = scrapedb['ads']

#fp = webdriver.FirefoxProfile()
#fp.set_preference("browser.link.open_newwindow", 3)
#fp.set_preference("browser.link.open_newwindow.restriction", 2)

#driver = webdriver.Firefox(firefox_profile=fp)

driver = webdriver.Firefox()
time.sleep(2)
driver.get(url)

dropdown_type = Select(driver.find_element_by_id('n_srch_typ'))
dropdown_type.select_by_value('1') # typ: predaj

# ---
button_druh = driver.find_element_by_class_name('ui-multiselect.ui-widget.ui-state-default.ui-corner-all')
button_druh.click() # vyvolat popup s druhom nehnutelnosti

time.sleep(2)
select_byt = driver.find_element_by_xpath("//ul[@class='ui-multiselect-checkboxes ui-helper-reset']/li[1]")
select_byt.click() # druh nehnutelnosti - byty
# ---
# ---
time.sleep(2)
element_to_hover = select_byt
hover = ActionChains(driver).move_to_element(element_to_hover)
hover.perform()

select_lokalita = driver.find_element_by_id('token-input-n_srch_obec')
select_lokalita.click()
select_lokalita.send_keys('Trnavský kraj')
time.sleep(2)
select_lokalita2 = driver.find_element_by_xpath("//div[@class='token-input-dropdown-topreality']//li[1]")
select_lokalita2.click()
# ---

results = driver.find_element_by_xpath("//span[@id='foundresults']/strong")
results_nr = int(results.text.replace(' ', ''))
results_nr_on_page = 15

if results_nr % results_nr_on_page == 0:
    pages_nr = results_nr/results_nr_on_page
else:
    pages_nr = results_nr//results_nr_on_page + 1

button_search = driver.find_element_by_name('n_search') # 'vyhladat' button
button_search.click()

# close 'zasielat ponuky e-mailom'

button_close = driver.find_element_by_xpath("//button[@title='Close']")
button_close.click()

# get links on a page - 15 real estate ads
links = []

for i in range(1, 5):
    if i >= 2:
        button_page = driver.find_element_by_xpath("//div[@class='paginatorContainer']//div[@class='paginator']//a[text()='" + str(i) + "']")
        button_page.click()
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    listing_container = soup.find('div', {'class':'listing'})
    for d in listing_container.find_all('div', {'class':re.compile(r'^estate')}):
        links.append(d.find('div', {'class':'thumb'}).a['href'])
    
    time.sleep(3)


# scrape ad
#   tabulka - ad_properties{}
#   fotky - ad_gallery_links[]
#   text - ad_text
#   stitky (Ďalšie vlastnosti nehnuteľnosti) - ad_tags[]
#   predajca - ad_seller{}
#   energ. certifikat (Ukazovateľ integrovanej energetickej hospodárnosti) - ad_energyCert
#   koordinaty z mapy - ad_map_coord



link = 'https://www.topreality.sk/predaj-3iz-byt-topolniky-r6300350.html'
response = requests.get(link)
soup = BeautifulSoup(response.content, 'html.parser')

# ad properties
ad_properties = {}
i = 0

for li in soup.find('div', {'class':'properties'}).ul.find_all('li'):
    key = li.span.text
    if key == '\xa0':
        key = 'empty' + str(i)
        i += 1
    ad_properties[key] = li.strong.text

# ad text    
ad_text = soup.find('p', {'itemprop':'description'}).text

# ad tags
ad_tags = []

try:
    for a in soup.find('div', {'class':'detail-keywords'}).find_all('a'):
        ad_tags.append(a.text)
except:
    pass
    
# ad energy certificate
ad_energyCert = 'Nema'

try:
    ad_energyCert = soup.find('div', {'class':'energCert'}).div.span.text
except:
    pass

# ad pictures
#   get pictures links    
ad_galleryLinks = []
ad_galleryLinks.append('https://topreality.sk' + soup.find('div', {'class':'gallery'}).a['href'])

for li in soup.find('div', {'class':'gallery'}).ul.find_all('li'):
    ad_galleryLinks.append('https://topreality.sk/' + li.a['href'])

#   save the pics into folder

ad_id = re.search('id(\d*)', ad_properties['empty1'])[1]
gallery_dir = 'data/pics/topreality/' + ad_id

if not os.path.exists(gallery_dir):
    os.makedirs(gallery_dir)

for i, pic_link in enumerate(ad_galleryLinks):
    time.sleep(3)
    response = requests.get(pic_link, stream = True)
    with open(gallery_dir + '/' + 'img' + str(i) + '.jpg', 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)

# ad seller
        
ad_seller = {}

try:
    ad_seller['name'] = soup.find('div', {'class':'contact'}).a.strong.text
    # other info is via regex, since br tags are not closed properly
    ad_seller_regex = re.search('<br>(.*)<br>(.*)<br><br/{0,1}><span>Registrovaný na TopReality.sk<br/>od (.*)</span>', str(soup.find('div', {'class':'contact'}).br))
    ad_seller['street'] = ad_seller_regex[1]
    ad_seller['city'] = ad_seller_regex[2]
    ad_seller['since'] = ad_seller_regex[3]
    ad_seller['type'] = 'agency'
except:
    ad_seller['type'] = 'private'
            

# ad map coordinates

ad_map_coord = {}
try:
    map_div_for_regex = soup.find('div', {'id':'map_canvas'})['data-kml']
    ad_map_coord_regex = re.search('lon=(\d{1,3}\.\d{2,7})&lat=(\d{1,3}\.\d{2,7})', map_div_for_regex)
    ad_map_coord = {'lon':float(ad_map_coord_regex[1]),
                    'lat':float(ad_map_coord_regex[2])}
except TypeError: # bacause map canvas might be not present
    pass

# correct values
#   ad properties
#       - Cena ako float
#       - Hypoteka ako float
#       - Poschodia ako int, novy Pocet poschodi ako int
#       - emty0 premenovat Cena za meter2, ako float
#       - uzitkova plocha ako float
#       - datum aktualizacie ako datetime

ad_properties['Cena'] = float(ad_properties['Cena'].split(',')[0].replace(' ', ''))
ad_properties['Hypotéka'] = float(ad_properties['Hypotéka'].split(' ')[1])
if 'Poschodie' in ad_properties:
    ad_properties['Počet poschodí'] = int(ad_properties['Poschodie'].split('/')[1].strip())
    ad_properties['Poschodie'] = int(ad_properties['Poschodie'].split('/')[0].strip())
ad_properties['Cena za meter'] = float(ad_properties['empty0'].split(' ')[0].replace(',', '.'))
del(ad_properties['empty0'])
ad_properties['Úžitková plocha v m2'] = float(ad_properties['Úžitková plocha'].split(' ')[0])
del(ad_properties['Úžitková plocha'])
ad_properties['Link s id'] = ad_properties.pop('empty1')
ad_properties['Aktualizácia'] = datetime.datetime.strptime(ad_properties['Aktualizácia'], '%d.%m.%Y %H:%M:%S')

# put all info into one dictionary

ad = {'properties':ad_properties,
      'pictureslinks':ad_galleryLinks,
      'text':ad_text,
      'tags':ad_tags,
      'seller':ad_seller,
      'energycert':ad_energyCert,
      'mapcoord':ad_map_coord,
      'gallerydir':os.getcwd().replace('\\' ,'/') + '/' + gallery_dir}

# save scraped ad info to database

x = adcollection.insert_one(ad)

# random timing
# rotating proxies
# rotating browser headers
# make ad as class?
# or myscraper as class, with methods:
#   scrape_topreality_links(filter_kraj, type = ['all', pages_nr, 'new', 'updated'])
#   scrape_ad(link, browser_header_list, proxies_list)
#   save_to_db(dict)

# skrejpovat celkovo
# skrejpovat len novo pridane
# skrejpovat len novo aktualizovane


"""

myclient = pymongo.MongoClient('mongodb://localhost:27017') # connect to local mongodb instance
scrapedb = myclient['scrapedb'] # create database (but database gets created after we insert into it some document)
print(myclient.list_database_names()) # list databases
adcollection = scrapedb['ads'] # create collection
x = adcollection.insert_one(ad_properties) # insert one document

# downloading picture via requests
import requests
import shutil
jpg_link = 'https://www.topreality.sk/predaj-2i-byt-v-novostabe-v-gabcikove-d1-634-6346689_1.jpg'
response = requests.get(jpg_link), stream = True)
with open('img_test.jpg', 'wb') as out_file:
    shutil.copyfileobj(response.raw, out_file)

# open new tab with link
driver.execute_script("window.open('https://www.topreality.sk/predaj-59m2-kompletne-rekonstruovany-3izbovy-byt-v-dunajskej-strede-r6297145.html');")
driver.switch_to.window(driver.window_handles[1]) # focus on new tab
driver.close() # close the new tab

driver.switch_to.window(driver.window_handles[0]) # focus on first tab
driver.close() # close first(only) tab, closes the browser


selenium element info

element.text
element.tag_name
element.parent
element.location
element.size

get value of elements attribute

element.get_attribute('class')

"""
