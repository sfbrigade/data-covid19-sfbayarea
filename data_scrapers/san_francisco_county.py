#!/usr/bin/env python3
import requests
import json
from typing import Dict

<<<<<<< HEAD:data_scrapers/san_francisco_county.py
<<<<<<< HEAD:data_scrapers/san_francisco_county.py
# API endpoints
=======
#EL: get just the AC columns in dte order. Return the latest date as the cumulative case numbers.
=======
>>>>>>> Fetch Alameda county cases and deaths into pandas object:county-scrapers/san-francisco-county.py
# API endpoints 
>>>>>>> Alameda - fetch age, gender, race:county-scrapers/san-francisco-county.py
age_gender_url = 'https://data.sfgov.org/resource/sunc-2t3k.json'
race_ethnicity_url = 'https://data.sfgov.org/resource/vqqm-nsqg.json'
transmission_url = 'https://data.sfgov.org/resource/tvq9-ec9w.json'
hospitalizations_url = 'https://data.sfgov.org/resource/nxjg-bhem.json'
tests_url = 'https://data.sfgov.org/resource/nfpa-mg4g.json'

def get_json(url, query=''):
    """
    Fetches data from url with optional query in JSON format
    and parses it into a dict
    """
    raw_response = requests.get(url + query)
    parsed_json = json.loads(raw_response.content)
    return parsed_json

# Confirmed cases by age and gender
def get_age_gender_json() -> Dict:
    """fetch age x gender data"""
    return get_json(age_gender_url)

def get_age_json() -> Dict:
    """group data by age"""
    age_query = '?$select=age_group, sum(confirmed_cases)&$order=age_group&$group=age_group'
    return get_json(age_gender_url, age_query)

def get_gender_json() -> Dict:
    """group data by gender"""
    gender_query = '?$select=gender, sum(confirmed_cases)&$group=gender'
    return get_json(age_gender_url, gender_query)

#Confirmed cases by race and ethnicity
def get_race_ethnicity_json() -> Dict:
    """ fetch race x ethnicity data """
    return get_json(race_ethnicity_url)

def get_race_json() -> Dict:
    """ group data by race"""
    race_query = '?$select=race, sum(confirmed_cases)&$group=race'
    return get_json(race_ethnicity_url, race_query)

def get_ethnicity_json() -> Dict:
    """ group data by ethnicity"""
    ethnicity_query = '?$select=ethnicity, sum(confirmed_cases)&$group=ethnicity'
    return get_json(race_ethnicity_url, ethnicity_query)

# Confirmed Cases and Deaths by Date and Transmission
def get_cases_and_deaths() -> Dict:
    """Get total confirmed cases and deaths by summing over transmission table.
    Note that total confrimed cases excludes deaths."""
    query = '?$select=case_disposition, sum(case_count)&$group=case_disposition'
    return get_json(transmission_url + query)

def get_date_transmission_json() -> Dict:
    """Get cases by date, transmission, and disposition; order by date ascending."""
    # date_order_query = '?$order=date'
    return get_json(transmission_url)

def get_transmission_json() -> Dict:
    """Group data by transmission category"""
    transmission_query = '?$select=transmission_category, sum(case_count)&$group=transmission_category'
    return get_json(transmission_url, transmission_query)

# COVID+ patients from all SF hospitals in ICU vs. acute care, by date
def get_hospitalization_json() -> Dict:
    """Get number of COVID+ patients by bed category (ICU or regular), order by date ascending."""
    date_order_query = '?$order=reportdate'
    return get_json(hospitalizations_url + date_order_query)

def get_icu_beds() -> Dict:
    """group data by bed type: ICU or regular"""
    icu_query = '?$select=dphcategory, sum(patientcount)&$group=dphcategory'
    return get_json(hospitalizations_url + icu_query)

# Daily count of tests with count and percent of positive tests
def get_tests() -> Dict:
    """Get tests by day, order by date ascending"""
    date_order_query = '?$order=result_date'
    return get_json(tests_url + date_order_query)

def get_test_totals() -> Dict:
    """Get total tests and total number of positive tests, to date"""
    total_test_query = '?$select=sum(tests) as tests'
    tests = get_json(tests_url + total_test_query)
    total_positives_query = '?$select=sum(pos) as total_positives'
    positives = get_json(tests_url + total_positives_query)
    tests[0].update(positives[0])
    return tests

if __name__ == '__main__':
    """ When run as a script, logs grouped data queries to console"""
    print("Total cases and deaths: \n", json.dumps(get_cases_and_deaths(), indent=4))
    # print("Cases by age:\n", json.dumps(get_age_json(), indent=4))
    # print("Cases by gender:\n", json.dumps(get_gender_json(), indent=4))
    # print("Cases by race:\n", json.dumps(get_race_json(), indent=4))
    # print("Cases by ethnicity:\n", json.dumps(get_ethnicity_json(), indent=4))
    # print("Cases by transmission\n", json.dumps(get_transmission_json(), indent=4))
    # print("Cases by ICU beds\n", json.dumps(get_icu_beds(), indent=4))
    # print("Total tests\n", json.dumps(get_test_totals(), indent=4))
