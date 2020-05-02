#!/usr/bin/env python3
import requests
import json
import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta, timezone

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
    update = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc)

    # get cases, deaths, and demographics data
    cases_deaths_series = get_timeseries()
    demo_totals, counts_lt_10 = get_demographics()

    out = {
        "name": "Alameda County",
        "update_time": update.isoformat(timespec='minutes'),
        "source_url": "https://data.acgov.org/search?source=alameda%20county%20public%20health%20department&tags=covid-19",
        "meta_from_source": "Notes and disclaimers: The City of Berkeley and Alameda County(minus Berkeley) are separate local health jurisdictions(LHJs). We are showing data for each separately and together. The numbers for the Alameda County LHJ and the Berkeley LHJ come from the state’s communicable disease tracking database, CalREDIE. These data are updated daily, with cases sometimes reassigned to other LHJs and sometimes changed from a suspected to a confirmed case, so counts for a particular date in the past may change as information is updated in CalREDIE. Dates reflect the date created in CalREDIE. Furthermore, we review our data routinely and adjust to ensure its integrity and that it most accurately represents the full picture of COVID-19 cases in our county. The case rates likely reflect more the availability of testing than the actual disease burden. For instance, Hayward and places near Hayward have the highest case rates likely because of the availability of drive-through testing. Berkeley LHJ cases do not include two cases that were passengers of the Diamond Princess cruise.",
        "meta_from_baypd": "These datapoints have a value less than 10: " + ", ".join([item for item in counts_lt_10]),
        "series": {"cases": [], "deaths": [], "tests": []},
        "case_totals": {
            "gender": {"female": -1, "male": -1, "other": -1, "unknown": -1},
            "age_group": {},
            "race_eth": {"African_Amer": -1, "Asian": -1, "Latinx/Hispanic": -1, "Native_Amer": -1, "Multiple_Race": -1, 
                        "Other": -1, "Pacific Islander": -1, "White": -1, "Unknown": -1 },
            "transmission_cat": { "community": -1, "from_contact": -1, "unknown": -1 }
        },
        "death_totals": {
            "gender": {"female": -1, "male": -1, "other": -1, "unknown": -1 },
            "age_group": {},
            "race_eth": { "African_Amer": -1, "Asian": -1, "Latinx/Hispanic": -1, "Native_Amer": -1, "Multiple_Race": -1,
                        "Other": -1, "Pacific Islander": -1, "White": -1, "Unknown": -1},
            "underlying_cond": {},
            "transmission_cat": { "community": -1, "from_contact": -1, "unknown": -1 }
        },
    }

     # re-key series
    new_keys = ["date", "cases", "cumul_cases", "deaths", "cumul_deaths"]
    cases_deaths_series = [ dict(zip(new_keys, list(entry.values()) ) ) for entry in cases_deaths_series ]
    death_keys = ["date", "cases", "deaths", "cumul_deaths"]
    case_keys = ["date", "cases", "cumul_cases"]
    # parse series into cases and deaths
    out["series"]["cases"] = [ { k:v for k,v in entry.items() if k in case_keys } for entry in cases_deaths_series]
    out["series"]["deaths"] = [{k: v for k, v in entry.items() if k in death_keys} for entry in cases_deaths_series]

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

# Confirmed Cases and Deaths
def get_timeseries(dataframe = False) -> Dict: 
    """Fetch daily and cumulative cases and deaths by day
    Returns a .json by default. If dataframe set to True, returns a 
    pandas DataFrame."""

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
        obj['Date'] = "{}/{}/{}".format(year, month, day)
    
    if not dataframe:
        return features
    
    fields = parsed["fields"]
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
    print(get_county())
    # ac_timeseries = get_timeseries()
    # print("Timeseries cases and deaths: \n", ac_timeseries)
    # ac_cumulative = get_cases_and_deaths(ac_timeseries)
    # print("Cumulative cases and deaths: \n", ac_cumulative)
    # demographics = get_demographics(False)
    # print("Cases and deaths by demographics: \n", demographics)
