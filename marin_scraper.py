# is there a way to get historical data
# is there a way to have a script click on the "download csv" files?
#!/usr/bin/env python3
import csv
import json
import numpy as np
from selenium import webdriver
from bs4 import BeautifulSoup

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
	print(download_csvs(url))

def download_csvs(url):
	# div class = "dw-chart-notes"
	driver = webdriver.Chrome('/Users/angelakwon/Downloads/chromedriver')
	driver.implicitly_wait(30)
	driver.get(url)

	iframe_list = driver.find_elements_by_tag_name('iframe')
	driver.switch_to.frame(iframe_list[3])
	driver.implicitly_wait(30)
	for elt in driver.find_elements_by_tag_name('a'):
		if not elt.is_displayed():
			elt.sendkeys(Keys.RETURN) # got the element to be clicked on, but... not downloading anything?
	#print(driver.find_elements_by_css_selector('.dw-chart-footer .dw-data-link')) 
	#.class1 .class2
	#print(driver.find_elements_by_css_selector('div.footer > a')) 

	#link = driver.find_element_by_tag_name('a')
	#print(driver.find_elements_by_tag_name('a')) # there are two
	#print(driver.find_elements_by_css_selector('#datawrapper-chart-Eq6Es a')) # I think this selection is wrong

	#datawrapper-chart-Eq6Es a

	#print(driver.find_elements_by_class_name('dw-data-link'))
	#driver.maximize_window()
	#print("Element is visible? " + str(driver.find_element_by_tag_name('a').is_displayed()))

	#print("Element is visible? " + str(driver.find_element_by_class_name('dw-data-link').is_displayed()))

	#WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a')))
	#ActionChains(driver).move_to_element(link).click(link).perform()
	# both of these produce the same kind of error



	# so the reason I was getting a null error was because... 
	# you can't select an iframe  using the name? not sure.

	# 1. try to switch to the iframe using the name or id. 
	# The name is datawrapper-chart-Eq6Es
	#return driver.switch_to.frame('datawrapper-chart-Eq6Es')
	# returns None

	# 2. Try to switch to the iframe using the frame index
	#return driver.switch_to.frame(3)
	# returns None
	# maybe it's lowkey nested, so let's just get the first frame.
	#return driver.switch_to.frame(1)

	# 3. Try XPATH - recommended in a good number of SO posts.
	#csv = driver.find_element_by_xpath("/////////////iframe[1]")
	# seems too deep to be found by xpath?
	#return csv


	# Then search for the element by class name/tag name.
	#driver.find_element(By.TAG_NAME, 'a').click()

	# all csvs have the a tag, and class=dw-data-link
	#print(driver.find_element_by_class_name("dw-data-link"))

	# x path is probably not the best way, but let's give it a try
	# the click button is within the  within an iframe. 
	# I need to switch to the iframe, and then click, 


	# Then leave the iframe
	driver.switch_to.default_content()
	return 'Done downloading'

	#print(driver.find_element(By.TAG_NAME, 'button').click())

	# Clicking on it should be simple
	# print(soup.find_all("a", class_ = "dw-data-link"))


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