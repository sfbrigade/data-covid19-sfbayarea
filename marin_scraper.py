#!/usr/bin/env python3
import csv
import json
import numpy as np
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import unquote_plus
from datetime import datetime


# do a final check 
def get_county_data():
	"""Main method for populating county data"""

	url = 'https://coronavirus.marinhhs.org/surveillance'
	with open('/Users/angelakwon/Desktop/data-covid19-sfbayarea/data-model.json') as template:
		# TO-DO: Need to change this to github location
		model = json.load(template)

	csvs = {"cases": "Eq6Es", "deaths": "Eq6Es", "tests": None, "age": "VOeBm", "gender": "FEciW", "race_eth": "aBeEd", "transmission": None}
	# NOTE: they used to have a pos/neg test csv, but it seems to be gone now. 
	# also, their graph doesn't show pos/neg.
	# population totals and transmission data missing.

	#model['name'] = 
	#model['update_time'] = 
	model['source_url'] = url
	#model['meta_from_source'] = 
	# make sure to get the comments below the data
	#model['meta_from_baypd']
	#model["series"]["cases"] = get_case_series(csvs["cases"], url) 
	#model["series"]["deaths"] =  get_death_series(csvs["deaths"], url)
	#model["series"]["tests"] = get_test_series(case_csv)
	#model["case_totals"]["age_group"], model["death_totals"]["age_group"] = get_breakdown_age(csvs["age"], url)
	#model["case_totals"]["gender"], model["death_totals"]["gender"] = get_breakdown_gender(csvs["gender"], url)
	model["case_totals"]["race_eth"], model["death_totals"]["race_eth"] = get_breakdown_race_eth(csvs["race_eth"], url)
	print(model["case_totals"]["race_eth"], model["death_totals"]["race_eth"])
	

def extract_csvs(chart_id, url):
	driver = webdriver.Chrome('/Users/angelakwon/Downloads/chromedriver') # can I leave this blank, will virtual env take care of it?
	
	driver.implicitly_wait(30)
	driver.get(url)

	#frame = driver.find_element_by_css_selector(f'iframe[src^="//datawrapper.dwcdn.net/{chart_id}/"]')
	# the link changed - now it attaches a random number after the chart id so I needed to change the attribute.
	frame = driver.find_element_by_css_selector(f'iframe[src*="//datawrapper.dwcdn.net/{chart_id}/"]')
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
		

	# Then leave the iframe
	driver.switch_to.default_content()
	return csv_string


def get_metadata(url):
	# I think I want to return a list

	notes = []
	driver = webdriver.Chrome('/Users/angelakwon/Downloads/chromedriver')
	driver.implicitly_wait(30)
	driver.get(url)
	soup = BeautifulSoup(driver.page_source, 'html5lib')
	soup.find_all('p') .getText()
	# THEN use the getText function
	
	driver.quit() 

def get_case_series(chart_id, url):
	csv_ = extract_csvs(chart_id, url)
	series = []

	csv_strs = csv_.splitlines()
	keys = csv_strs[0].split(',')
	#print(keys)
	
	case_history = []

	for row in csv_strs[1:]:
	# 	# TO-DO: throw an exception if there are more than the expected number of headers, or when order has changed
	 	daily = {}
	 	#daily["date"] = row.split(',')[0] 
	 	date_time_obj = datetime.strptime(row.split(',')[0], '%m/%d/%Y')
	 	daily["date"] = date_time_obj.isoformat()
	 	# TO-DO: need to format the date properly
	 	case_history.append(int(row.split(',')[1]))
	 	daily["cumul_cases"] = int(row.split(',')[1])
	 	series.append(daily)
		
	case_history_diff = np.diff(case_history) 
	case_history_diff = np.insert(case_history_diff, 0, 0) # there will be no calculated difference for the first day, so adding it in manually
	for val, case_num in enumerate(case_history_diff):
		series[val]["cases"] = case_num
	return series

def get_death_series(chart_id,  url):
	csv_ = extract_csvs(chart_id, url)
	series = []

	csv_strs = csv_.splitlines()
	keys = csv_strs[0].split(',')
	
	death_history = []

	for row in csv_strs[1:]:
	# 	# TO-DO: throw an exception if there are more than the expected number of headers, or when order has changed
	 	daily = {}
	 	date_time_obj = datetime.strptime(row.split(',')[0], '%m/%d/%Y')
	 	daily["date"] = date_time_obj.isoformat()
	 	death_history.append(int(row.split(',')[4]))
	 	daily["cumul_deaths"] = int(row.split(',')[4])
	 	series.append(daily)
		
	death_history_diff = np.diff(death_history) 
	death_history_diff = np.insert(death_history_diff, 0, 0) # there will be no calculated difference for the first day, so adding it in manually
	for val, death_num in enumerate(death_history_diff):
		series[val]["deaths"] = death_num
	return series


def get_breakdown_age(chart_id, url):
	""" Gets breakdown of cases and deaths by age """
	csv_ = extract_csvs(chart_id, url)
	c_brkdown = []
	d_brkdown = []

	csv_strs = csv_.splitlines()
	keys = csv_strs[0].split(',') # don't know if this is actually needed

	
	for row in csv_strs[1:]:
		c_age = {}
		d_age = {}
		c_age["group"] = row.split(',')[0]
		c_age["raw_count"] = int(row.split(',')[2])
		d_age["group"] = row.split(',')[0]
		d_age["raw_count"] = int(row.split(',')[4])
		c_brkdown.append(c_age)
		d_brkdown.append(d_age)

	return c_brkdown, d_brkdown

def get_breakdown_gender(chart_id, url):
	""" Gets breakdown of cases and deaths by gender """
	csv_ = extract_csvs(chart_id, url)

	csv_strs = csv_.splitlines()
	keys = csv_strs[0].split(',') # don't know if this is actually needed

	c_gender = {}
	d_gender = {}
	
	for row in csv_strs[1:]:
		split = row.split(',')
		gender = split[0].lower()
		c_gender[gender] = int(split[2])
		d_gender[gender] = int(split[4])			
		# check to see what other scrapers have done with missing data model values

	return c_gender, d_gender


def get_breakdown_race_eth(chart_id, url):
	csv_ = extract_csvs(chart_id, url)

	csv_strs = csv_.splitlines()
	key_mapping = {"black/african american":"African_Amer", "hispanic/latino": "Latinx_or_Hispanic",
            "american indian/alaska native": "Native_Amer", "native hawaiian/pacific islander": "Pacific_Islander", "white": "White", "asian": "Asian", "multi or other race": "Multi or Other Race"}
            # "Multiple_Race", "Other" are not separate in this data set - they are one value under "Multi or Other Race"

	c_race_eth = {}
	d_race_eth = {}
	
	for row in csv_strs[1:]:
		split = row.split(',')
		race_eth = split[0].lower()
		if race_eth not in key_mapping:
			print("New race_eth group")
		else:
			c_race_eth[key_mapping[race_eth]] = int(split[2])
			d_race_eth[key_mapping[race_eth]] = int(split[6])
		# check to see what other scrapers have done with missing data model values

	return c_race_eth, d_race_eth

#def get_breakdown_transmission():

#def get_death_totals_underlying():


#def get_test_series():


get_county_data()


# figure out a way to run the scraper through the command line 