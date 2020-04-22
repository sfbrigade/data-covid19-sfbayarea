#!/usr/bin/env python3
import requests
import json
from typing import List, Dict
from datetime import datetime, timedelta

# .json file endpoints
# Note that we are using numbers for all of Alameda County, including Berkeley
counts = 'https://services3.arcgis.com/1iDJcsklY3l3KIjE/arcgis/rest/services/COVID_Counts/FeatureServer/0/query?where = 0 % 3D0 & outFields = * & f = pjson'
age_gender_url = 'https://services3.arcgis.com/1iDJcsklY3l3KIjE/ArcGIS/rest/services/COVID_Gender_age/FeatureServer/0/3/?f=pjson'
race_ethnicity_url = 'https://services3.arcgis.com/1iDJcsklY3l3KIjE/arcgis/rest/services/Race_Eth2/FeatureServer/0/3/?f=pjson'

def get_json(url, query=''):
    """
    Fetches data from url with optional query in JSON format
    and parses it into a dict
    """
    raw_response = requests.get(url + query)
    parsed_json = json.loads(raw_response.content)
    return parsed_json


# https: // services3.arcgis.com/1iDJcsklY3l3KIjE/arcgis/rest/services/COVID_Counts/FeatureServer/0/query?select = features & where = 0 = 0 & orderby = ObjectID & outFields = * & f = pjson
# Confirmed Cases and Deaths
def get_timeseries() -> Dict:
    """Get a time series of confirmed cases and deaths """
    return get_json(counts)["features"]


# Confirmed cases by age and gender
def get_age_gender_json() -> Dict:
    """fetch age x gender data"""
    return get_json(age_gender_url)["feature"]["attributes"]

def get_age_json() -> Dict:
    """get age breakdown"""
    source = get_age_gender_json()
    cols = ["Under_19", "Age_20_44", "Age_45_54", "Age_55_64", "Age_65_74", "Age_75_84", "Age_85_plus", "Other_Age"]
    age = {col: source[col] for col in cols}
    return age

def get_gender_json() -> Dict:
    """get gender breakdown"""
    source = get_age_gender_json()
    cols = ["Female", "Male", "Other", "Unknown"]
    gender = { col: source[col] for col in cols}
    return gender

#Confirmed cases by race and ethnicity
# Note: Alamedy county does not distingusih between race and ethnicity
def get_race_ethnicity_json() -> Dict:
    """ fetch race x ethnicity data """
    source = get_json(race_ethnicity_url)["feature"]["attributes"]
    return { col: source[col] for col in source.keys() if col != "Geography" and col != "ObjectId"}




if __name__ == '__main__':
    """ When run as a script, logs grouped data queries to console"""
    # print("Total cases and deaths: \n", json.dumps(
    #      get_cases_and_deaths(), indent=4))
    # print("Cases by age:\n", json.dumps(get_age_json(), indent=4))
    # print("Cases by gender:\n", json.dumps(get_gender_json(), indent=4))
    # print("Cases by race/ethnicity:\n", json.dumps(get_race_ethnicity_json(), indent=4))


