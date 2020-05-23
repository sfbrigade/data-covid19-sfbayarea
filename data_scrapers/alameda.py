#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup # type: ignore
import json
from typing import List, Dict, Tuple
from datetime import datetime, timezone
from selenium import webdriver  # type: ignore
from data_scrapers.utils import get_data_model

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
    """Main method for populating county data .json"""

    # Load data model template into a local dictionary called 'out'.
    out = get_data_model()

    # populate dataset headers
    out["name"] = "Alameda County"
    out["source_url"] = landing_page
    out["meta_from_source"] = get_notes()

    # fetch cases metadata, to get the timestamp
    response = requests.get(cases_meta)
    response.raise_for_status()
    cases_header = response.json()
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
    out.update(demo_totals)
    if counts_lt_10:
        out["meta_from_baypd"] = "These datapoints have a value less than 10: " + ", ".join([item for item in counts_lt_10])
    else:
        out["meta_from_baypd"] = ""
    return out


# Confirmed Cases and Deaths
def get_timeseries() -> Dict:
    """Fetch daily and cumulative cases and deaths by day
    Returns the dictionary value for "series": {"cases":[], "deaths":[]}.
    To create a DataFrame from this dictionary, run
    'pd.DataFrame(get_timeseries())'
    """

    series: Dict[str, List] = {"cases":[], "deaths":[]} # dictionary holding the timeseries for cases and deaths
    # Dictionary of 'source_label': 'target_label' for re-keying
    TIMESERIES_KEYS = {
        'Date': 'date',
        'AC_Cases': 'cases',
        'AC_CumulCases': 'cumul_cases',
        'AC_Deaths': 'deaths',
        'AC_CumulDeaths': 'cumul_deaths'
    }

    # query API
    param_list = {'where':'0=0', 'resultType': 'none', 'outFields': 'Date,AC_Cases,AC_CumulCases,AC_Deaths,AC_CumulDeaths', 'outSR': '4326','orderByField': 'Date', 'f': 'json'}
    response = requests.get(cases_deaths, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    features = [obj["attributes"] for obj in parsed['features']]

    # convert dates
    for obj in features:
        month, day, year = obj['Date'].split('/')
        if int(month) < 10:
            month = '0' + month
        if int(day) < 10:
            day = '0' + day
        obj['Date'] = "{}-{}-{}".format(year, month, day)



    re_keyed = [{TIMESERIES_KEYS[key]: value for key, value in entry.items()}
                for entry in features]

    # parse series into cases and deaths
    death_keys = ["date", "deaths", "cumul_deaths"]
    case_keys = ["date", "cases", "cumul_cases"]
    series["cases"] = [{k: v for k, v in entry.items() if k in case_keys} for entry in re_keyed]
    series["deaths"] = [{k: v for k, v in entry.items() if k in death_keys} for entry in re_keyed]
    return series

def get_notes() -> str:
    """Scrape notes and disclaimers from dashboards."""
    notes = []
    driver = webdriver.Firefox()
    driver.implicitly_wait(30)
    for url in dashboards:
        has_notes = False
        driver.get(url)
        soup = BeautifulSoup(driver.page_source,'html5lib')
        for p_tag in soup.find_all('p'):
            if 'Notes' in p_tag.get_text():
                notes.append(p_tag.get_text().strip())
                has_notes = True
        if not has_notes:
            raise(FutureWarning("This dashboard url has changed. None of the <p> elements contain the text \'Notes\': " + url))
        driver.get('about:blank') # loads empty page to allow loading of next page
    driver.quit()
    return '\n\n'.join(notes)

def get_demographics(out: Dict) -> Tuple[Dict, List]:
    """Fetch cases and deaths by age, gender, race, ethnicity
    Returns the dictionary value for {"cases_totals": {}, "death_totals":{}}, as well as a list of
    strings describing datapoints that have a value of "<10".
    To create a DataFrame from the dictionary, run 'pd.DataFrame(get_demographics()[0])'
    Note that the DataFrame will convert the "<10" strings to NaN.
    """
    # Dicts of target_label : source_label for re-keying.
    # Note that the cases table includes MTF and FTM, but the deaths table does not.
    GENDER_KEYS = {"female": "Female", "male": "Male",
                   "unknown": "Unknown_Sex", "mtf": "MTF", "ftm": "FTM"}
    RACE_KEYS = {"Latinx_or_Hispanic": "Hispanic_Latino", "Asian": "Asian", "African_Amer": "African_American_Black",
                 "White": "White", "Pacific_Islander": "Pacific_Islander", "Native_Amer": "Native_American", "Multiple_Race": "Multirace",
                 "Other": "Other_Race", "Unknown": "Unknown_Race"}
    # list of ordered (target_label, source_label) tuples  for re-keying the age table
    AGE_KEYS = { "18_and_under":"Age_LT18", "18_to_30":"Age_18_30", "31_to_40":"Age_31_40", "41_to_50":"Age_41_50", "51_to_60":"Age_51_60", "61_to_70":"Age_61_70", "71_to_80":"Age_71_80", "81_and_older":"Age_81_Up", "Unknown":"Unknown_Age" }

    # format query to get entry for Alameda County
    param_list = {'where': "Geography='Alameda County'", 'outFields': '*', 'outSR':'4326', 'f':'json'}
    # get cases data
    response = requests.get(demographics_cases, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    cases_data = parsed['features'][0]['attributes']
    # get deaths data
    response = requests.get(demographics_deaths, params=param_list)
    response.raise_for_status()
    parsed = response.json()
    deaths_data = parsed['features'][0]['attributes']

    # join cases and deaths tables in a temporary dictionary, to use for checking for values <10
    demo_data = {"case_totals": cases_data, "death_totals": deaths_data}
    # Handle values equal to '<10', if any. Note that some data points are entered as `null`, which
    # will be decoded as Python's `None`
    counts_lt_10 = []
    for cat, data in demo_data.items():
        for key, val in data.items():
            if key in GENDER_KEYS.values():
                demo = 'gender'
            elif key in RACE_KEYS.values():
                demo = 'race'
            elif key in AGE_KEYS.values():
                demo = 'age_group'
            elif key == "Geography":
                continue # exclude the k,v pair "Geography":"Alameda County"
            if val == '<10':
                counts_lt_10.append(f"{cat}.{demo}.{key}")
            elif val is None:  # proactively set None values to our default value of -1
                data[key] = - 1
            else:  # this value should be a number. check that val can be cast to an int.
                try:
                    int(val)
                except ValueError:
                    raise ValueError(f'Non-integer value for {key}')

    # copy dictionary structure of 'out' dictionary to local variable
    demo_totals = {
        "case_totals": out["case_totals"], "death_totals": out["death_totals"]}

    # Parse and re-key demo_totals
    # gender cases and deaths
    for k, v in GENDER_KEYS.items():
        demo_totals["case_totals"]["gender"][k] = cases_data[v]
        if f'Deaths_{v}' in deaths_data:  # the deaths table does not currently include MTF or FTM
            demo_totals["death_totals"]["gender"][k] = deaths_data['Deaths_' + v]
    # race cases and deaths
    for k, v in RACE_KEYS.items():
        demo_totals["case_totals"]["race_eth"][k] = cases_data[v]
        demo_totals["death_totals"]["race_eth"][k] = deaths_data['Deaths_' + v]
    # re-key and re-format age tables as a list
    cases_age_table = []
    deaths_age_table = []
    for out_key, data_key in AGE_KEYS.items():
        cases_age_table.append( {'group': out_key, 'raw_count':cases_data.get(data_key) } )
        deaths_age_table.append( {'group': out_key, 'raw_count':deaths_data.get("Deaths_"+data_key) } )

    demo_totals['case_totals']['age_group'] = cases_age_table
    demo_totals['death_totals']['age_group'] = deaths_age_table

    return demo_totals, counts_lt_10

if __name__ == '__main__':
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(get_county(), indent=4))

