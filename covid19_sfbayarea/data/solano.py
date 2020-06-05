#!/usr/bin/env python3
import requests
import re
from bs4 import BeautifulSoup  # type: ignore
import json
from typing import List, Dict, Tuple
from datetime import datetime, timezone
from ..webdriver import get_firefox
from .utils import get_data_model

# URLs and API endpoints:
# data_url has cases, deaths, tests, and race_eth
data_url = "https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID_19_Survey_part_1_v2_new_public_view/FeatureServer/0/query"
# data2_url has age and gender
data2_url = "https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID_19_survey_part_2_v2_public_view/FeatureServer/0/query"
metadata_url = 'https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID_19_Survey_part_1_v2_new_public_view/FeatureServer/0?f=pjson'
dashboard_url = 'https://doitgis.maps.arcgis.com/apps/opsdashboard/index.html#/6c83d8b0a564467a829bfa875e7437d8'

def get_county() -> Dict:
    """Main method for populating county data .json"""

    # Load data model template into a local dictionary called 'out'.
    out = get_data_model()

    # populate dataset headers
    out["name"] = "Solano County"
    out["source_url"] = data_url
    out["meta_from_source"] = get_notes()
    out["meta_from_baypd"] = '\n'.join(["Solano County reports daily cumulative cases, deaths, and residents tested. In addition to cumulative cases each day, the county separately reports new daily confirmed cases.",
    "Solano reports cumulative tests, but does not report test results.",
    "Deaths by race/eth not currently reported.",
    "Multiple race and other race individuals are reported in the same category, which Bay PD is reporting as Multiple_Race.",
    "Cases by gender are ambiguous datapoints in the source data, and have not been confirmed by dashboards and reports released by the County to the public."])

    # fetch cases metadata, to get the timestamp
    response = requests.get(metadata_url)
    response.raise_for_status()
    metadata = response.json()
    timestamp = metadata["editingInfo"]["lastEditDate"]
    # Raise an exception if a timezone is specified. If "dateFieldsTimeReference" is present, we need to edit this scraper to handle it.
    # See: https://developers.arcgis.com/rest/services-reference/layer-feature-service-.htm#GUID-20D36DF4-F13A-4B01-AA05-D642FA455EB6
    if "dateFieldsTimeReference" in metadata["editFieldsInfo"]:
        raise FutureWarning("A timezone may now be specified in the metadata.")
    # convert timestamp to datetime object
    update = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc)
    out["update_time"] = update.isoformat()

    # get cases, deaths, and demographics data
    get_timeseries(out)
    get_gender_age(out)
    get_race_eth(out)

    return out


# Confirmed Cases and Deaths
def get_timeseries(out: Dict):
    """Fetch cumulative cases and deaths by day
    Note that Solano county reports daily cumumlative cases, deaths, and tests; and also separately reports daily new confirmed cases.
    Solano reports cumulative tests, but does not report test results.
    """

    # Link to map item: https://www.arcgis.com/home/webmap/viewer.html?url=https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID_19_Survey_part_1_v2_new_public_view/FeatureServer/0&source=sd
    # The table view of the map item is a helpful reference.

    # dictionary holding the timeseries for cases and deaths
    series: Dict[str, List] = {"cases": [], "deaths": [], "tests": [] }
    # Dictionary of 'source_label': 'target_label' for re-keying
    TIMESERIES_KEYS = {
        'date_reported': 'date',
        'new_cases_confirmed_today': 'cases',
        'cumulative_number_of_cases_on_t': 'cumul_cases',
        'total_deaths': 'cumul_deaths',
        'residents_tested': 'cumul_tests'
    }

    # query API for days where cumulative number of cases on the day > 0
    param_list = {'where': 'cumulative_number_of_cases_on_t>0', 'resultType': 'none', 'outFields': 'date_reported,cumulative_number_of_cases_on_t,total_deaths,residents_tested,new_cases_confirmed_today',
                  'orderByField': 'date_reported', 'f': 'json'}
    response = requests.get(data_url, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    features = [obj["attributes"] for obj in parsed['features']]

    # convert dates
    for obj in features:
        timestamp = obj['date_reported']
        date = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc)
        obj['date_reported'] = date.strftime("%Y-%m-%d")

    re_keyed = [{TIMESERIES_KEYS[key]: value for key, value in entry.items()}
                for entry in features]

    # Templates have all data points in the data model
    # datapoints that are not reported have a value of -1
    CASES_TEMPLATE = { "date": -1, "cases":-1, "cumul_cases":-1 }
    DEATHS_TEMPLATE = {"date":-1, "deaths":-1, "cumul_deaths":-1 }
    TESTS_TEMPLATE = { "date": -1, "tests": -1, "positive": -1, "negative": -1, "pending": -1, "cumul_tests": -1,"cumul_pos": -1, "cumul_neg": -1, "cumul_pend": -1 }

    for entry in re_keyed:
        # deep copy of templates
        cases = { k:v for k,v in CASES_TEMPLATE.items() }
        deaths = { k:v for k,v in DEATHS_TEMPLATE.items() }
        tests = { k:v for k,v in TESTS_TEMPLATE.items() }
        cases.update( { k:v for k,v in entry.items() if k in cases } )
        deaths.update( { k:v for k,v in entry.items() if k in deaths } )
        tests.update( { k:v for k,v in entry.items() if k in tests } )

        series["cases"].append(cases)
        series["deaths"].append(deaths)
        series["tests"].append(tests)

    out["series"].update(series)


