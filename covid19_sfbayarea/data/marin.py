#!/usr/bin/env python3
import csv
from typing import List, Dict, Tuple
from bs4 import BeautifulSoup # type: ignore
from urllib.parse import unquote_plus
from datetime import datetime, timezone
from contextlib import contextmanager
import time


from ..webdriver import get_firefox
from .utils import get_data_model

def get_county() -> Dict:
    """Main method for populating county data"""

    url = 'https://coronavirus.marinhhs.org/surveillance'
    model = get_data_model()

    chart_ids = {
        "cases": "Eq6Es",
        "deaths": "bSxdG",
        "age": "zSHDs",
        "gender": "FEciW",
        "race_eth": "aBeEd",
        "tests": "7sHQq",
    }
    # The time series data for negative tests is gone, so I've just scraped positive test data using the new chart referenced above.

    model['name'] = "Marin County"
    model['update_time'] = datetime.now(tz=timezone.utc).isoformat()
    model["meta_from_baypd"] = ""
    model['source_url'] = url
    model['meta_from_source'] = get_chart_meta(url, chart_ids)

    model["series"]["cases"] = get_series_data(chart_ids["cases"], url, ['Date', 'Total Cases', 'Total Recovered*'], "cumul_cases", 'Total Cases', 'cases')
    model["series"]["deaths"] =  get_series_data(chart_ids["deaths"], url, ['Event Date', 'Total Hospitalizations', 'Total Deaths'], "cumul_deaths", 'Total Deaths', 'deaths', date_column='Event Date')

    model["series"]["tests"] = get_test_series(chart_ids["tests"], url)
    model["case_totals"]["age_group"], model["death_totals"]["age_group"] = get_breakdown_age(chart_ids["age"], url)
    model["case_totals"]["gender"], model["death_totals"]["gender"] = get_breakdown_gender(chart_ids["gender"], url)
    model["case_totals"]["race_eth"], model["death_totals"]["race_eth"] = get_breakdown_race_eth(chart_ids["race_eth"], url)
    return model

@contextmanager
def chart_frame(driver, chart_id: str): # type: ignore
    # is this bad practice? I didn't know what type to specify here for the frame.
    frame = driver.find_element_by_css_selector(f'iframe[src*="//datawrapper.dwcdn.net/{chart_id}/"]')
    driver.switch_to.frame(frame)
    try:
        yield frame
    finally:
        driver.switch_to.default_content()
        driver.quit()

def get_chart_data(url: str, chart_id: str) -> List[str]:
    """This method extracts parsed csv data from the csv linked in the data wrapper charts."""
    with get_firefox() as driver:
        driver.implicitly_wait(30)
        driver.get(url)

        with chart_frame(driver, chart_id):
            csv_data = driver.find_element_by_class_name('dw-data-link').get_attribute('href')
            # Deal with the data
            if csv_data.startswith('data:'):
                media, data = csv_data[5:].split(',', 1)
                # Will likely always have this kind of data type
                if media != 'application/octet-stream;charset=utf-8':
                    raise ValueError(f'Cannot handle media type "{media}"')
                csv_string = unquote_plus(data)
                csv_data = csv_string.splitlines()
            else:
                raise ValueError('Cannot handle this csv_data href')

    return csv_data

def get_chart_meta(url: str, chart_ids: Dict[str, str]) -> str:
    """This method gets all the metadata underneath the data wrapper charts and the metadata at the top of the county dashboard."""
    # Some metadata strings are repeated, so use sets to dedupe them.
    metadata: List[str] = []
    chart_metadata: List[str] = []

    with get_firefox() as driver:
        driver.implicitly_wait(30)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html5lib')

        for soup_obj in soup.findAll('div', attrs={"class":"surveillance-data-text"}):
            if soup_obj.findAll('p'):
                # TODO: it's not clear why any of these are being removed, nor
                # why they are not being replaced with an equivalent ASCII
                # character or just a space (not having something else in their
                # place results in joined up words, like "arealways")
                # \u2014 = em dash
                # \u00a0 = non-breaking space
                # \u2019 = apostrophe/right single quote
                metadata.extend(paragraph.text.replace("\u2014","").replace("\u00a0", "").replace("\u2019","")
                                for paragraph in soup_obj.findAll('p'))
            else:
                raise ValueError('Metadata location has changed.')

        for chart_id in chart_ids.values():
            with chart_frame(driver, chart_id, quit_after=False):
                # TODO: just use selenium commands here
                for div in driver.find_elements_by_css_selector('div.notes-block'):
                    chart_metadata.append(div.text)

    # Manually adding in metadata about testing data
    chart_metadata.append("Negative and pending tests are excluded from the Marin County test data.")
    chart_metadata.append("Note that this test data is about tests done by Marin County residents, not about all tests done in Marin County (includes residents and non-residents).")

    # Deduplicate metadata messages. (But preserve order!)
    all_metadata = list(dict.fromkeys([*metadata, *chart_metadata]))
    return '\n\n'.join(all_metadata)

