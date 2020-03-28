#!/usr/bin/env python3
import requests
import json
from typing import List, Dict

def get_json() -> Dict:
    """
    Fetches location-keyed data in JSON format from the CDS
    and parses it into a dict
    """
    corona_url = 'https://coronadatascraper.com/timeseries-byLocation.json'
    raw_response = requests.get(corona_url)
    parsed_json = json.loads(raw_response.content)
    return parsed_json

def clean_dates(dates: Dict[str,Dict]) -> List[Dict]:
    """
    Takes in a dict of data where they key is a date and the value is a dict
    of the data for that date and returns a list of those dicts with the
    date as a value under the key 'date'
    """
    date_list = []
    for key in dates:
        val = dates[key]
        val['date'] = key
        date_list.append(val)
    return date_list

def get_county_data(county_names: List[str], data: Dict) -> Dict:
    """
    Takes in a list of county names and maps the corresponding county data
    to that list
    """
    county_dicts = {}
    for name in county_names:
        clean_county_data = {}
        county_data = data[name]
        county_name = county_data['county']
        clean_county_data['name'] = county_name
        clean_county_data['population'] = county_data['population']
        clean_county_data['cases'] = clean_dates(county_data['dates'])
        county_dicts[county_name] = clean_county_data
    return county_dicts

def pipeline(counties: List[str]) -> Dict[str, Dict]:
    """
    Puts all the above functions together to fetch data from the CDS
    and package it up
    """
    all_data = get_json()
    county_data = get_county_data(counties, all_data)
    return county_data

bay_area_counties = [
    'Solano County, CA, USA',
    'Alameda County, CA, USA',
    'Santa Clara County, CA, USA',
    'San Francisco County, CA, USA',
    'Contra Costa County, CA, USA',
    'San Mateo County, CA, USA',
    'Sonoma County, CA, USA',
    'Napa County, CA, USA',
    'Marin County, CA, USA'
]


# uncomment the lines below to log all of the scraped and cleaned data to the console
# covid_data = pipeline(bay_area_counties)
# print(json.dumps(covid_data, indent=4))
