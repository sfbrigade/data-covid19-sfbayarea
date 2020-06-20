#!/usr/bin/env python3
import csv
import json
import numpy as np
from typing import List, Dict, Tuple
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import unquote_plus
from datetime import datetime
import re

from ..webdriver import get_firefox
from .utils import get_data_model
#Can you also please make sure to use 4-space (not tab) indentation, so this is consistent with the other files? 

def get_county_data() -> Dict:
    """Main method for populating county data"""

    url = 'https://coronavirus.marinhhs.org/surveillance'
    model = get_data_model()

    chart_ids = {"cases": "Eq6Es", "deaths": "Eq6Es", "tests": '2Hgir', "age": "VOeBm", "gender": "FEciW", "race_eth": "aBeEd"} 
    # population totals and transmission data missing.
    model['name'] = "Marin County"
    model['update_time'] = datetime.today().isoformat()
    # No actual update time on their website? They update most charts daily (so the isoformat is only partially correct.)
    model['source_url'] = url
    model['meta_from_source'] = get_metadata(url, chart_ids)
    model["series"]["cases"] = get_case_series(chart_ids["cases"], url) 
    model["series"]["deaths"] =  get_death_series(chart_ids["deaths"], url)
    model["series"]["tests"] = get_test_series(chart_ids["tests"], url)
    model["case_totals"]["age_group"], model["death_totals"]["age_group"] = get_breakdown_age(chart_ids["age"], url)
    model["case_totals"]["gender"], model["death_totals"]["gender"] = get_breakdown_gender(chart_ids["gender"], url)
    model["case_totals"]["race_eth"], model["death_totals"]["race_eth"] = get_breakdown_race_eth(chart_ids["race_eth"], url)
    
    print(model)

def extract_csvs(chart_id: str, url: str) -> str:
    """This method extracts the csv string from the data wrapper charts."""
    driver = get_firefox()
    # need to figure out how to change the webdriver
    
    driver.implicitly_wait(30)
    driver.get(url)

    frame = driver.find_element_by_css_selector(f'iframe[src*="//datawrapper.dwcdn.net/{chart_id}/"]')

    driver.switch_to.frame(frame)
    # Grab the raw data out of the link's href attribute
    csv_data = driver.find_element_by_class_name('dw-data-link').get_attribute('href')
    # Switch back to the parent frame to "reset" the context
    driver.switch_to.parent_frame()
    
    # Deal with the data
    if csv_data.startswith('data:'):
        media, data = csv_data[5:].split(',', 1)
        # Will likely always have this kind of data type
        if media != 'application/octet-stream;charset=utf-8':
            raise ValueError(f'Cannot handle media type "{media}"')
        csv_string = unquote_plus(data)

    # Then leave the iframe
    driver.switch_to.default_content()

    return csv_string

def get_metadata(url: str, chart_ids: str) -> Tuple:
    notes = []
    driver = get_firefox()
    driver.implicitly_wait(30)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html5lib')
    metadata = []

    to_be_matched = ['Total Cases, Recovered, Hospitalizations and Deaths by Date Reported', 'Daily Count of Positive Results and Total Tests for Marin County Residents by Test Date ', 'Cases, Hospitalizations, and Deaths by Age, Gender and Race/Ethnicity ']
    chart_metadata = []

    for text in to_be_matched:
        target = soup.find('h4',text=text)
        if not target:
            raise ValueError('Cannot handle this header.')
        for sib in target.find_next_siblings()[:1]: # I only want the first paragraph tag
            # Is it more efficient to use something like (soup object).select('h1 + p') to grab the first paragraph that follows?
            metadata += [sib.text]

    # Metadata for each chart visualizing the data of the csv file I'll pull. There's probably a better way to organize this.
    for chart_id in chart_ids.values():
        frame = driver.find_element_by_css_selector(f'iframe[src*="//datawrapper.dwcdn.net/{chart_id}/"]')
        driver.switch_to.frame(frame)
        # The metadata for the charts is located in elements with the class `dw-chart-notes' 
        for c in driver.find_elements_by_class_name('dw-chart-notes'):
            chart_metadata.append(c.text)

        # Switch back to the parent frame to "reset" the context
        driver.switch_to.parent_frame()

    driver.quit() 

    # Return the metadata. I take the set of the chart_metadata since there are repeating metadata strings.
    return metadata, list(set(chart_metadata)) 

