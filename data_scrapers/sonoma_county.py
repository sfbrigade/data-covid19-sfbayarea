#!/usr/bin/env python3
import requests
import json
import re
from datetime import datetime
from typing import List, Dict, Union
from bs4 import BeautifulSoup, element # type: ignore

def get_rows(tag: element.Tag) -> List[element.ResultSet]:
    """
    Gets all tr elements in a tag but the first, which is the header
    """
    return tag.find_all('tr')[1:]

def get_cells(row: element.ResultSet) -> List[str]:
    """
    Gets all th and tr elements within a single tr element
    """
    return [el.text for el in row.find_all(['th', 'td'])]

def generate_update_time(soup: BeautifulSoup) -> str:
    """
    Generates a timestamp string (e.g. May 6, 2020 10:00 AM) for when the scraper is run
    """
    update_time_text = soup.find('time').text.strip()
    update_datetime = datetime.strptime(update_time_text, '%B %d, %Y %I:%M %p')
    return update_datetime.isoformat()

def get_source_meta(soup: BeautifulSoup) -> str:
    """
    Finds the 'Definitions' header on the page and gets all of the text in it
    """
    definitions_header = soup.find('h3', string='Definitions')
    definitions_text = definitions_header.find_parent().text
    return definitions_text.replace('\n', '/').strip()

# apologies for this horror of a output type
def transform_cases(cases_tag: element.Tag) -> Dict[str, List[Dict[str, Union[str, int]]]]:
    """
    Takes in a BeautifulSoup tag for the cases table and returns all cases
    (historic and active), deaths, and recoveries in the form:
    { 'cases': [], 'deaths': [], 'recovered': [], 'active': [] }
    Where each list contains dictionaries (representing each day's data)
    of form (example for cases):
    { 'date': '', 'cases': -1, 'cumul_cases': -1 }
    """
    cases = []
    cumul_cases = 0
    deaths = []
    cumul_deaths = 0
    recovered = []
    cumul_recovered = 0
    active = []
    cumul_active = 0
    rows = get_rows(cases_tag)
    for row in rows:
        row_cells = row.find_all(['th', 'td'])
        # print(type(row_cells))
        date = row_cells[0].text.replace('/', '-')

        # instead of 0, this dashboard reports the string '-'
        active_cases, new_infected, dead, recoveries = [0 if el.text == '–' else int(el.text) for el in row_cells[1:]]

        cumul_cases += new_infected
        cases.append({ 'date': date, 'cases': new_infected, 'cumul_cases': cumul_cases })

        new_deaths = dead - cumul_deaths
        deaths.append({ 'date': date, 'deaths': new_deaths, 'cumul_deaths': dead })

        new_recovered = recoveries - cumul_recovered
        recovered.append({ 'date': date, 'recovered': new_recovered, 'cumul_recovered': recoveries })

        new_active = active_cases - cumul_active
        active.append({ 'date': date, 'active': new_active, 'cumul_active': active_cases })

    return { 'cases': cases, 'deaths': deaths, 'recovered': recovered, 'active': active }

def transform_transmission(transmission_tag: element.Tag) -> Dict[str, int]:
    """
    Takes in a BeautifulSoup tag for the transmissions table and breaks it into
    a dictionary of type:
    {'community': -1, 'from_contact': -1, 'travel': -1, 'unknown': -1}
    """
    transmissions = {}
    rows = get_rows(transmission_tag)
    # turns the transmission categories on the page into the ones we're using
    transmission_type_conversion = {'Community': 'community', 'Close Contact': 'from_contact', 'Travel': 'travel', 'Under Investigation': 'unknown'}
    for row in rows:
        type, number, _pct = get_cells(row)
        if type not in transmission_type_conversion:
            raise FutureWarning('The transmission type {0} was not found in transmission_type_conversion'.format(type))
        type = transmission_type_conversion[type]
        transmissions[type] = int(number)
    return transmissions

def transform_tests(tests_tag: element.Tag) -> Dict[str, int]:
    tests = {}
    rows = get_rows(tests_tag)
    for row in rows:
        result, number, _pct = get_cells(row)
        lower_res = result.lower()
        tests[lower_res] = int(number.replace(',', ''))
    return tests;

def generic_transform(tag: element.Tag) -> Dict[str, int]:
    """
    Transform function for tables which don't require any special processing.
    Takes in a BeautifulSoup tag for a table and returns a dictionary
    in which the keys are strings and the values integers
    """
    categories = {}
    rows = get_rows(tag)
    for row in rows:
        cat, cases, _pct = get_cells(row)
        categories[cat] = int(cases)
    return categories

