# is there a way to get historical data
# is there a way to have a script click on the "download csv" files?
#!/usr/bin/env python3
import csv
import json
import numpy as np

# build csv parsing functionality first, then scrape the metadata, and then figure out how to download the CSVs (seleniuim)
# throw error when the button isn't correctly pressed
# do a final check 
def get_county_data():
	url = 'https://coronavirus.marinhhs.org/surveillance'
	case_csv = '/Users/angelakwon/Downloads/data-Eq6Es.csv'
	"""Main method for populating county data"""
	with open('data-covid19-sfbayarea/data-model.json') as template:
		model = json.load(template)

	#model['name'] = 
	#model['update_time'] = 
	model['source_url'] = url
	#model['meta_from_source'] = 
	# make sure to get the comments below the data
	#model['meta_from_baypd']
	model["series"]["cases"] = get_case_series(case_csv) 
	#cases - new cases for that day, cumul_cases - total number of cases which have occurred
	#model["series"]["deaths"] =  get_death_series()
	#model["series"]["tests"] = get_test_series()

	#print(model)

def get_case_series(csv_):
	#series = [{key:[]} for key in ["date", "cases", "cumul_cases"]]
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
	# is it ok to assume they will be the same value?
	for val, case_num in enumerate(case_history_diff):
		series[val]["cases"] = case_num
	print(series)
	# needs to return a list of dictionaries of time series

#def get_death_series(csv):


#def get_test_series():


#def get_case_totals_gender():

#def get_case_totals_age():

#def get_case_totals_race_eth():

#def get_case_totals_category():


#def get_death_totals_gender():

#def get_death_totals_age():

#def get_death_totals_race_eth():

#def get_death_totals_underlying():

#def get_death_totals_transmission():

# population totals

get_county_data()
# figure out a way to run the scraper through the command line 