def get_notes() -> str:
    """Scrape notes and disclaimers from dashboard."""
    # As of 6/5/20, the only disclaimer is "Data update weekdays at 4:30pm"
    pass
    notes = []
    match = re.compile('[Dd]isclaimers?')
    driver = get_firefox()
    driver.implicitly_wait(30)
    driver.get(dashboard_url)
    soup = BeautifulSoup(driver.page_source, 'html5lib')
    has_notes = False
    text = soup.get_text().splitlines()
    for text_item in text:
        if match.search(text_item):
            notes.append(text_item)
            has_notes = True
    if not has_notes:
        raise(FutureWarning(
            "This dashboard url has changed. None of the <div> elements contains'[Dd]isclaimers?$' " + dashboard_url))
    driver.quit()
    return '\n\n'.join(notes)


def get_race_eth (out: Dict):
    """
    Fetch cases by race and ethnicity
    Deaths by race/eth not currently reported. Multiple race and other race individuals counted in the same category, which I'm choosing to map to multiple_race.
    Returns the dictionary value for {"cases_totals": {}}, for use by get_county() in updating the main out dictionary
    """
    # Link to map item: https://www.arcgis.com/home/webmap/viewer.html?url=https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID_19_Survey_part_1_v2_new_public_view/FeatureServer/0&source=sd
    # The table view of the map item is a helpful reference.

    RACE_KEYS = {"Latinx_or_Hispanic": "all_cases_hispanic", "Asian": "all_cases_asian", "African_Amer": "all_cases_black",
                 "White": "all_cases_white", "Pacific_Islander": "all_cases_pacificIslander", "Native_Amer": "all_cases_ai_an", "Multiple_Race": "all_cases_multi_o",
                 "Unknown": "unknown_all"}

    # format query to get entry for latest date
    param_list = {'where': '0=0','outFields': '*', 'orderByFields':'date_reported DESC', 'resultRecordCount':1, 'f': 'json'}
    response = requests.get(data_url, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    latest_day = parsed['features'][0]['attributes']

    race_eth_table = { target_key: latest_day[source_key] for target_key, source_key in RACE_KEYS.items() }
    out["case_totals"]["race_eth"].update(race_eth_table)

def get_gender_age(out: Dict):
    """
    Fetch cases by gender and age group, deaths by age group
    Returns the dictionary value for {"cases_totals": {}, "death_totals":{} }, for use by get_county() in updating the main out dictionary
    """
    #TODO: Confirm which datapoints are the gender numbers with Solano County, and/or add caveat to metadata that the gender numbers are a guess
    """
    My best guess is that this table is a result of a botched join on a a gender table and an age table.
    The numbers that I'm guessing match up with age groups do match the numbers reported on the dashboard.
    The dashboard does not show gender, so I don't actually know if these are gender numbers.
    The data are reported as 3 sets of entries per day:

    [ {
            date_reported: timestamp_for_the_day,
            gender: male,
            number_of_cases: cumul number of male cases???,
            age_group: 0-18,
            non-severe: cumul number of non-severe 0-18 cases???,
            hospitalized: cumul number of hospitalized 0-18 case???,
            deaths: cumul number of 0-18 deaths??? },

      {
          date_reported: timestamp_for_the_day,
          gender: female,
          number_of_cases: cumul number of female cases???,
          age_group: 19-64,
          non-severe: cumul number of non-severe 19-64 cases???,
          hospitalized: cumul number of hospitalized 19-64 case???,
          deaths: cumul number of 19-64 deaths??? },

      {
          date_reported: timestamp_for_the_day,
          gender: unknown, or empty(!!!)
          number_of_cases: cumul number of unknown cases???,
          age_group: 65+,
          non-severe: cumul number of non-severe 65+ cases???,
          hospitalized: cumul number of hospitalized 65+ case???,
          deaths: cumul number of 65+ deaths???
          } ]

    See the data at this map item: https://www.arcgis.com/home/webmap/viewer.html?url=https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID_19_survey_part_2_v2_public_view/FeatureServer/0&source=sd
    The table view of the map item is a helpful reference.
    """


    # format query to get entries for latest date
    param_list = {'where': '0=0', 'outFields': '*',
                  'orderByFields': 'date_reported DESC', 'resultRecordCount': 3, 'f': 'json'}
    response = requests.get(data2_url, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    entries = [ attr["attributes"] for attr in parsed['features'] ] # surface data from nested attributes dict
    # Dicts of source_label: target_label for re-keying.
    GENDER_KEYS = {"female": "female", "male": "male",
                   "unknown": "unknown"}
    AGE_KEYS = {"0_18": "18_and_under",
                "19_64": "19_to_64", "65+": "65_and_over"}
    gender_table_cases = dict()
    age_table_cases = []
    age_table_deaths = []

    # parse output
    for entry in entries:
        gender_key = GENDER_KEYS.get(entry["gender"], "unknown") # for entries where gender not reported, assume unknown
        gender_cases = entry["number_of_cases"]
        age_key = AGE_KEYS.get(entry["age_group"])
        age_group_cases = entry["non_severe"] + entry["hospitalized"]
        age_group_deaths = entry["deaths"]
        gender_table_cases[gender_key] = gender_cases
        # also parsing ages in this for loop. It's possible that the entries could be stored out of order in the future, but it looks like
        # they are have always been correctly sorted.
        age_table_cases.append( { "group": age_key, "raw_count": age_group_cases } )
        age_table_deaths.append( { "group": age_key, "raw_count": age_group_deaths } )

    if age_table_cases[0]["group"] is not "18_and_under":
        raise FutureWarning("Age groups may not be in sorted order.")

    out["case_totals"]["gender"].update(gender_table_cases)
    out["case_totals"]["age_group"] = age_table_cases
    out["death_totals"]["age_group"] = age_table_deaths

if __name__ == '__main__':
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(get_county(), indent=4))
