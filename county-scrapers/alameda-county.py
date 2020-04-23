#!/usr/bin/env python3
import requests
import json
import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta

# Note that we are using numbers for all of Alameda County, including Berkeley
# Open data landing page: https://data.acgov.org/search?source=alameda%20county%20public%20health%20department&tags=covid-19
# API endpoints: 
cases_deaths = 'https://opendata.arcgis.com/datasets/7ea4fd9b8a1040a7b3815f2e0b5f92ba_0/FeatureServer/0/query'
demographics = 'https://opendata.arcgis.com/datasets/f218564293f9400a8296558e9325f265_0/FeatureServer/0/query'

# Confirmed Cases and Deaths
def get_timeseries() -> pd.DataFrame:
    """Fetch daily and cumulative cases and deaths by day"""
    param_list = {'where':'0=0', 'resultType': 'none', 'outFields': 'OBJECTID,Date,AC_Cases,AC_CumulCases,AC_Deaths,AC_CumulDeaths', 'outSR': 4326,'orderByField': 'Date', 'f': 'json'}
    response = requests.get(cases_deaths, params=param_list)
    parsed = json.loads(response.content)
    fields = parsed["fields"]
    features = [obj["attributes"] for obj in parsed['features']]
    rows = [entry["OBJECTID"] for entry in features]
    
    # convert dates to 'yyyy/mm/dd'
    for obj in features:
        month, day, year = obj['Date'].split('/')
        if int(month) < 10:
            month = '0' + month
        obj['Date'] = "{}/{}/{}".format(year, month, day)

    cols = [f["name"] for f in parsed['fields']]
    dframe = pd.DataFrame(data=features, index=rows, columns=cols)
    return dframe

def get_cases_and_deaths(timeseries):
    """Get latest date entry for cumulative cases and deaths. Since data was fetched to sort by date, the latest field will be the last entry. """    
    return timeseries.tail(1)

def get_demographics() -> pd.DataFrame:
    """Fetch cases and deaths by age, gender, race, ethnicity"""
    param_list = {'where': '0=0', 'outFields': '*', 'outSR':4326, 'f':'json'}
    response = requests.get(demographics, params=param_list)
    parsed = json.loads(response.content)
    fields = parsed['fields']
    features = [obj['attributes'] for obj in parsed['features']]
    rows = [entry['OBJECTID'] for entry in features]
    cols = [f['name'] for f in parsed['fields']]
    dframe = pd.DataFrame(data=features, index=rows, columns=cols)
    return dframe

if __name__ == '__main__':
    """ When run as a script, logs DataFrames to console"""
    ac_timeseries = get_timeseries()
    print("Timeseries cases and deaths: \n", ac_timeseries)
    ac_cumulative = get_cases_and_deaths(ac_timeseries)
    print("Cumulative cases and deaths: \n", ac_cumulative)
    demographics = get_demographics()
    print("Cases and deaths by demographics: \n", demographics)