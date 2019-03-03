# Scrape

A web scraper and a Dash app.

## Project description

This project can be split into 2 main parts: scraping data from a website and dash web application framework.
My goal was to scrape a website with interesting content and monitor the scraping process in a web app.	

As a target website to scrape I choosed 2nd most visited website in Slovakia with [real estate advertisements](https://www.topreality.sk),
with focus on flats offerings.

Example of scraped data are in pickled **ads.data** file. 
	
So basically you can get all important data related to real estate advertisement (like all  its properties - size,
number of rooms, price, map coordinates, energy certificates, seller information, text, tags, pictures, …)
in a structured way, already preprocessed.


### Part 1 - Scraping data

There are plenty of useful scraping resources out there, but for me most valuable was [scrapehero](https://www.scrapehero.com), 
for libraries which I choosed was Selenium and BeautifulSoup.

Regarding how the scraping process works, I wanted to design it so that it is not too easy detectable with
logic for choosing proxies based on epsilon-greedy explore-exploit algorithm, taken from the multi-armed bandit problem.
First, most common browseruser agents, which are used in requests headers are ready as a json file in the repo, or you can scrape them
with the function **scrape_user_agents()**. I used only elite (anonymous) https proxies from Slovakia, Hungary and Czech republic,
which can be scraped using function **scrape_proxies()**. There are 2 classes: **TopRealityAd**, which represents
the real estate advertisement and **proxyPool**, which represents the pool of proxies and takes care of the proxy
selection procedure.  Real estate data and data describing the scraping process are saved into MongoDB. 

### Part 2 - Scraping process monitoring

The Dash app is a monitor for the scraping process and it refreshes the data every 5 seconds.
Visualized on various types of charts, you can see:

* Statistics about time how long each link was scraped
* Number of attempts per link
* Compare artificial wait time, pure time and total time to process links
* Moving averages and cumulative quartiles of the total time to process links
* Cumulative mean of each bin (bandit) of proxies
* Number of times each bandit was chosen
* Proxies position change metric
* Detailed view of proxies means inside each bandit, in calculated window or all
* Detailed view of proxies response times

You can also choose from few prompts, like the value of moving average on selected charts, type of x asis,
or wether to limit visible data, since you can scrape thousands of links which can have a bit of impact
on the responsivity of the app and charts, but nothing dramatic.

When it comes to interactivity of the charts, you can use all the features of the plotly library (like zooming, exporting charts, … ).
If you want to for example preserve the zoomed chart, you have to click on Stop button to pause refreshing
the data (the feature to preserve the chart state is currently in development of the Dash team). On Proxies tab
you can click on some bandits boxplot and the other 2 charts will show corresponding data.

You can check a short video of the scraping process and the dash app [here](https://youtu.be/YmA7QfbOLVE)

## Environment and prerequisites

If you want to try the scraper and Dash app locally, you can recreate the anaconda environment which I used from the **scrape.yml** file.
If you experience errors with some packages during the process, just remove them from the yml file
and aftter finishing install them manually. I used Selenium with the Firefox driver, so do not forget to copy
the Gecko driver into the folder where the app is located. You have also to install Mongo DB and create 'scrapedb" database.
I used Windows 10 with Anaconda 3 and Python 3.6.

## Disclaimer

This project was done for educational purposes only.