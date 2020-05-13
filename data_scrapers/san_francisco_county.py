#!/usr/bin/env python3
import requests
import json
from typing import Dict

# API endpoints 
# landing page: https://data.sfgov.org/stories/s/San-Francisco-COVID-19-Data-and-Reports/fjki-2fab

RESOURCE_IDS = {'cases_deaths_transmission': 'tvq9-ec9w', 'age_gender': 'sunc-2t3k', 
                'race_eth': 'vqqm-nsqg', 'tests': 'nfpa-mg4g' }

metadata_url = 'https://data.sfgov.org/api/views/metadata/v1/'
data_url = 'https://data.sfgov.org/resource/'
age_gender_url = f"{data_url}{RESOURCE_IDS['age_gender']}.json"
race_ethnicity_url = f"{data_url}{RESOURCE_IDS['race_eth']}.json"
transmission_url = f"{data_url}{RESOURCE_IDS['cases_deaths_transmission']}.json"
tests_url = f"{data_url}{RESOURCE_IDS['tests']}.json"
hospitalizations_url = 'https://data.sfgov.org/resource/nxjg-bhem.json' # will be deprecated 

def get_county() -> Dict:
    """Main method for populating county data .json"""

    # Load data model template into a local dictionary called 'out'.
    with open('./data_models/data_model.json') as template:
        out = json.load(template)

    # fetch metadata
    meta_from_source = ''
    update_times = []
    for k,v in RESOURCE_IDS.items():
        url = f"{metadata_url}{v}.json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        meta_from_source += data["description"] + '\n\n'
        update_times.append(data["dataUpdatedAt"])

    # populate headers
    out["name"] = "San Francisco County"
    out["source_url"] = "https://data.sfgov.org/stories/s/San-Francisco-COVID-19-Data-and-Reports/fjki-2fab"
    out["update_time"] =  sorted(update_times)[0] # get earliest update time 
    out["meta_from_source"] =  meta_from_source
    out["meta_from_baypd"] =  "SF county only reports tests with positive or negative results, excluding pending tests. The following datapoints are not directly reported, and were calculated by BayPD using available data: cumulative cases, cumulative deaths, cumulative positive tests, cumulative negative tests, cumulative total tests."
    
      # get timeseries and demographic totals
    out["series"] = get_timeseries()
    demo_totals = get_demographics(out)
    out.update(demo_totals)

    return out


def get_timeseries() -> Dict:
    """
    Returns the dictionary value for "series": {"cases":[], "deaths":[], "tests":[]}.
    To create a DataFrame from this dictionary, run
    'pd.DataFrame(get_timeseries())'
    """
    out_series = {"cases": [], "deaths": [], "tests":[] }  # dictionary structure for time_series
    out_series["cases"] = get_cases_series()
    out_series["deaths"] = get_deaths_series()
    out_series["tests"] = get_tests_series()
    return out_series

# Confirmed Cases and Deaths by Date and Transmission
# Note that cumulative totals are not directly reported, we are summing over the daily reported numbers
def get_cases_series() -> Dict:
    """Get cases timeseries, sum over transmision cat by date"""
    params = { 'case_disposition':'Confirmed','$select':'date,sum(case_count) as cases', '$group':'date', '$order':'date'}   
    response = requests.get(transmission_url, params=params)
    response.raise_for_status()
    cases_series = response.json()
    # convert date from ISO string to 'yyyy-mm-dd'. convert number strings to int.
    # calculate daily cumulative
    cumul = 0
    for entry in cases_series:
        entry["date"] = entry["date"][0:10]
        entry["cases"] = int(entry["cases"])
        cumul += entry["cases"]
        entry["cumul_cases"] = cumul
    return cases_series

def get_deaths_series() -> Dict:
    """Get  deaths timeseries, sum over transmision cat by date"""
    params = {'case_disposition': 'Death',
              '$select': 'date,sum(case_count) as deaths', '$group': 'date', '$order': 'date'}
    response = requests.get(transmission_url, params=params)
    response.raise_for_status()
    death_series = response.json()
    # convert date from ISO string to 'yyyy-mm-dd'. convert number strings to int.
    # calculate daily cumulative
    cumul = 0
    for entry in death_series:
        entry["date"] = entry["date"][0:10]
        entry["deaths"] = int(entry["deaths"])
        cumul += entry["deaths"]
        entry["cumul_deaths"] = cumul
    return death_series


# Daily count of tests with count of positive tests
# Note that SF county does not include pending tests, and does not directly report negative tests or cumulative tests.
def get_tests_series() -> Dict:
    """Get tests by day, order by date ascending"""
    test_series = [] # copy the dictionary structure of an entry in the tests series
    date_order_query = '?$order=result_date' 
    response = requests.get(tests_url + date_order_query)
    response.raise_for_status()
    series = response.json()

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


