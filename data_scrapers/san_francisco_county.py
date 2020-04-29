#!/usr/bin/env python3
import requests
import json
from typing import Dict

# API endpoints 
metadata_url = 'https://data.sfgov.org/api/views/metadata/v1/tvq9-ec9w/'
age_gender_url = 'https://data.sfgov.org/resource/sunc-2t3k.json'
race_ethnicity_url = 'https://data.sfgov.org/resource/vqqm-nsqg.json'
transmission_url = 'https://data.sfgov.org/resource/tvq9-ec9w.json'
hospitalizations_url = 'https://data.sfgov.org/resource/nxjg-bhem.json'
tests_url = 'https://data.sfgov.org/resource/nfpa-mg4g.json'

def get_county() -> None:
    """ Write county data to .json in standard format."""
    metadata = json.loads(requests.get(metadata_url).content)
    update_time = metadata["dataUpdatedAt"]
    out = {
        "name": "San Francisco County",
        "update_time": update_time,
        "source_url": "https://data.sfgov.org/COVID-19/COVID-19-Cases-Summarized-by-Date-Transmission-and/tvq9-ec9w",
        "meta_from_source": "Transmission Category can be Community, Contact or Unknown. Unknowns may become known as more information becomes available about cases. " + 
                            "In the race/ethnicity data, the 'Other' category includes those who identified as 'Other' or with a race/ethnicity that does not fit the choices collected. " +
                            "The “Unknown” includes individuals who did not report a race/ethnicity to their provider, could not be contacted, or declined to answer. " +
                            "To date, no cases reported among trans women or trans men. " +
                            "Reported test results only include tests with a positive or negative result.",
        "meta_from_baypd": "",
        "series": {"cases": [], "deaths": [], "tests": []},
        "case_totals": {
            "gender": {"female": -1, "male": -1, "other": -1, "unknown": -1},
            "age_group": {},
            "race_eth": {"African_Amer": -1, "Asian": -1, "Latinx/Hispanic": -1, "Native_Amer": -1, "Multiple_Race": -1,
                         "Other": -1, "Pacific Islander": -1, "White": -1, "Unknown": -1},
            "transmission_cat": {"community": -1, "from_contact": -1, "unknown": -1}
        },
        "death_totals": {
            "gender": {"female": -1, "male": -1, "other": -1, "unknown": -1},
            "age_group": {},
            "race_eth": {"African_Amer": -1, "Asian": -1, "Latinx/Hispanic": -1, "Native_Amer": -1, "Multiple_Race": -1,
                         "Other": -1, "Pacific Islander": -1, "White": -1, "Unknown": -1},
            "underlying_cond": {},
            "transmission_cat": {"community": -1, "from_contact": -1, "unknown": -1}
        },
    }
    out["series"]["cases"] = get_cases_series()
    out["series"]["deaths"] = get_deaths_series()
    with open('./county_data/san_francisco_county.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=4)
    return json.dumps(out, indent=4)  # for printing to console


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
    get_county()
    # print("Total cases and deaths: \n", json.dumps(get_cases_and_deaths(), indent=4))
    # print("Cases by age:\n", json.dumps(get_age_json(), indent=4))
    # print("Cases by gender:\n", json.dumps(get_gender_json(), indent=4))
    # print("Cases by race:\n", json.dumps(get_race_json(), indent=4))
    # print("Cases by ethnicity:\n", json.dumps(get_ethnicity_json(), indent=4))
    # print("Cases by transmission\n", json.dumps(get_transmission_json(), indent=4))
    # print("Cases by ICU beds\n", json.dumps(get_icu_beds(), indent=4))
    # print("Total tests\n", json.dumps(get_test_totals(), indent=4))
