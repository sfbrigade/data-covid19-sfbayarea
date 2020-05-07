#!/usr/bin/env python3
import requests
import json
from datetime import datetime
from typing import Dict
from bs4 import BeautifulSoup

url = 'https://socoemergency.org/emergency/novel-coronavirus/coronavirus-cases/'
page = requests.get(url)
soup = BeautifulSoup(page.content, 'html.parser')
tables = soup.findAll('table')

def generate_update_time(soup):
    update_time_text = soup.find('time').text.strip()
    # format is May 6, 2020 10:00 AM
    update_datetime = datetime.strptime(update_time_text, '%B %d, %Y %I:%M %p')
    return update_datetime.isoformat()


model = {
    'name': 'Sonoma County',
    'update_time': generate_update_time(soup),
    'source': url,

}

# for i in range(len(tables)):
#     if i >= 4: # we don't need the first three tables
#         table = tables[i]
#         print('\n\n')
#         print(table.findAll('tr'))
