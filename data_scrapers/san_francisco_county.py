#!/usr/bin/env python3
import requests
import json
from typing import Dict

# API endpoints 
# landing page: https://data.sfgov.org/stories/s/San-Francisco-COVID-19-Data-and-Reports/fjki-2fab
metadata_url = 'https://data.sfgov.org/api/views/metadata/v1/tvq9-ec9w/'
age_gender_url = 'https://data.sfgov.org/resource/sunc-2t3k.json'
race_ethnicity_url = 'https://data.sfgov.org/resource/vqqm-nsqg.json'
transmission_url = 'https://data.sfgov.org/resource/tvq9-ec9w.json'
hospitalizations_url = 'https://data.sfgov.org/resource/nxjg-bhem.json'
tests_url = 'https://data.sfgov.org/resource/nfpa-mg4g.json'

# Load data model template into the 'out' dictionary. 'out' will be global to all methods.
with open('./data_scrapers/_data_model.json') as template:
    out = json.load(template)

def get_county() -> Dict:
    """Main method for populating the 'out' dictionary"""
    
    # fetch metadata
    response = requests.get(metadata_url)
    response.raise_for_status()
    metadata = json.loads(response.content)

    # populate headers
    out["name"]: "San Francisco County"
    out["source_url"]: "https://data.sfgov.org/stories/s/San-Francisco-COVID-19-Data-and-Reports/fjki-2fab"
    out["update_time"]: metadata["dataUpdatedAt"]
    out["meta_from_source"]: metadata["description"] # EL: add descriptions from other endpoints here
    out["meta_from_baypd"]: "SF county only reports tests with positive or negative results, excluding pending tests. The following datapoints are not directly reported, and were calculated by BayPD using available data: cumulative cases, cumulative deaths, cumulative positive tests, cumulative negative tests, cumulative total tests."
    
      # get timeseries and demographic totals
    out["series"] = get_timeseries()
    demo_totals = get_demographics()
    out["case_totals"], out["death_totals"] = demo_totals["case_totals"], demo_totals["death_totals"]
     
    return out


def get_timeseries() -> Dict:
    """
    Returns the dictionary value for "series": {"cases":[], "deaths":[], "tests":[]}.
    To create a DataFrame from this dictionary, run
    'pd.DataFrame(get_timeseries())'
    """
    out_series = out["series"] # copy dictionary structure for series
    out_series["cases"] = get_cases_series()
    out_series["deaths"] = get_deaths_series()
    out_series["tests"] = get_tests_series()
    return out_series

# Confirmed Cases and Deaths by Date and Transmission
# Note that cumulative totals are not directly reported,
# we are summing over the daily reported numbers
def get_cases_series() -> Dict:
    """Get cases timeseries, sum over transmision cat by date"""
    params = { 'case_disposition':'Confirmed','$select':'date,sum(case_count) as cases', '$group':'date', '$order':'date'}   
    out = json.loads(requests.get(transmission_url, params = params).content)
    # convert date from ISO string to 'yyyy/mm/dd'. convert number strings to int.
    # calculate daily cumulative
    cumul = 0
    for entry in out:
        entry["date"] = entry["date"][0:10].replace('-','/')
        entry["cases"] = int(entry["cases"])
        cumul += entry["cases"]
        entry["cumul_cases"] = cumul
    return out

def get_deaths_series() -> Dict:
    """Get  deaths timeseries, sum over transmision cat by date"""
    params = {'case_disposition': 'Death',
              '$select': 'date,sum(case_count) as deaths', '$group': 'date', '$order': 'date'}
    out = json.loads(requests.get(transmission_url, params=params).content)
    # convert date from ISO string to 'yyyy/mm/dd'. convert number strings to int.
    # calculate daily cumulative
    cumul = 0
    for entry in out:
        entry["date"] = entry["date"][0:10].replace('-', '/')
        entry["deaths"] = int(entry["deaths"])
        cumul += entry["deaths"]
        entry["cumul_deaths"] = cumul
    return out


# Daily count of tests with count and percent of positive tests
def get_tests_series() -> Dict:
    """Get tests by day, order by date ascending"""
    test_series = [] # copy the dictionary structure of an entry in the tests series
    date_order_query = '?$order=result_date' 
    response = requests.get(tests_url + date_order_query)
    response.raise_for_status()
    series = json.loads(response.content)

    # parse source series into out series, calculating cumulative values
    cumul_tests, cumul_pos, cumul_neg = 0,0,0
    for entry in series:
        out_entry = dict()
        out_entry["date"] = entry["result_date"][0:10]
        out_entry["tests"] = int(entry["tests"])
        out_entry["positive"] = int(entry["pos"])
        out_entry["negative"] = out_entry["tests"] - out_entry["positive"]
        # calculate cumulative values
        cumul_tests += out_entry["tests"]
        cumul_pos += out_entry["positive"]
        cumul_neg += out_entry["negative"]
        out_entry["cumul_tests"] = cumul_tests
        out_entry["cumul_pos"] = cumul_pos
        out_entry["cumul_neg"] = cumul_neg
        test_series.append(out_entry)
    return test_series



# Confirmed cases by age and gender
def get_age_gender_json() -> Dict:
    """fetch age x gender data"""
    return json.loads(requests.get(age_gender_url))

def get_age_json() -> Dict:
    """group data by age"""
    age_query = '?$select=age_group, sum(confirmed_cases)&$order=age_group&$group=age_group'
    return json.loads(requests.get(age_gender_url + age_query))

def get_gender_json() -> Dict:
    """group data by gender"""
    gender_query = '?$select=gender, sum(confirmed_cases)&$group=gender'
    return json.loads(requests.get(age_gender_url + gender_query))


# Confirmed cases by race and ethnicity
# Note that SF reporting race x ethnicty requires special handling

# In the race/ethnicity data shown below, the "Other” category 
# includes those who identified as Other or with a race/ethnicity that does not fit the choices collected. 
# The “Unknown” includes individuals who did not report a race/ethnicity to their provider, 
# could not be contacted, or declined to answer.
# Sum over race categories, except for unknown. 
# Sum over Hispanic/Latino (all races). "Unknown" should only be unknown race & 
# unknown ethnicity, or, if no race, unknown ethnicity

def get_race_ethnicity_json() -> Dict:
    """ fetch race x ethnicity data """
    return json.loads(requests.get(race_ethnicity_url))




# we probably won't use the transmission timeseries
def get_date_transmission_json() -> Dict:
    """Get cases by date, transmission, and disposition; order by date ascending."""
    date_order_query = '?$order=date'
    return json.loads(requests.get(transmission_url+date_order_query))

def get_transmission_json() -> Dict:
    """Group data by transmission category"""
    cat_query = '?$select=transmission_category, sum(case_count)&$group=transmission_category'
    return json.loads(requests.get(transmission_url + cat_query))



# COVID+ patients from all SF hospitals in ICU vs. acute care, by date
# Note: this source will be superseded by data from CHHS
def get_hospitalization_json() -> Dict:
    """Get number of COVID+ patients by bed category (ICU or regular), order by date ascending."""
    date_order_query='?$order=reportdate'
    return get_json(hospitalizations_url + date_order_query)
def get_icu_beds() -> Dict:
    """group data by bed type: ICU or regular"""
    icu_query='?$select=dphcategory, sum(patientcount)&$group=dphcategory'
    return get_json(hospitalizations_url + icu_query)

if __name__ == '__main__':
    """ When run as a script, logs grouped data queries to console"""
    print(json.dumps(get_timeseries(), indent=4))