def get_demographics(out:Dict) -> Dict:
    """
    Fetch cases by age, gender, race_eth. Fetch cases by transmission category
    Returns the dictionary value for {"cases_totals": {}, "death_totals":{}}.
    Note that SF does not provide death totals, so these datapoints will be -1.
    To crete a DataFrame from the dictionary, run 'pd.DataFrame(get_demographics())'
    """
    # copy dictionary structure of global 'out' dictionary to local variable
    demo_totals = {"case_totals": out["case_totals"], "death_totals": out["death_totals"]}
    demo_totals["case_totals"]["gender"] = get_gender_table()
    demo_totals["case_totals"]["age_group"] = get_age_table()
    demo_totals["case_totals"]["transmission_cat"] = get_transmission_table()
    demo_totals["case_totals"]["race_eth"] = get_race_eth_table()
    return demo_totals

def get_age_table() -> Dict:
    """Get cases by age"""
    age_query = '?$select=age_group, sum(confirmed_cases)&$order=age_group&$group=age_group'
    response = requests.get(age_gender_url + age_query)
    response.raise_for_status()
    data = response.json()
    age_table = dict()
    for entry in data:
        k = entry["age_group"]
        v = int(entry["sum_confirmed_cases"])
        age_table[k] = v
    return age_table

def get_gender_table() -> Dict:
    """Get cases by gender"""
    # Dict of source_label:target_label for re-keying.
    # Note: non cis genders not currently reported 
    GENDER_KEYS = {"Female": "female", "Male": "male",
                   "Unknown": "unknown"}
    gender_query = '?$select=gender, sum(confirmed_cases)&$group=gender'
    response = requests.get(age_gender_url + gender_query)
    response.raise_for_status()
    data = response.json()   
    # re-key
    gender_data = dict()
    for entry in data:
        k = GENDER_KEYS[ entry["gender"] ]
        gender_data[k] = entry["sum_confirmed_cases"]
    return gender_data

def get_transmission_table() -> Dict:
    """Get cases by transmission category"""
    # Dict of source_label:target_label for re-keying
    TRANSMISSION_KEYS = { "Community": "community", "From Contact": "from_contact", "Unknown": "unknown" }
    cat_query = '?$select=transmission_category, sum(case_count)&$group=transmission_category'
    response = requests.get(transmission_url + cat_query)
    response.raise_for_status()
    data = response.json()
    # re-key
    transmission_data = dict()
    for entry in data:
        k = TRANSMISSION_KEYS[ entry["transmission_category"] ]
        transmission_data[k] = int(entry["sum_case_count"])
    return transmission_data

# Confirmed cases by race and ethnicity
# Note that SF reporting race x ethnicty requires special handling
# "In the race/ethnicity data shown below, the "Other” category 
# includes those who identified as Other or with a race/ethnicity that does not fit the choices collected. 
# The “Unknown” includes individuals who did not report a race/ethnicity to their provider, 
# could not be contacted, or declined to answer."

def get_race_eth_table() -> Dict:
    """ fetch race x ethnicity data """
    response = requests.get(race_ethnicity_url)
    response.raise_for_status()
    # Dict of target_label : source_label for re-keying.
    # Note: Native_Amer not currently reported
    RACE_ETH_KEYS = {"Latinx_or_Hispanic": "Hispanic or Latino", "Asian": "Asian", "African_Amer": "Black or African American",
                 "White": "White", "Pacific_Islander": "Native Hawaiian or Other Pacific Islander", "Multiple_Race": "Multiple Race",
                 "Other": "Other", "Unknown": "Unknown"}
    data = response.json()
    # re-key and aggregate to flatten race x ethnicity
    race_eth_data: Dict[str,int] = { k:0 for k in RACE_ETH_KEYS.keys() } # initalize all categories to 0 for aggregating

    for item in data: # iterate through all race x ethnicity objects
        cases = int(item["confirmed_cases"])
        cols = item.keys()

        # handle unknown
        # sum over only items for which BOTH race and ethnicity are Unknown, or one is Unknown and the other is not reported
        if "race" in cols and "ethnicity" in cols:
            if item["race"] == "Unknown" and item["ethnicity"] == "Unknown": # both race and ethnicity are Unknown
                race_eth_data["Unknown"] += cases
        elif "ethnicity" in cols and item["ethnicity"] == "Unknown": # or, race not reported and ethnicity is unknown
            race_eth_data["Unknown"] += cases
        elif "race" in cols and item["race"] == "Unknown": # or, ethnicity not reported and race is unknown
            race_eth_data["Unknown"] += cases
        
        # sum over 'Hispanic or Latino', all races
        if "ethnicity" in cols and item["ethnicity"] == "Hispanic or Latino":
            race_eth_data["Latinx_or_Hispanic"] += cases
        
        # sum over all known races
        if "race" in cols and item["race"] != "Unknown": 
            if item["race"] == "Other":  # except for race = Other, ethnicity = Hispanic or Latino; exclude Other/Hispanic Latino from Other
                if "ethnicity" in cols and item["ethnicity"] != "Hispanic or Latino": 
                    race_eth_data["Other"] += cases
            else:
                for k,v in RACE_ETH_KEYS.items(): # look up this item's re-key
                    if v == item["race"]:
                        race_eth_data[k] += cases

    return race_eth_data

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
    """ When run as a script, logs data to console"""
    print(json.dumps(get_county(), indent=4))
