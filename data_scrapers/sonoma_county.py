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
        raise FutureWarning('The webpage has changed and the source metadata has moved -- please look at the Sonoma County webpage and locate it, then update the scraper with this information')
    definitions_text = definitions_header.find_parent().text
    return definitions_text

model = {
    'name': 'Sonoma County',
    'update_time': generate_update_time(sonoma_soup),
    'source': url,
    'meta_from_source': get_source_meta(sonoma_soup)
}

# cases, source, tests, age, sex, region, hospitalized = tables
# transform_cases(cases)
print(get_source_meta(sonoma_soup))
