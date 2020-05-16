#!/usr/bin/env python3
import requests
import json
from datetime import datetime
from typing import List, Dict, Union
from bs4 import BeautifulSoup, element

url = 'https://socoemergency.org/emergency/novel-coronavirus/coronavirus-cases/'
page = requests.get(url)
sonoma_soup = BeautifulSoup(page.content, 'html.parser')
tables = sonoma_soup.findAll('table')[4:] # we don't need the first three tables

def generate_update_time(soup: BeautifulSoup) -> str:
    update_time_text = soup.find('time').text.strip()
    # format is May 6, 2020 10:00 AM
    update_datetime = datetime.strptime(update_time_text, '%B %d, %Y %I:%M %p')
    return update_datetime.isoformat()

def get_source_meta(soup: BeautifulSoup) -> str:
    h3_tags = soup.findAll('h3')
    definitions_header = None
    for el in h3_tags:
        if el.text == 'Definitions':
            definitions_header = el
    if definitions_header == None:
        raise FutureWarning('The source metadata has moved -- please look at the Sonoma County webpage and locate it, then update the scraper with this information')
    definitions_text = definitions_header.find_parent().text
    return definitions_text

# apologies for this horror of a output type
def transform_cases(cases_tag: element.Tag) -> Dict[str, List[Dict[str, Union[str, int]]]]:
    cases = []
    cumul_cases = 0
    deaths = []
    cumul_deaths = 0
    recovered = []
    cumul_recovered = 0
    active = []
    cumul_active = 0
    rows = cases_tag.findAll('tr')[1:]
    for row in rows:
        row_cells = row.findAll(['th', 'td'])
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

    # print(deaths)
    return { 'cases': cases, 'deaths': deaths, 'recovered': recovered, 'active': active }

def transform_transmission(transmission_tag: element.Tag) -> Dict[str, int]:
    transmissions = {}
    rows = transmission_tag.findAll('tr')[1:]
    # turns the transmission categories on the page into the ones we're using
    transmission_type_conversion = {'Community': 'community', 'Close Contact': 'from_contact', 'Travel': 'travel', 'Under Investigation': 'unknown'}
    for row in rows:
        row_cells = row.findAll(['th', 'td'])
        type, number, _pct = [el.text for el in row_cells]
        if type not in transmission_type_conversion:
            raise FutureWarning('The transmission type {0} was not found in transmission_type_conversion'.format(type))
        type = transmission_type_conversion[type]
        transmissions[type] = int(number)
    return transmissions

def transform_tests(tests_tag: element.Tag) -> Dict[str, int]:
    tests = {}
    rows = tests_tag.findAll('tr')[1:]
    for row in rows:
        row_cells = row.findAll(['th', 'td'])
        result, number, _pct = [el.text for el in row_cells]
        lower_res = result.lower()
        tests[lower_res] = int(number.replace(',', ''))
    print(tests)
    return tests;

def transform_age(age_tag: element.Tag) -> Dict[str, int]:
    age_brackets = {}
    rows = age_tag.findAll('tr')[1:]
    for row in rows:
        row_cells = row.findAll(['th', 'td'])
        bracket, cases, _pct = [el.text for el in row_cells]
        age_brackets[bracket] = int(cases)
    return age_brackets

try:
    hist_cases, cases_by_source, cases_by_race, total_tests, cases_by_region, region_guide, hospitalized, underlying_cond, symptoms, cases_by_gender, underlying_cond_by_gender, hospitalized_by_gender, symptoms_female, symptoms_male, symptoms_desc, cases_by_age, symptoms_by_age, underlying_cond_by_age = tables
except ValueError as e:
    raise FutureWarning('The number of values on the page has changed -- please adjust the page')

model = {
    'name': 'Sonoma County',
    'update_time': generate_update_time(sonoma_soup),
    'source': url,
    'meta_from_source': get_source_meta(sonoma_soup),
    'meta_from_baypd': '',
    'series': transform_cases(hist_cases),
    'case_totals': {
        'transmission_cat': transform_transmission(cases_by_source),
        'age_group': transform_age(cases_by_age)
    },
    'tests_totals': {
        'tests': transform_tests(total_tests),
    }
}

# print(model)