def get_unknown_race(race_eth_tag: element.Tag) -> int:
    """
    Gets the notes under the 'Cases by race and ethnicity' table to find the
    number of cases where the person's race is unknown
    """
    parent = race_eth_tag.parent
    note = parent.find('p').text
    matches = re.search('(\d+) \(\d{1,3}%\) missing race/ethnicity', note)
    if not matches:
        raise FutureWarning('The format of the note with unknown race data has changed')
    return(int(matches.groups()[0]))

def transform_race_eth(race_eth_tag: element.Tag) -> Dict[str, int]:
    """
    Takes in the BeautifulSoup tag for the cases by race/ethnicity table and
    transforms it into an object of form:
    'race_eth': {'Asian': -1, 'Latinx_or_Hispanic': -1, 'Other': -1, 'White':-1, 'Unknown': -1}
    NB: These are the only races reported seperatley by Sonoma county at this time
    """
    race_cases = {}
    race_transform = {'Asian/Pacific Islander, non-Hispanic': 'Asian', 'Hispanic/Latino': 'Latinx_or_Hispanic', 'Other*, non-Hispanic': 'Other', 'White, non-Hispanic': 'White'}
    rows = get_rows(race_eth_tag)
    for row in rows:
        group_name, cases, _pct = get_cells(row)
        if group_name not in race_transform:
            raise FutureWarning('The racial group {0} is new in the data -- please adjust the scraper accordingly')
        internal_name = race_transform[group_name]
        race_cases[internal_name] = int(cases)
    race_cases['Unknown'] = get_unknown_race(race_eth_tag)
    return race_cases

def transform_total_hospitalizations(hospital_tag: element.Tag) -> Dict[str, int]:
    """
    Takes in a BeautifulSoup tag of the cases by hospitalization table and
    returns a dictionary with the numbers of hospitalized and non-hospitalized
    cases
    """
    hospitalizations = {}
    rows = get_rows(hospital_tag)
    for row in rows:
        hospitalized, number, _pct = get_cells(row)
        if hospitalized.lower() == 'yes':
            hospitalizations['hospitalized'] = int(number)
        else:
            hospitalizations['not_hospitalized'] = int(number)
    return hospitalizations

def transform_gender_hospitalizations(hospital_tag: element.Tag) -> Dict[str, float]:
    """
    Takes in a BeautifulSoup tag representing the percent of cases hospitalized
    by gender and returns a dictionary of those percentages in float form
    e.g. 9% is 0.09
    """
    hospitalized = {}
    rows = get_rows(hospital_tag)
    for row in rows:
        gender, no, yes = get_cells(row)
        yes_int = int(yes.replace('%', ''))
        hospitalized[gender] = (yes_int / 100)
    return hospitalized

def get_county() -> Dict:
    """Main method for populating county data .json"""
    url = 'https://socoemergency.org/emergency/novel-coronavirus/coronavirus-cases/'
    page = requests.get(url)
    sonoma_soup = BeautifulSoup(page.content, 'html5lib')
    tables = sonoma_soup.find_all('table')[4:] # we don't need the first three tables

    try:
        # we have a lot more data here than we are using
        hist_cases, cases_by_source, cases_by_race, total_tests, cases_by_region, region_guide, hospitalized, underlying_cond, symptoms, cases_by_gender, underlying_cond_by_gender, hospitalized_by_gender, symptoms_female, symptoms_male, symptoms_desc, cases_by_age, symptoms_by_age, underlying_cond_by_age = tables
    except ValueError:
        raise FutureWarning('The number of values on the page has changed -- please adjust the scraper')

    model = {
        'name': 'Sonoma County',
        'update_time': generate_update_time(sonoma_soup),
        'source': url,
        'meta_from_source': get_source_meta(sonoma_soup),
        'meta_from_baypd': 'Racial "Other" category includes "Black/African American, American Indian/Alaska Native, and Other"',
        'series': transform_cases(hist_cases),
        'case_totals': {
            'transmission_cat': transform_transmission(cases_by_source),
            'age_group': generic_transform(cases_by_age),
            'race_eth': transform_race_eth(cases_by_race),
            'gender': generic_transform(cases_by_gender)
        },
        'tests_totals': {
            'tests': transform_tests(total_tests),
        },
        # 'hospitalizations': {
        #     'hospitalized_cases': transform_total_hospitalizations(hospitalized),
        #     'gender': transform_gender_hospitalizations(hospitalized_by_gender)
        # }
    }
    return model

if __name__ == '__main__':
    print(json.dumps(get_county(), indent=4))
