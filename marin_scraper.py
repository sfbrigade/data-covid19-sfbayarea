# is there a way to get historical data
# is there a way to have a script click on the "download csv" files?
#!/usr/bin/env python3
import csv
import json
import numpy as np
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import unquote_plus

# GOING TO WORK ON: then scrape the metadata, and then figure out how to download the CSVs (seleniuim)
# throw error when the button isn't correctly pressed
# do a final check 
def get_county_data():
	url = 'https://coronavirus.marinhhs.org/surveillance'
	case_csv = '/Users/angelakwon/Downloads/data-Eq6Es.csv'
	"""Main method for populating county data"""
	with open('/Users/angelakwon/Desktop/data-covid19-sfbayarea/data-model.json') as template:
		model = json.load(template)

	#model['name'] = 
	#model['update_time'] = 
	model['source_url'] = url
	#model['meta_from_source'] = 
	# make sure to get the comments below the data
	#model['meta_from_baypd']
	model["series"]["cases"] = get_case_series(case_csv) 
	model["series"]["deaths"] =  get_death_series(case_csv)
	#model["series"]["tests"] = get_test_series(case_csv)

	#print(model)
	#print(get_metadata(url))
	print(extract_csvs(url))

def extract_csvs(url):
	# div class = "dw-chart-notes"
	driver = webdriver.Chrome('/Users/angelakwon/Downloads/chromedriver') 
	# can I leave this blank, will virtual env take care of it?
	driver.implicitly_wait(30)
	driver.get(url)

	chart_id = 'tyXjV'
	frame = driver.find_element_by_css_selector(f'iframe[src^="//datawrapper.dwcdn.net/{chart_id}/"]')
	driver.switch_to.frame(frame)
	# Grab the raw data out of the link's href attribute
	csv_data = driver.find_element_by_class_name('dw-data-link').get_attribute('href')
	# Switch back to the parent frame to "reset" the context
	driver.switch_to.parent_frame()

	# Deal with the data
	if csv_data.startswith('data:'):
    	media, data = csv_data[5:].split(',', 1)
    # Will likely always have this kind of data type
    if media != 'application/octet-stream;charset=utf-8':
        raise ValueError(f'Cannot handle media type "{media}"')
    csv_string = unquote_plus(data)
    print(csv_string)

	# Then leave the iframe
	driver.switch_to.default_content()
	#return 'Done downloading'


def get_metadata(url):
	# I think I want to return a list

	notes = []
	driver = webdriver.Chrome('/Users/angelakwon/Downloads/chromedriver')
	driver.implicitly_wait(30)
	driver.get(url)
	soup = BeautifulSoup(driver.page_source, 'html5lib')
	soup.find_all('p') 
	# THEN use the getText function
	
	driver.quit() # does this close the tab?

def get_case_series(csv_):
	series = []
	with open(csv_, mode = 'r') as case_csv: 
		csv_reader = csv.DictReader(case_csv)
		csv_headers = list(next(csv_reader).keys()) # TO-DO: Make it work without hard coding the keys
		case_history = []
		for row in csv_reader:
			# TO-DO: throw an exception if there are more than the expected number of headers, or when order has changed
			daily = {}
			daily["date"] = row["Date"] # TO-DO: need to format the date properly
			case_history.append(int(row["Total Cases"]))
			daily["cumul_cases"] = row["Total Cases"]
			series.append(daily)
		
	case_history_diff = np.diff(case_history) 
	case_history_diff = np.insert(case_history_diff, 0, 0) # there will be no calculated difference for the first day, so adding it in manually
	for val, case_num in enumerate(case_history_diff):
		series[val]["cases"] = case_num
	return series

def get_death_series(csv_):
	series = []
	with open(csv_, mode = 'r') as case_csv: 
		csv_reader = csv.DictReader(case_csv)
		csv_headers = list(next(csv_reader).keys()) # TO-DO: Make it work without hard coding the keys
		case_history = []
		for row in csv_reader:
			# TO-DO: throw an exception if there are more than the expected number of headers, or when order has changed
			daily = {}
			daily["date"] = row["Date"] # TO-DO: need to format the date properly
			case_history.append(int(row["Total Deaths"]))
			daily["cumul_deaths"] = row["Total Deaths"]
			series.append(daily)
		
	case_history_diff = np.diff(case_history) 
	case_history_diff = np.insert(case_history_diff, 0, 0) # there will be no calculated difference for the first day, so adding it in manually
	for val, case_num in enumerate(case_history_diff):
		series[val]["deaths"] = case_num # should I change up the order of the keys?
	return series

#def get_test_series():
	# "date": "yyyy-mm-dd",
 #                "tests": -1,
 #                "positive": -1,
 #                "negative": -1,
 #                "pending": -1,
 #                "cumul_tests": -1,
 #                "cumul_pos": -1,
 #                "cumul_neg": -1,
 #                "cumul_pend": -1
 	#save the first row as values
 	#need to keep track of pos and negative, but no values for pending


#def get_case_totals_gender():

#def get_case_totals_age():

#def get_case_totals_race_eth():

#def get_case_totals_category():


#def get_death_totals_gender():

#def get_death_totals_age():

#def get_death_totals_race_eth():

#def get_death_totals_underlying():

#def get_death_totals_transmission(): # not sure if this information exists

# population totals

get_county_data()
# figure out a way to run the scraper through the command line 