def get_case_series(chart_id: str, url: str) -> List:
    """This method extracts the date, number of cumulative cases, and new cases."""
    csv_ = extract_csvs(chart_id, url)
    series = []

    csv_strs = csv_.splitlines()
    keys = csv_strs[0].split(',')
    
    if keys != ['Date', 'Total Cases', 'Total Recovered*', 'Total Hospitalized', 'Total Deaths']:
        raise ValueError('The headers have changed')

    case_history = []

    for row in csv_strs[1:]:
        daily = {}
        # Grab the date in the first column
        date_time_obj = datetime.strptime(row.split(',')[0], '%m/%d/%Y')
        daily["date"] = date_time_obj.isoformat()
        # Collect the case totals in order to compute the change in cases per day 
        case_history.append(int(row.split(',')[1]))
        # Grab the cumulative number in the fifth column
        daily["cumul_cases"] = int(row.split(',')[1])
        series.append(daily)
        
    case_history_diff = np.diff(case_history) 
    # there will be no calculated difference for the first day, so adding it in manually
    case_history_diff = np.insert(case_history_diff, 0, 0) 
    # adding the case differences into the series
    for val, case_num in enumerate(case_history_diff):
        series[val]["cases"] = case_num
    return series

def get_death_series(chart_id: str, url: str) -> List:
    """This method extracts the date, number of cumulative deaths, and new deaths."""
    csv_ = extract_csvs(chart_id, url)
    series = []

    csv_strs = csv_.splitlines()
    keys = csv_strs[0].split(',')
    if keys != ['Date', 'Total Cases', 'Total Recovered*', 'Total Hospitalized', 'Total Deaths']:
        raise ValueError('The headers have changed.')

    death_history = []

    for row in csv_strs[1:]:
        daily = {}
        # Grab the date in the first column
        date_time_obj = datetime.strptime(row.split(',')[0], '%m/%d/%Y')
        daily["date"] = date_time_obj.isoformat()
        # Collect the death totals in order to compute the change in deaths per day 
        death_history.append(int(row.split(',')[4]))
        # Grab the cumulative number in the fifth column
        daily["cumul_deaths"] = int(row.split(',')[4])
        series.append(daily)
        
    death_history_diff = np.diff(death_history) 
    # there will be no calculated difference for the first day, so adding it in manually
    death_history_diff = np.insert(death_history_diff, 0, 0) 
    # adding the case differences into the series
    for val, death_num in enumerate(death_history_diff):
        series[val]["deaths"] = death_num
    return series

def get_breakdown_age(chart_id: str, url: str) -> Tuple:
    """This method gets the breakdown of cases and deaths by age."""
    csv_ = extract_csvs(chart_id, url)
    c_brkdown = []
    d_brkdown = []

    csv_strs = csv_.splitlines()
    keys = csv_strs[0].split(',') 

    if keys != ['Age Category', 'POPULATION', 'Cases', 'Hospitalizations', 'Deaths']:
        raise ValueError('The headers have changed')

    ages = ['0-18', '19-34', '35-49', '50-64', '65+'] 
    for row in csv_strs[1:]:
        c_age = {}
        d_age = {}
        # Extracting the age group and the raw count (the 3rd and 5th columns, respectively) for both cases and deaths.
        # Each new row has data for a different age group.
        c_age["group"] = row.split(',')[0]
        if c_age["group"] not in ages:
            raise ValueError('The age groups have changed.')
        c_age["raw_count"] = int(row.split(',')[2])
        d_age["group"] = row.split(',')[0]
        d_age["raw_count"] = int(row.split(',')[4])
        c_brkdown.append(c_age)
        d_brkdown.append(d_age)

    return c_brkdown, d_brkdown

