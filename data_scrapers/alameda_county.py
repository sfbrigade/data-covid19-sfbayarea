#!/usr/bin/env python3
import requests
import urllib.request
from bs4 import BeautifulSoup
import json
from typing import List, Dict
from datetime import datetime, timedelta, timezone

# Note that we are using numbers for all of Alameda County, including Berkeley
# Open data landing page: https://data.acgov.org/search?source=alameda%20county%20public%20health%20department&tags=covid-19
    # Getting strted with the ArcGIS REST API: https://developers.arcgis.com/rest/services-reference/get-started-with-the-services-directory.htm
    # Services reference for Layer: https://developers.arcgis.com/rest/services-reference/layer-feature-service-.htm

# Endpoints:
cases_deaths = 'https://opendata.arcgis.com/datasets/7ea4fd9b8a1040a7b3815f2e0b5f92ba_0/FeatureServer/0/query'
demographics = 'https://opendata.arcgis.com/datasets/f218564293f9400a8296558e9325f265_0/FeatureServer/0/query'
cases_meta = 'https://services3.arcgis.com/1iDJcsklY3l3KIjE/arcgis/rest/services/AC_dates/FeatureServer/0?f=json'
demographics_meta = 'https://services3.arcgis.com/1iDJcsklY3l3KIjE/arcgis/rest/services/AC_geography/FeatureServer/0?f=json'
dashboards = ['https://ac-hcsa.maps.arcgis.com/apps/opsdashboard/index.html#/1e0ac4385cbe4cc1bffe2cf7f8e7f0d9',
              'https://ac-hcsa.maps.arcgis.com/apps/opsdashboard/index.html#/332a092bbc3641bd9ec8373e7c7b5b3d']

def get_county() -> Dict:
    """Fetch county data into standard .json format"""

    # load data model template into a local dictionary
    with open('./data_scrapers/_data_model.json') as template:
        out = json.load(template)
    
    # populate dataset headers
    out["name"] = "Alameda County"
    out["source_url"] = "https://data.acgov.org/search?source=alameda%20county%20public%20health%20department&tags=covid-19"
    out["meta_from_source"] = get_notes()

    # fetch cases metadata, to get the timestamp
    response = json.loads(requests.get(cases_meta).content)
    response.raise_for_status()
    timestamp = response["editingInfo"]["lastEditDate"]
    # Raise an exception if a timezone is specified. If "dateFieldsTimeReference" is present, we need to edit this scrapr to handle it. 
    # See: https://developers.arcgis.com/rest/services-reference/layer-feature-service-.htm#GUID-20D36DF4-F13A-4B01-AA05-D642FA455EB6
    if "dateFieldsTimeReference" in cases_header["editingInfo"] or "editFieldsInfo" in cases_header:
        raise FutureWarning("A timezone may now be specified in the metadata.")
    # convert timestamp to datetime object
    update = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc)
    out["update_time"] = update.isoformat()

    # get cases, deaths, and demographics data
    out["series"] = get_timeseries()


    demo_totals, counts_lt_10 = get_demographics()
    out["meta_from_baypd"] = "These datapoints have a value less than 10: " + ", ".join([item for item in counts_lt_10])

    # parse demographics
    # note: gender does not currently include other genders
    gender_keys = {"female": "Female", "male": "Male", "unknown": "Unknown_Sex"} # dict of target_label : source_label for re-keying
    race_keys = {"Latinx/Hispanic": "Hispanic/Latino", "Asian": "Asian", "African_Amer": "African_American/Black", 
                 "White":"White", "Pacific_Islander": "Pacific_Islander", "Native_Amer": "Native_American", "Multiple_Race": "Multirace", 
                 "Other": "Other_Race", "Unknown": "Unknown_Race"}
    
    # parse gender cases
    for k,v in gender_keys.items():
        out["case_totals"]["gender"][k] = demo_totals[v]
    # parse race cases and deaths
    for k, v in race_keys.items():
        out["case_totals"]["race_eth"][k] = demo_totals[v]
        out["death_totals"]["race_eth"][k] = demo_totals['Deaths\u2014' + v] # dashes are decoded as the escape sequence '\u2014'
    # get age cases
    out["case_totals"]["age_group"] = { k:v for k,v in demo_totals.items() if 'Age' in k}

    with open('./county_data/alameda_county.json', 'w', encoding = 'utf-8') as f:
        json.dump(out, f, ensure_ascii= False, indent=4)
        
    return json.dumps(out, indent=4) # for printing to console


