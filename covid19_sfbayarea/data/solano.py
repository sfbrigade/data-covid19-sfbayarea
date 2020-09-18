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
# data_url has cases, deaths, tests
data_url = "https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID19Surveypt1v3_view/FeatureServer/0/query"
# data2_url looks like a join on Race/Eth and Age Group #TODO: Parse this nightmare
data2_url = "https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID19Surveypt2v3_view_3/FeatureServer/0/query"
metadata_url = 'https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID19Surveypt1v3_view/FeatureServer/0?f=pjson'
dashboard_url = 'https://doitgis.maps.arcgis.com/apps/opsdashboard/index.html#/d28335cd317a45cd84211cd290889c27'

def get_county() -> Dict:
    """Main method for populating county data .json"""

    # Load data model template into a local dictionary called 'out'.
    out = get_data_model()

    # populate dataset headers
    out["name"] = "Solano County"
    out["source_url"] = data_url
    out["meta_from_source"] = get_notes()
    out["meta_from_baypd"] = '\n'.join([
        "Solano reports daily cumulative cases, deaths, and residents tested. The county does not report new daily confirmed cases.",
        "Solano reports total number of residents tested on each date. This may exclude counts of tests for individuals being retested. Solano does not report test results.",
        "Deaths by gender not currently reported."])

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
        'Date_reported': 'date',
        'cumulative_cases': 'cumul_cases',
        'total_deaths': 'cumul_deaths',
        'residents_tested': 'cumul_tests'
    }

    # query API for days where cumulative number of cases on the day > 0
    param_list = {  'where': 'cumulative_cases>0',
                    'resultType': 'none',
                    'outFields': 'Date_reported,cumulative_cases,total_deaths,residents_tested',
                    'orderByFields': 'date_reported asc', 'f': 'json'}
    response = requests.get(data_url, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    features = [obj["attributes"] for obj in parsed['features']]

    # convert dates
    PACIFIC_TIME = dateutil.tz.gettz('America/Los_Angeles')
    for obj in features:
        timestamp = obj['Date_reported']
        date = datetime.fromtimestamp(timestamp/1000, tz=PACIFIC_TIME)
        obj['Date_reported'] = date.strftime("%Y-%m-%d")

    re_keyed = [{TIMESERIES_KEYS[key]: value for key, value in entry.items()}
                for entry in features]

    # Templates have all data points in the data model
    # datapoints that are not reported have a value of -1
    CASES_TEMPLATE = { "date": -1, "cases":-1, "cumul_cases":-1 }
    DEATHS_TEMPLATE = {"date":-1, "deaths":-1, "cumul_deaths":-1 }
    TESTS_TEMPLATE = { "date": -1, "tests": -1, "positive": -1, "negative": -1, "pending": -1, "cumul_tests": -1,"cumul_pos": -1, "cumul_neg": -1, "cumul_pend": -1 }

    for entry in re_keyed:
        # grab cumulative values, to check if they are None
        cumul_cases = entry["cumul_cases"]
        cumul_deaths = entry["cumul_deaths"]
        cumul_tests = entry["cumul_tests"]

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
    # As of 9/18/20, the only disclaimer is "Numbers are updated weekdays at 6:00 PM."
    with get_firefox() as driver:
        notes = []
        match = re.compile('disclaimer?', re.IGNORECASE)
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
                "This dashboard has changed. None of the <div> elements contains'Disclaimers' " + dashboard_url)
        return '\n\n'.join(notes)


