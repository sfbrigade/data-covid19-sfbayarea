#!/usr/bin/env python3
import requests
import json
from typing import List, Dict

def get_json() -> List[Dict]:
    """
    Fetches location-keyed data in JSON format from the CDS
    and parses it into a dict
    Since 8/31/2020, the CDS site has not been updating data.
    Seems the public site is busted but the data is still updating and
    available directly from the updated link below.
    Keep watching the issue: https://github.com/covidatlas/li/issues/606
    """
    corona_url = 'https://liproduction-reportsbucket-bhk8fnhv1s76.s3-us-west-1.amazonaws.com/v1/latest/timeseries-byLocation.json'
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

def get_county_data(county_names: List[str], data: List[Dict]) -> Dict:
    """
    Takes in a list of county names and maps the corresponding county data
    to that list
    """
    county_dicts = {}
    for county_data in data:
        if county_data['name'] in county_names:
            clean_county_data = {}
            county_name = county_data['countyName']
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
    'Solano County, California, United States',
    'Alameda County, California, United States',
    'Santa Clara County, California, United States',
    'San Francisco County, California, United States',
    'Contra Costa County, California, United States',
    'San Mateo County, California, United States',
    'Sonoma County, California, United States',
    'Napa County, California, United States',
    'Marin County, California, United States'
]
covid_data = pipeline(bay_area_counties)
print(json.dumps(covid_data, indent=4))