# https: // services3.arcgis.com/1iDJcsklY3l3KIjE/arcgis/rest/services/COVID_Counts/FeatureServer/0/query?select = features & where = 0 = 0 & orderby = ObjectID & outFields = * & f = pjson
# Confirmed Cases and Deaths
def get_timeseries(dataframe = False) -> Dict: 
    """Fetch daily and cumulative cases and deaths by day
    Returns the dictionary value for "series": {"cases":[], "deaths":[]} by default.
    If dataframe set to True, returns a pandas DataFrame."""

    series = {"cases":[], "deaths":[]} # dictionary holding the timeseries for cases and deaths

    # query API
    param_list = {'where':'0=0', 'resultType': 'none', 'outFields': 'Date,AC_Cases,AC_CumulCases,AC_Deaths,AC_CumulDeaths', 'outSR': 4326,'orderByField': 'Date', 'f': 'json'}
    response = requests.get(cases_deaths, params=param_list)
    parsed = json.loads(response.content)
    features = [obj["attributes"] for obj in parsed['features']]
    
    # convert dates to 'yyyy/mm/dd'
    for obj in features:
        month, day, year = obj['Date'].split('/')
        if int(month) < 10:
            month = '0' + month
        obj['Date'] = "{}-{}-{}".format(year, month, day)

    # re-key series
    new_keys = ["date", "cases", "cumul_cases", "deaths", "cumul_deaths"]
    re_keyed = [dict(zip(new_keys, list(entry.values())))
                           for entry in features]

    # parse series into cases and deaths
    death_keys = ["date", "cases", "deaths", "cumul_deaths"]
    case_keys = ["date", "cases", "cumul_cases"]
    
    series["cases"] = [{k: v for k, v in entry.items() if k in case_keys} for entry in re_keyed]
    series["deaths"] = [{k: v for k, v in entry.items() if k in death_keys} for entry in re_keyed]
    
    if not dataframe:
        return series
    
    fields = parsed["fields"]
    cols = [f['name'] for f in parsed['fields']]
    dframe = pd.DataFrame(data=series, index=rows, columns=cols)
    return dframe

def get_notes() -> str:
    """Scrape notes and disclaimers from dashboards."""
    notes = ""
    return notes

def get_demographics(dataframe = False) -> Dict:
    """Fetch cases and deaths by age, gender, race, ethnicity
    Returns a .json by default. If dataframe set to True, returns a pandas
    DataFrame."""
    param_list = {'where': "Geography='Alameda County'", 'outFields': '*', 'outSR':4326, 'f':'json'}
    response = requests.get(demographics, params=param_list)
    parsed = response.json()
    fields = parsed['fields']
    data = parsed['features'][0]['attributes']
    #make a list of all datapoints with value '<10'
    # due to some quirk in the json decoding, dashes are stored as the escape sequence '\u2014'
    counts_lt_10 = []
    for key, val in data.items():
        key = key.replace('\u2014', '-')
        if val == '<10':
            counts_lt_10.append(key)
    if not dataframe:
        return data, counts_lt_10

    cols = [f['name'] for f in parsed['fields']]
    dframe = pd.DataFrame(data=data, index=rows, columns=cols)
    return dframe, counts_lt_10




if __name__ == '__main__':
    """ When run as a script, logs data to console"""
    # print(get_county())
    print(get_notes())
    # ac_timeseries = get_timeseries()
    # print("Timeseries cases and deaths: \n", ac_timeseries)
    # demographics = get_demographics(False)
    # print("Cases and deaths by demographics: \n", demographics)
