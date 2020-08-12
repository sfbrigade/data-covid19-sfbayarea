"""
Grabs data from the 'FAQ Content' CSV and turns it into nice JSON: a main faq object containing an array of Section objects, each Section Object in turn holding an array of Question objects consisting of question, answer and related link/s, as so:
    [
        {
          'Q': 'What are the symptoms of COVID-19?',
          'A': 'Symptoms of COVID-19 include coughing and shortness of breath. Additionally, a person showing two or more of the following symptoms may have the virus: fever, repeated shaking with chills, muscle pain, headache, sore throat, new loss of taste or smell.',
          'link': 'https://www.cdc.gov/coronavirus/2019-ncov/symptoms-testing/symptoms.html'
        },
    .
    .
    .
    ]
    etc
In addition to an array of Question objects, each Section incorporates its title and a 'last updated' date value. For the Python intermediary stage (between CSV stream  and JSON) we will create a hierarchy of nested dictionaries and lists equivalent to the JSON objects and arrays.

Execute with: $ python3 scraper_faq_sheet.py path/to/where/I/want/faq_json
"""

#!/usr/bin/env python3
import requests
import json
import csv
import datetime
import sys
from typing import Iterable, Dict, List, Any


# function to grab data from a google sheet + return as reader object
def google_sheet_csv_data(sheet: str, gid: str) -> Iterable[List[str]]:
    url = f'https://docs.google.com/spreadsheets/d/{sheet}/export'
    response = requests.get(url, params={
        'format': 'csv',
        'id': sheet,
        'gid': gid
    })
    response.raise_for_status()
    return csv.reader(response.iter_lines(decode_unicode=True))


# Pass faq Content sheet id and gid to function
_reader = google_sheet_csv_data(
    '1_wBXS62S5oBQrwetGc8_-dFvDjEmNqzqHwUeP-DzkYs',
    '1318925039'
 )

# Date, to be updated each time the program runs, in UTC
date = datetime.datetime.utcnow().strftime('%Y-%m-%d')

# Create the main FAQ dictionary
# Create a list to contain our Section objects
# Place the Sections list inside the main FAQ dictionary
faq_dict = {}
sections_list: List[Dict] = []
faq_dict['faqItems'] = sections_list

# Ensure only first two columns in each row are used
# Now arrange the Sections and Questions in a JSON-friendly way
for index, row in enumerate(_reader):
    rowtype, rowval, *_rest = row
    if rowtype == 'Category':   # We don't need this row
        pass
    elif rowtype == 'Section Head':
        section: Dict[str, Any] = {}   # Create a dictionary for a Section
        sections_list.append(section)   # Add new Section to Sections list
        section['title'] = rowval   # Give the Section its title
        section['lastUpdatedAt'] = date   # a 'last updated' value
        questions_list: List[Dict] = []   # Create list to contain questions
        section['qa'] = questions_list   # add new Questions list to its Section
    elif rowtype == 'Q':
        question = {}   # Create new Question dictionary
        question['q'] = rowval   # the Question's title
        questions_list.append(question)   # Append Question to given Section
    elif rowtype == 'A':   # Now the same for Answers & Links
        question['a'] = rowval
    elif rowtype == 'link':
        question['url'] = rowval
    elif rowtype == '':   # Some safeguards
        pass
    elif rowval and not rowtype:
        raise ValueError(f'row {index} has a value but no description!')
    else:
        raise ValueError(f'Unknown row header: "{rowtype}"')

# Create formatted json file; write to file object ready to be assigned destination at execution
faq_json = json.dumps(faq_dict, indent=2)
sys.stdout.write(faq_json)