def get_race_eth (out: Dict)-> None :
    """
    Fetch cases by race and ethnicity
    """
    # Link to map item: https://www.arcgis.com/home/webmap/viewer.html?url=https://services2.arcgis.com/SCn6czzcqKAFwdGU/ArcGIS/rest/services/COVID19Surveypt2v3_view_3/FeatureServer&source=sd
    # The table view of the map item is a helpful reference.

    # format query to get entry for latest date for race/eth reporting
    # filter for any days on which a total race/eth was reported
    param_list = {'where': "Race_ethnicity='Total_RE'",'outFields': '*', 'orderByFields':'Date_reported DESC', 'resultRecordCount': '1', 'f': 'json'}
    response = requests.get(data2_url, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    latest_day_timestamp = parsed['features'][0]['attributes']['Date_reported']
    # translate timestamp  to a date string in format 'mm-dd-yyyy' to use in the query string
    latest_day = datetime.fromtimestamp(latest_day_timestamp/1000, tz=timezone.utc).strftime('%m-%d-%Y')

    # get all positive values for race/ethnicity total cases on the latest day
    param2_list = {'where': f"RE_total_cases>0 AND Date_reported = '{latest_day}' ",'outFields': 'Race_ethnicity, RE_total_cases, RE_deaths', 'f': 'json'}
    response2 = requests.get(data2_url, params=param2_list)
    response2.raise_for_status()
    parsed2 = response2.json()

    race_eth_cases = { entry['attributes']['Race_ethnicity']: entry['attributes']['RE_total_cases']  for entry in parsed2['features'] }
    # A complete table will have 10 datapoints, as of 9/18/20. If there are any more or less, raise an error.
    if len(race_eth_cases) != 10:
        raise FormatError( f'Race_eth query did not return 10 groups. Results: {race_eth_cases}')

    race_eth_deaths = { entry['attributes']['Race_ethnicity']: entry['attributes']['RE_deaths']  for entry in parsed2['features'] }
    # save to the out dict
    out["case_totals"]["race_eth"] = race_eth_cases
    out["death_totals"]["race_eth"] = race_eth_deaths

def get_age_table(out: Dict) -> None:
    """
    Fetch cases and deaths by age group
    Updates out with {"cases_totals": {}, "death_totals":{} }
    """

     # filter for any days on which a total age group cases was reported
    param_list = {'where': "Age_group='Total_AG'",'outFields': 'Date_reported', 'orderByFields':'Date_reported DESC', 'resultRecordCount': '1', 'f': 'json'}
    response = requests.get(data2_url, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    latest_day_timestamp = parsed['features'][0]['attributes']['Date_reported']
    # translate timestamp  to a date string in format 'mm-dd-yyyy' to use in the query string
    latest_day = datetime.fromtimestamp(latest_day_timestamp/1000, tz=timezone.utc).strftime('%m-%d-%Y')

    # get all positive values for race/ethnicity total cases on the latest day
    param2_list = {'where': f"AG_Total_cases>0 AND Date_reported = '{latest_day}' ",'outFields': 'Age_group, AG_Total_cases, AG_deaths', 'f': 'json'}
    response2 = requests.get(data2_url, params=param2_list)
    response2.raise_for_status()
    parsed2 = response2.json()

    age_group_cases = { entry['attributes']['Age_group']: entry['attributes']['AG_Total_cases']  for entry in parsed2['features'] }
    # A complete table will have 5 datapoints, as of 9/18/20. If there are any more or less, raise an error.
    if len(age_group_cases) != 5:
        raise FormatError( f'Race_eth query did not return 5 groups. Results: {age_group_cases}')

    age_group_deaths = { entry['attributes']['Age_group']: entry['attributes']['AG_deaths']  for entry in parsed2['features'] }
    # save to the out dict
    out["case_totals"]["age_group"] = age_group_cases
    out["death_totals"]["age_group"] = age_group_deaths

    out["case_totals"]["age_group"] = age_group_cases
    out["death_totals"]["age_group"] = age_group_deaths


def get_gender_table(out: Dict) -> None:
    """
    Fetch cases by gender
    Updates out with {"cases_totals": {} }
    """
     # filter for any days on which a Gender total cases numbner was reported
    param_list = {'where': "G_Total_cases>0",'outFields': 'Date_reported', 'orderByFields':'Date_reported DESC', 'resultRecordCount': '1', 'f': 'json'}
    response = requests.get(data2_url, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    latest_day_timestamp = parsed['features'][0]['attributes']['Date_reported']
    # translate timestamp  to a date string in format 'mm-dd-yyyy' to use in the query string
    latest_day = datetime.fromtimestamp(latest_day_timestamp/1000, tz=timezone.utc).strftime('%m-%d-%Y')

    # get all positive values for Gender total cases reported on the latest day
    param2_list = {'where': f"G_Total_cases>0 AND Date_reported = '{latest_day}' ",'outFields': 'Gender, G_Total_cases', 'f': 'json'}
    response2 = requests.get(data2_url, params=param2_list)
    response2.raise_for_status()
    parsed2 = response2.json()

    gender_cases = { entry['attributes']['Gender']: entry['attributes']['G_Total_cases']  for entry in parsed2['features'] }
    # A complete table will have at least 2 datapoints, as of 9/18/20. If were less than 2, raise an error.
    if len(gender_cases) <2 :
        raise FormatError( f'Gender query returned less than 2 groups. Results: {gender_cases}')

    # save to the out dict
    out["case_totals"]["gender"] = gender_cases

if __name__ == '__main__':
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(get_county(), indent=4))