def get_series_data(chart_id: str, url: str, headers: list, model_typ: str, typ: str, new_count: str, date_column: str = 'Date') -> List:
    """This method extracts the date, number of cases/deaths, and new cases/deaths."""

    csv_data = get_chart_data(url, chart_id)
    csv_reader = csv.DictReader(csv_data)

    keys = csv_reader.fieldnames

    series: list = list()

    if keys != headers:
        raise ValueError(f'Data headers for chart "{chart_id}" have changed! '
                         f'Expected: {headers}, found: {keys}')

    history: list = list()

    for row in csv_reader:
        daily: dict = dict()
        date_time_obj = datetime.strptime(row[date_column], '%m/%d/%Y')
        daily["date"] = date_time_obj.strftime('%Y-%m-%d')
        # Collect the case totals in order to compute the change in cases per day
        history.append(int(row[typ]))
        daily[model_typ] = int(row[typ])
        series.append(daily)

    history_diff: list = list()
    # Since i'm substracting pairwise elements, I need to adjust the range so I don't get an off by one error.
    for i in range(0, len(history)-1):
        history_diff.append((int(history[i+1]) - int(history[i])) + int(series[0][model_typ]))
        # from what I've seen, series[0]["cumul_cases"] will be 0, but I shouldn't assume that.
    history_diff.insert(0, int(series[0][model_typ]))

    for val, num in enumerate(history_diff):
        series[val][new_count] = num
    return series

def get_breakdown_age(chart_id: str, url: str) -> Tuple[List, List]:
    """This method gets the breakdown of cases and deaths by age."""
    csv_data = get_chart_data(url, chart_id)
    csv_reader = csv.DictReader(csv_data)

    keys = csv_reader.fieldnames

    c_brkdown: list = list()
    d_brkdown: list = list()

    if keys != ['Age Category', 'POPULATION', 'Cases', 'Hospitalizations', 'Deaths']:
        raise ValueError('The headers have changed')

    key_mapping = {"0-9": "0_to_9", "10-18": "10_to_18", "19-34": "19_to_34", "35-49": "35_to_49", "50-64": "50_to_64", "65-79": "65_to_79", "80-94": "80_to_94", "95+": "95_and_older"}

    for row in csv_reader:
        c_age: dict = dict()
        d_age: dict = dict()
         # Extracting the age group and the raw count for both cases and deaths.
        c_age["group"], d_age["group"] = row['Age Category'], row['Age Category']
        if c_age["group"] not in key_mapping:
            raise ValueError(str(c_age["group"]) + ' is not in the list of age groups. The age groups have changed.')
        else:
            c_age["group"] = key_mapping[c_age["group"]]
            c_age["raw_count"] = int(row["Cases"])
            d_age["group"] = key_mapping[d_age["group"]]
            d_age["raw_count"] = int(row["Deaths"])
            c_brkdown.append(c_age)
            d_brkdown.append(d_age)

    return c_brkdown, d_brkdown

def get_breakdown_gender(chart_id: str, url: str) -> Tuple[Dict, Dict]:
    """This method gets the breakdown of cases and deaths by gender."""
    csv_data = get_chart_data(url, chart_id)
    csv_reader = csv.DictReader(csv_data)

    keys = csv_reader.fieldnames

    if keys != ['Gender', 'POPULATION', 'Cases', 'Hospitalizations', 'Deaths']:
        raise ValueError('The headers have changed.')

    genders = ['male', 'female']
    c_gender: dict = dict()
    d_gender: dict = dict()

    for row in csv_reader:
        # Extracting the gender and the raw count (the 3rd and 5th columns, respectively) for both cases and deaths.
        # Each new row has data for a different gender.
        gender = row["Gender"].lower()
        if gender not in genders:
            raise ValueError("The genders have changed.")
        c_gender[gender] = int(row["Cases"])
        d_gender[gender] = int(row["Deaths"])

    return c_gender, d_gender

def get_breakdown_race_eth(chart_id: str, url: str) -> Tuple[Dict, Dict]:
    """This method gets the breakdown of cases and deaths by race/ethnicity."""

    csv_data = get_chart_data(url, chart_id)
    csv_reader = csv.DictReader(csv_data)

    keys = csv_reader.fieldnames

    if keys != ['Race/Ethnicity', 'COUNTY POPULATION', 'Cases', 'Case Percent', 'Hospitalizations', 'Hospitalizations Percent', 'Deaths', 'Deaths Percent']:
        raise ValueError("The headers have changed.")

    key_mapping = {"Black/African American":"African_Amer", "Hispanic/Latino": "Latinx_or_Hispanic", "White": "White", "Asian": "Asian", "Native Hawaiian/Pacific Islander": "Pacific_Islander", "American Indian/Alaska Native": "Native_Amer", "Multi or Other Race": "Multi_or_Other"}

    c_race_eth: dict = dict()
    d_race_eth: dict = dict()

    for row in csv_reader:
        race_eth = row["Race/Ethnicity"]
        if race_eth not in key_mapping:
            raise ValueError("The race_eth groups have changed.")
        else:
            c_race_eth[key_mapping[race_eth]] = int(row["Cases"])
            d_race_eth[key_mapping[race_eth]] = int(row["Deaths"])

    return c_race_eth, d_race_eth

def get_test_series(chart_id: str, url: str) -> List:
    """This method gets the date, the number of new positive tests on that date, and the number of cumulative positive tests."""
    csv_data = get_chart_data(url, chart_id)
    csv_reader = csv.DictReader(csv_data)

    keys = csv_reader.fieldnames

    if keys != ['Test Date', 'Positive Tests']:
        raise ValueError("The headers have changed.")

    test_series: list = list()

    cumul_pos = 0
    for row in csv_reader:
        daily: dict = dict()
        date_time_obj = datetime.strptime(row['Test Date'], '%m/%d/%Y')
        daily["date"] = date_time_obj.strftime('%Y-%m-%d')
        daily["positive"] = int(row["Positive Tests"])
        cumul_pos += daily["positive"]
        daily["cumul_positive"] = cumul_pos
        test_series.append(daily)

    return test_series
