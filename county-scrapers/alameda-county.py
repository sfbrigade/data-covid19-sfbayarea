#!/usr/bin/env python3
import requests
import json
import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta

# Note that we are using numbers for all of Alameda County, including Berkeley
# Open data landing page: https://data.acgov.org/search?source=alameda%20county%20public%20health%20department&tags=covid-19
# Endpoints:
cases_deaths = 'https://opendata.arcgis.com/datasets/7ea4fd9b8a1040a7b3815f2e0b5f92ba_0/FeatureServer/0/query'
demographics = 'https://opendata.arcgis.com/datasets/f218564293f9400a8296558e9325f265_0/FeatureServer/0/query'
cases_meta = 'https://services3.arcgis.com/1iDJcsklY3l3KIjE/arcgis/rest/services/AC_dates/FeatureServer/0?f=json'
demographics_meta = 'https://services3.arcgis.com/1iDJcsklY3l3KIjE/arcgis/rest/services/AC_geography/FeatureServer/0?f=json'

def get_county() -> Dict:
    """Fetch county data into standard .json format"""

    # fetch cases metadata
    cases_header = json.loads(requests.get(cases_meta).content)
    timestamp = cases_header["editingInfo"]["lastEditDate"]
    # convert timestamp to datetime object
    update = datetime.utcfromtimestamp(timestamp/1000)

    # get cases, deaths, and demographics data
    cases_deaths_series = get_timeseries(True)
    demo_totals, counts_lt_10 = get_demographics(True)

    header = {
        "name": "Alameda County",
        "update_date": update.strftime("%Y/%m/%d"),
        "update_time": update.strftime("%I:%M %p"),
        "source_url": "https://data.acgov.org/search?source=alameda%20county%20public%20health%20department&tags=covid-19",
        "meta_from_source": "",
        "meta_from_baypd": "These datapoints have value less than 10: " + ", ".join([item for item in counts_lt_10])
    }

    series = {
        "series": {
            "cases": {

            },
            "deaths": {

            },
            "tests": {

            }
        }
    }


# Confirmed Cases and Deaths
def get_timeseries(dataframe = False) -> Dict:
    """Fetch daily and cumulative cases and deaths by day
    Returns a .json by default. If dataframe set to True, returns a 
    pandas DataFrame."""

    # query API
    param_list = {'where':'0=0', 'resultType': 'none', 'outFields': 'OBJECTID,Date,AC_Cases,AC_CumulCases,AC_Deaths,AC_CumulDeaths', 'outSR': 4326,'orderByField': 'Date', 'f': 'json'}
    response = requests.get(cases_deaths, params=param_list)
    parsed = json.loads(response.content)
    features = [obj["attributes"] for obj in parsed['features']]
    
    # convert dates to 'yyyy/mm/dd'
    for obj in features:
        month, day, year = obj['Date'].split('/')
        if int(month) < 10:
            month = '0' + month
        obj['Date'] = "{}/{}/{}".format(year, month, day)
    
    if not dataframe:
        return json.dumps(features)
    
    fields = parsed["fields"]
    rows = [entry["OBJECTID"] for entry in features]
    cols = [f['name'] for f in parsed['fields']]
    dframe = pd.DataFrame(data=features, index=rows, columns=cols)
    return dframe

def get_cases_and_deaths(timeseries: pd.DataFrame): 
    """Get latest date entry for cumulative cases and deaths. 
    Since data was fetched to sort by date, the latest field will be the last entry. """    
    return timeseries.tail(1)

def get_demographics(dataframe = False) -> Dict:
    """Fetch cases and deaths by age, gender, race, ethnicity
    Returns a .json by default. If dataframe set to True, returns a pandas
    DataFrame."""
    param_list = {'where': '0=0', 'outFields': '*', 'outSR':4326, 'f':'json'}
    response = requests.get(demographics, params=param_list)
    parsed = json.loads(response.content)
    fields = parsed['fields']
    features = [obj['attributes'] for obj in parsed['features']]
    #make a list of all datapoints with value '<10'
    counts_lt_10 = []
    for row in features:
        if row['Geography'] == 'Alameda County':
            for key, val in row.items():
                if val == '<10':
                    counts_lt_10.append(key)

    if not dataframe:
        return json.dumps(features), counts_lt_10

    rows = [entry['OBJECTID'] for entry in features]
    cols = [f['name'] for f in parsed['fields']]
    dframe = pd.DataFrame(data=features, index=rows, columns=cols)
    return dframe, counts_lt_10

if __name__ == '__main__':
    """ When run as a script, logs data to console"""
    get_county()
    # ac_timeseries = get_timeseries()
    # print("Timeseries cases and deaths: \n", ac_timeseries)
    # ac_cumulative = get_cases_and_deaths(ac_timeseries)
    # print("Cumulative cases and deaths: \n", ac_cumulative)
    # demographics = get_demographics(True)
    # print("Cases and deaths by demographics: \n", demographics)
