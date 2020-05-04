#!/usr/bin/env python3
import requests
import urllib.request
from bs4 import BeautifulSoup
import json
import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import re
import os

# Note that we are using numbers for all of Alameda County, including Berkeley
# Running this scraper requires a Firefox webdriver. The macos Firefox driver, geckodriver, is stored in ./env/bin
# This is the open data landing page: https://data.acgov.org/search?source=alameda%20county%20public%20health%20department&tags=covid-19
    # Getting strted with the ArcGIS REST API: https://developers.arcgis.com/rest/services-reference/get-started-with-the-services-directory.htm
    # Services reference for Layer: https://developers.arcgis.com/rest/services-reference/layer-feature-service-.htm

# URLs and API endpoints:
landing_page = "https://data.acgov.org/search?source=alameda%20county%20public%20health%20department&tags=covid-19"
cases_deaths = 'https://opendata.arcgis.com/datasets/7ea4fd9b8a1040a7b3815f2e0b5f92ba_0/FeatureServer/0/query'
demographics_cases = 'https://services3.arcgis.com/1iDJcsklY3l3KIjE/arcgis/rest/services/AC_cases/FeatureServer/0/query'
demographics_deaths = 'https://services3.arcgis.com/1iDJcsklY3l3KIjE/arcgis/rest/services/AC_deaths_rates/FeatureServer/0/query'
cases_meta = 'https://services3.arcgis.com/1iDJcsklY3l3KIjE/arcgis/rest/services/AC_dates/FeatureServer/0?f=json'
demographics_meta = 'https://services3.arcgis.com/1iDJcsklY3l3KIjE/arcgis/rest/services/AC_geography/FeatureServer/0?f=json'
dashboards = ['https://ac-hcsa.maps.arcgis.com/apps/opsdashboard/index.html#/1e0ac4385cbe4cc1bffe2cf7f8e7f0d9',
              'https://ac-hcsa.maps.arcgis.com/apps/opsdashboard/index.html#/332a092bbc3641bd9ec8373e7c7b5b3d']



def get_county() -> Dict:
    """Main method for populating the 'out' dictionary"""
    
    # Load data model template into a local dictionary called 'out'.
    with open('./data_scrapers/_data_model.json') as template:
        out = json.load(template)
    
    # populate dataset headers
    out["name"] = "Alameda County"
    out["source_url"] = landing_page
    out["meta_from_source"] = get_notes()

    # fetch cases metadata, to get the timestamp
    response = requests.get(cases_meta)
    response.raise_for_status()
    cases_header = json.loads(response.text)
    timestamp = cases_header["editingInfo"]["lastEditDate"]
    # Raise an exception if a timezone is specified. If "dateFieldsTimeReference" is present, we need to edit this scrapr to handle it. 
    # See: https://developers.arcgis.com/rest/services-reference/layer-feature-service-.htm#GUID-20D36DF4-F13A-4B01-AA05-D642FA455EB6
    if "dateFieldsTimeReference" in cases_header["editingInfo"] or "editFieldsInfo" in cases_header:
        raise FutureWarning("A timezone may now be specified in the metadata.")
    # convert timestamp to datetime object
    update = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc)
    out["update_time"] = update.isoformat()

    # get cases, deaths, and demographics data
    out["series"] = get_timeseries()
    demo_totals, counts_lt_10 = get_demographics(out)
    out["case_totals"], out["death_totals"] = demo_totals["case_totals"], demo_totals["death_totals"]
    out["meta_from_baypd"] = "These datapoints have a value less than 10: " + ", ".join([item for item in counts_lt_10])
    return out


