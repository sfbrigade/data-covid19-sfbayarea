#!/usr/bin/env python3
import requests
import re
from bs4 import BeautifulSoup  # type: ignore
import json
from typing import List, Dict
from datetime import datetime, timezone
import dateutil.tz
from ..webdriver import get_firefox
from .utils import get_data_model
from collections import defaultdict
from ..errors import FormatError

# URLs and API endpoints:
# data_url has cases, deaths, tests, and race_eth
data_url = "https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID_19_Survey_part_1_v2_new_public_view/FeatureServer/0/query"
# data2_url used to be a join on gender and age. As of 6/15/20, Age Groups were removed from this table. It looks like Gender has been updated through 6/12.
data2_url = "https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID_19_survey_part_2_v2_public_view/FeatureServer/0/query"
# age_group_url has cumulative cases and deaths by age group. This endpoint was added to this script on 6/15/20
age_group_url = 'https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/AgeGroupsTable/FeatureServer/0/query'
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
    out["meta_from_baypd"] = '\n'.join([
        "Solano reports daily cumulative cases, deaths, and residents tested. In addition to cumulative cases each day, the county separately reports new daily confirmed cases.",
        "In the cases timeseries, cumulative cases on any given day may not equal the sum of new daily cases to date.",
        "This may be because source data for daily cases refers to cases that were laboratory-confirmed by 1:30 pm that day, with weekend case onfirmations possibly occurring on Mondays.",
        "Solano reports total number of residents tested on each date. This may exclude counts of tests for individuals being retested. Solano does not report test results.",
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
        raise FormatError("A timezone may now be specified in the metadata.")
    # convert timestamp to datetime object
    update = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc)
    out["update_time"] = update.isoformat()

    # get cases, deaths, and demographics data
    get_timeseries(out)
    get_age_table(out)
    get_gender_table(out)
    get_race_eth(out)

    return out


# Confirmed Cases and Deaths
def get_timeseries(out: Dict) -> None:
    """Fetch cumulative cases and deaths by day
    Update out dictionary with results.
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
    param_list = {  'where': 'cumulative_number_of_cases_on_t>0',
                    'resultType': 'none',
                    'outFields': 'date_reported,cumulative_number_of_cases_on_t,total_deaths,residents_tested,new_cases_confirmed_today',
                    'orderByFields': 'date_reported asc', 'f': 'json'}
    response = requests.get(data_url, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    features = [obj["attributes"] for obj in parsed['features']]

    # convert dates
    PACIFIC_TIME = dateutil.tz.gettz('America/Los_Angeles')
    for obj in features:
        timestamp = obj['date_reported']
        date = datetime.fromtimestamp(timestamp/1000, tz=PACIFIC_TIME)
        obj['date_reported'] = date.strftime("%Y-%m-%d")

    re_keyed = [{TIMESERIES_KEYS[key]: value for key, value in entry.items()}
                for entry in features]

    # Templates have all data points in the data model
    # datapoints that are not reported have a value of -1
    CASES_TEMPLATE = { "date": -1, "cases":-1, "cumul_cases":-1 }
    DEATHS_TEMPLATE = {"date":-1, "deaths":-1, "cumul_deaths":-1 }
    TESTS_TEMPLATE = { "date": -1, "tests": -1, "positive": -1, "negative": -1, "pending": -1, "cumul_tests": -1,"cumul_pos": -1, "cumul_neg": -1, "cumul_pend": -1 }

    for entry in re_keyed:
        #FIXME:
        # Sonoma county has entries for each day, but some days have "null" for cumulative deaths and cumulative tests.
        # This means that cumulative counts go something like: 1, null ,null, null, 2, 3 -- on consecutive days.
        # My best guess is that for deaths and tests they are entering "null" for the cumulative counts on days where the cumulative counts haven't changed from the previous day.
        # The solution below is just to filter out the cumulative count "null" values (Python None), which results in gaps in the timeseries.
        # We may want to revisit this and clean up our json to interpolate the values on null-count days until the day the value changes. But that means we're injecting numbers
        # into the data, and I don't know if we want to do that. But we will be interpolating anyways, in our visualizations, so maybe that's ok.

        # grab cumulative values, to check if they are None
        cumul_cases = entry["cumul_cases"]
        cumul_deaths = entry["cumul_deaths"]
        cumul_tests = entry["cumul_tests"]

        # grab cases and replace None with 0
        if entry["cases"] is None:
            entry["cases"] = 0

        if cumul_cases is not None:
            cases_entry = { k: entry[k] for k in CASES_TEMPLATE if k in entry }
            series["cases"].append(cases_entry)
        if cumul_deaths is not None:
            deaths_entry = {k: entry[k] for k in DEATHS_TEMPLATE if k in entry}
            series["deaths"].append(deaths_entry)
        if cumul_tests is not None:
            tests_entry = {k: entry[k] for k in TESTS_TEMPLATE if k in entry}
            series["tests"].append(tests_entry)

    out["series"].update(series)


def get_notes() -> str:
    """Scrape notes and disclaimers from dashboard."""
    # As of 6/5/20, the only disclaimer is "Data update weekdays at 4:30pm"
    with get_firefox() as driver:
        notes = []
        match = re.compile('disclaimers?', re.IGNORECASE)
        driver.implicitly_wait(30)
        driver.get(dashboard_url)
        soup = BeautifulSoup(driver.page_source, 'html5lib')
        has_notes = False
        text = soup.get_text().splitlines()
        for text_item in text:
            if match.search(text_item):
                notes.append(text_item.strip())
                has_notes = True
        if not has_notes:
            raise FormatError(
                "This dashboard url has changed. None of the <div> elements contains'Disclaimers' " + dashboard_url)
        return '\n\n'.join(notes)


def get_race_eth (out: Dict)-> None :
    """
    Fetch cases by race and ethnicity
    Deaths by race/eth not currently reported. Multiple race and other race individuals counted in the same category, which I'm choosing to map to multiple_race.
    Updates out dictionary with {"cases_totals": {}}
    """
    # Link to map item: https://www.arcgis.com/home/webmap/viewer.html?url=https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID_19_Survey_part_1_v2_new_public_view/FeatureServer/0&source=sd
    # The table view of the map item is a helpful reference.

    RACE_KEYS = {"Latinx_or_Hispanic": "all_cases_hispanic", "Asian": "all_cases_asian", "African_Amer": "all_cases_black",
                 "White": "all_cases_white", "Pacific_Islander": "all_cases_pacificIslander", "Native_Amer": "all_cases_ai_an", "Multiple_Race": "all_cases_multi_o",
                 "Unknown": "unknown_all"}

    # format query to get entry for latest date
    # check for the 'all_cases_total', which is the first total cases column before the race/eth columns
    param_list = {'where': 'all_cases_total>0','outFields': '*', 'orderByFields':'date_reported DESC', 'resultRecordCount': '1', 'f': 'json'}
    response = requests.get(data_url, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    latest_day = parsed['features'][0]['attributes']

    race_eth_table = { target_key: latest_day[source_key] for target_key, source_key in RACE_KEYS.items() }
    out["case_totals"]["race_eth"].update(race_eth_table)

def get_age_table(out: Dict) -> None:
    """
    Fetch cases and deaths by age group
    Updates out with {"cases_totals": {}, "death_totals":{} }
    """
    param_list = {'where': '0=0', 'outFields': 'Age_Group, All_cases_Number, Died_Number',
                  'orderByFields': 'Age_Group ASC', 'f': 'json'}
    response = requests.get(age_group_url, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    # surface data from nested attributes dict
    entries = [attr["attributes"] for attr in parsed['features']]

    if len(entries) != 4: # check that we have 4 entries, one for each expected age group
        raise FormatError(
            f"The source data structure has changed. Query did not return four age groups. Results: {entries}")

    # Dict of source_label: target_label for re-keying.
    AGE_KEYS = {"0-17 yrs": "0_to_17",
                "18-49 yrs": "18_to_49", "50-64 yrs": "50_to_64", "65+ yrs": "65_and_older" }
    age_table_cases = []
    age_table_deaths = []

    # parse output
    for entry in entries:
        age_key = AGE_KEYS[entry["Age_Group"]]
        age_group_cases = entry["All_cases_Number"] or 0 # explicitly set 0 for null values
        age_group_deaths = entry["Died_Number"] or 0
        age_table_cases.append(
            {"group": age_key, "raw_count": age_group_cases})
        age_table_deaths.append(
            {"group": age_key, "raw_count": age_group_deaths})

    out["case_totals"]["age_group"] = age_table_cases
    out["death_totals"]["age_group"] = age_table_deaths


def get_gender_table(out: Dict) -> None:
    """
    Fetch cases by gender
    Updates out with {"cases_totals": {} }
    """
    #TODO: Confirm which datapoints are the gender numbers with Solano County, and/or add caveat to metadata that the gender numbers are a guess
    """
    This data used to have Age Group numbers. The Age_Group columns are still being shown in this source.
    See the data at this map item: https://www.arcgis.com/home/webmap/viewer.html?url=https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID_19_survey_part_2_v2_public_view/FeatureServer/0&source=sd
    The table view of the map item is a helpful reference.
    """

    # format query to get the latest 3 entries. This will get the latest Male and Female entries, plus one additional entry to check if there was
    # an Unknown gender engry for the day
    param_list = {'where': '0=0', 'outFields': '*',
                  'orderByFields': 'date_reported DESC', 'resultRecordCount': '3', 'f': 'json'}
    response = requests.get(data2_url, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    entries = [ attr["attributes"] for attr in parsed['features'] ] # surface data from nested attributes dict


    # filter entries to surface the 3 entries for the most recent day with at least 2 Male/Female genders
    # to find them, compare to a complete day's set of included values
    complete_day = { 'male', 'female'}

    # days is a dict to collect the set of values
    # initialize days with an empty set of values for each day
    days = defaultdict(set)
    keys_to_check = ["gender"]
    # collect the values for keys to check in each day's set of values
    for entry in entries:
        day = entry["date_reported"]
        for k in keys_to_check:
            days[day].add( entry[k] )

    # compare each day's sets of keys to a complete day
    # make a list of all complete days
    complete_days = [ k for k,v in days.items() if complete_day.issubset(v) ]

    if len(complete_days) != 1:
        raise FormatError(f"The source data structure has changed. Issues with gender data for these dates: {','.join(complete_days)}" )

    # include all entries with date equal to the complete day
    gender_cols = [ entry for entry in entries if entry["date_reported"] in complete_days ]

    # Dicts of source_label: target_label for re-keying.
    GENDER_KEYS = {"female": "female", "male": "male",
                   "unknown": "unknown"}
    gender_table_cases = dict()

    # parse output
    for entry in gender_cols:
        gender_key = GENDER_KEYS.get(entry["gender"], "unknown") # for entries where gender not reported, assume unknown
        gender_cases = entry["number_of_cases"] or 0 # explicitly set 0 for null values
        gender_table_cases[gender_key] = gender_cases

    out["case_totals"]["gender"].update(gender_table_cases)

if __name__ == '__main__':
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(get_county(), indent=4))