def get_breakdown_gender(chart_id: str, url: str) -> Tuple:
    """This method gets the breakdown of cases and deaths by gender."""
    csv_ = extract_csvs(chart_id, url)

    csv_strs = csv_.splitlines()
    keys = csv_strs[0].split(',') 
    if keys != ['Gender', 'POPULATION', 'Cases', 'Hospitalizations', 'Deaths']:
        raise ValueError('The headers have changed.')

    genders = ['male', 'female']
    c_gender = {}
    d_gender = {}
    
    for row in csv_strs[1:]:
        # Extracting the gender and the raw count (the 3rd and 5th columns, respectively) for both cases and deaths.
        # Each new row has data for a different gender.
        split = row.split(',')
        gender = split[0].lower()
        if gender not in genders:
            return ValueError('The genders have changed.')
        c_gender[gender] = int(split[2])
        d_gender[gender] = int(split[4])            

    return c_gender, d_gender

def get_breakdown_race_eth(chart_id: str, url: str) -> Tuple:
    """This method gets the breakdown of cases and deaths by race/ethnicity."""

    csv_ = extract_csvs(chart_id, url)

    csv_strs = csv_.splitlines()
    keys = csv_strs[0].split(',') 
    
    if keys != ['Race/Ethnicity', 'COUNTY POPULATION', 'Case Count', 'Percent of Cases', 'Hospitalization Count', 'Percent of Hospitalizations', 'Death Count', 'Percent of Deaths']:
        raise ValueError("The headers have changed.")

    key_mapping = {"black/african american":"African_Amer", "hispanic/latino": "Latinx_or_Hispanic",
            "american indian/alaska native": "Native_Amer", "native hawaiian/pacific islander": "Pacific_Islander", "white": "White", "asian": "Asian", "multi or other race": "Multi or Other Race"}
            # "Multiple_Race", "Other" are not separate in this data set - they are one value under "Multi or Other Race"

    c_race_eth = {}
    d_race_eth = {}
    
    for row in csv_strs[1:]:
        split = row.split(',')
        race_eth = split[0].lower()
        if race_eth not in key_mapping:
            raise ValueError("The race_eth groups have changed.")
        else:
            c_race_eth[key_mapping[race_eth]] = int(split[2])
            d_race_eth[key_mapping[race_eth]] = int(split[6])

    return c_race_eth, d_race_eth

def get_test_series(chart_id: str, url: str) -> Tuple:
    """This method gets the date, the number of positive and negative tests on that date, and the number of cumulative positive and negative tests."""

    csv_ = extract_csvs(chart_id, url)
    series = []

    csv_strs = csv_.splitlines()
    keys = csv_strs[0].split(',')
    
    test_history = []
    
    # Grab the dates, which are in the header
    for entry in csv_strs[:1][0].split(',')[1:]: 
        # need to exclude very first item in the csv_strs[:1][0].split(',') list (which is the value 'Date')
        daily = {}
        date_time_obj = datetime.strptime(entry, '%m/%d/%Y')
        daily["date"] = date_time_obj.isoformat()
        series.append(daily)

    # The slicing makes this if statement hard to look at... there must be a better way?
    if csv_strs[1:2][0].split(',')[:1][0] != 'Positive Tests' and csv_strs[2:][0].split(',')[:1][0] != 'Negative Tests':
        raise ValueError('The kinds of tests have changed.')

    # Grab the positive test result numbers, which is in the second row. 
    # [1:] is included to make sure that 'Positive Tests' is not captured.
    p_entries = csv_strs[1:2][0].split(',')[1:]
    n_entries = csv_strs[2:][0].split(',')[1:]
    
    get_test_series_helper(series, p_entries, ['positive', 'cumul_pos'])
    get_test_series_helper(series, n_entries, ['negative', 'cumul_neg'])
    
    return series   

def get_test_series_helper(series: list, entries: list, keys: list) -> List:
    """This method helps get the pos/neg test count and the cumulative pos/neg test count."""
    
    # initialize values cumulative number, the positive/negative and cumul_pos/neg values for the first day, and the index needed for the while loop.
    
    # there's probably a more efficient way to do all of this, but I just wasn't sure.
    cumul = int(entries[0])
    series[0][keys[0]] = int(entries[0])
    series[0][keys[1]] = cumul
    index = 1   

    while index < len(series):
        # get a particular day
        day = series[index]
        curr = int(entries[index])
        # get pos/neg test count
        day[keys[0]] = int(curr)
        # add that day's pos/neg test count to get cumulative number of positive tests
        cumul += curr
        day[keys[1]] = cumul 
        index += 1
    return series


get_county_data()
