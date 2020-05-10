#!/usr/bin/env python3
import requests
import json
from datetime import datetime
from typing import List, Dict
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

# def transform_cases(cases_tag: element.Tag) -> List[Dict]:
#     cases = []
#     cumul_cases = 0
#     deaths = []
#     cumul_deaths = 0
#     recovered = []
#     cumul_recovered = 0
#     rows = cases_tag.findAll('tr')[1:]
#     for row in rows:
#         row_cells = row.findAll(['th', 'td'])
#         date = row_cells[0].text.replace('/', '-')
#         infected, new_infected, dead, recoveries = [int(el.text) for el in row_cells[1:]]
#         print(infected)
#         cumul_cases += new_infected
#         cases.append({ 'date': date, 'cases': infected, 'cumul_cases': cumul_cases})

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

    model = {
    'name': 'Sonoma County',
    'update_time': generate_update_time(sonoma_soup),
    'source': url,
    'meta_from_source': get_source_meta(sonoma_soup),
    'meta_from_baypd': '',
    'series': {},
    'case_totals': {
        'transmission_cat': transform_transmission(source)
    }
}

try:
    cases, source, tests, age, sex, region, regions, hospitalized, underlying, symptoms = tables
except ValueError as e:
    raise FutureWarning('The number of values on the page has changed -- please ')
# transform_cases(cases)