# Confirmed Cases and Deaths
def get_timeseries() -> Dict: 
    """Fetch daily and cumulative cases and deaths by day
    Returns the dictionary value for "series": {"cases":[], "deaths":[]}.
    To create a DataFrame from this dictionary, run
    'pd.DataFrame(get_timeseries())'
    """

    series = {"cases":[], "deaths":[]} # dictionary holding the timeseries for cases and deaths

    # query API
    param_list = {'where':'0=0', 'resultType': 'none', 'outFields': 'Date,AC_Cases,AC_CumulCases,AC_Deaths,AC_CumulDeaths', 'outSR': 4326,'orderByField': 'Date', 'f': 'json'}
    response = requests.get(cases_deaths, params=param_list)
    response.raise_for_status()
    parsed = json.loads(response.content)
    features = [obj["attributes"] for obj in parsed['features']]
    
    # convert dates
    for obj in features:
        month, day, year = obj['Date'].split('/')
        if int(month) < 10:
            month = '0' + month
        if int(day) < 10:
            day = '0' + day
        obj['Date'] = "{}-{}-{}".format(year, month, day)

    # re-key series
    new_keys = ["date", "cases", "cumul_cases", "deaths", "cumul_deaths"]
    re_keyed = [dict(zip(new_keys, list(entry.values())))
                           for entry in features]

    # parse series into cases and deaths
    death_keys = ["date", "deaths", "cumul_deaths"]
    case_keys = ["date", "cases", "cumul_cases"]
    series["cases"] = [{k: v for k, v in entry.items() if k in case_keys} for entry in re_keyed]
    series["deaths"] = [{k: v for k, v in entry.items() if k in death_keys} for entry in re_keyed]

    return series

def get_notes() -> str:
    """Scrape notes and disclaimers from dashboards."""
    notes = ""
    driver = webdriver.Firefox()
    driver.implicitly_wait(30)
    for url in dashboards:
        driver.get(url)
        soup = BeautifulSoup(driver.page_source,'lxml')
        for p_tag in soup.find_all('p'):
            if 'Notes' in p_tag.get_text():
                notes += p_tag.get_text().strip()
    return notes

def get_demographics(out:Dict) -> (Dict, List):
    """Fetch cases and deaths by age, gender, race, ethnicity
    Returns the dictionary value for {"cases_totals": {}, "death_totals":{}}, as well as a list of 
    strings describing datapoints that have a value of "<10". 
    To crete a DataFrame from the dictionary, run 'pd.DataFrame(get_demographics()[0])' 
    Note that the DataFrame will convert the "<10" strings to NaN. """

    param_list = {'where': "Geography='Alameda County'", 'outFields': '*', 'outSR':4326, 'f':'json'}
    response = requests.get(demographics, params=param_list)
    #response.raise_for_status()
    parsed = response.json()
    fields = parsed['fields']
    data = parsed['features'][0]['attributes']

    # copy dictionary structure of 'out' dictionary to local variable
    demo_totals = { "case_totals": out["case_totals"], "death_totals": out["death_totals"]} 

    # Parse and re-key
    # note: gender does not currently include other genders
    # dict of target_label : source_label for re-keying
    gender_keys = {"female": "Female", "male": "Male", "unknown": "Unknown_Sex"}
    race_keys = {"Latinx_or_Hispanic": "Hispanic/Latino", "Asian": "Asian", "African_Amer": "African_American/Black",
                 "White": "White", "Pacific_Islander": "Pacific_Islander", "Native_Amer": "Native_American", "Multiple_Race": "Multirace",
                 "Other": "Other_Race", "Unknown": "Unknown_Race"}

    # parse gender cases
    for k, v in gender_keys.items():
        demo_totals["case_totals"]["gender"][k] = data[v]
    # parse race cases and deaths
    for k, v in race_keys.items():
        demo_totals["case_totals"]["race_eth"][k] = data[v]
        # dashes are decoded as the escape sequence '\u2014'
        demo_totals["death_totals"]["race_eth"][k] = data['Deaths\u2014' + v]
    # get age cases
    demo_totals["case_totals"]["age_group"] = {
        k: v for k, v in data.items() if 'Age' in k}

    #make a list of all datapoints with value '<10'
    counts_lt_10 = []
    for cat, cat_dict in demo_totals.items(): # cases, deaths
        for group, group_dict in cat_dict.items(): # dictionaries for age, race/eth
            for key, val in group_dict.items():
                if val == '<10':
                    counts_lt_10.append(cat + ' ' + key)
                else:
                    try:
                        int(val)
                    except ValueError:
                        raise ValueError(f'Non-integer value for {key}')
    return demo_totals, counts_lt_10

if __name__ == '__main__':
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(get_county(), indent=4))
