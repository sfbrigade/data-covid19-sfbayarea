from bs4 import BeautifulSoup
from typing import Tuple, Dict
import requests
import re
import pandas as pd
import datetime

def get_html(url: str) -> BeautifulSoup:
    """
    Takes in a url string and returns a BeautifulSoup object representing the page
    """
    page = requests.get(url)
    return BeautifulSoup(page.content, 'html.parser')

def find_tags(soup: BeautifulSoup) -> Tuple[int, int, str]:
    """
    Takes in a BeautifulSoup object and returns a tuple of the number of cases (int), the number of deaths (int) and the time that the data was updated(str)
    """
    helpful_links_box = soup.find(id='helpful-links')

    cases_regex = re.compile('Total Positive Cases: ([\d,]+)')
    deaths_regex = re.compile('Deaths: ([\d,]+)')
    time_regex = re.compile('updated daily at (\d{1,2}:\d{1,2} (AM|PM))')

    cases_html = soup.find('p', text=cases_regex)
    deaths_html = soup.find('p', text=deaths_regex)
    time_html = soup.find('p', text=time_regex)

    num_cases = int(re.match(cases_regex, cases_html.text).group(1))
    num_deaths = int(re.match(deaths_regex, deaths_html.text).group(1))
    time_updated = re.match(time_regex, time_html.text).group(1)
    return (num_cases, num_deaths, time_updated)

def format_single_digits(number: int) -> str:
    """
    Adds a leading zero to one digit numbers to make them line up with the existing data
    """
    if number < 10:
        return "0{0}".format(number)
    else:
        return str(number)

def format_year(year: int) -> int:
    """
    Turns a year into its short form e.g. 2020 -> 20
    """
    # get the short form of the year
    return year - 2000

def gen_date() -> str:
    """
    Generates today's date in MM/DD/YY format
    """
    today = datetime.datetime.today()
    month = format_single_digits(today.month)
    day = format_single_digits(today.day)
    year = format_year(today.year)

    return "{0}/{1}/{2}".format(month, day, year)

def format_time(timestamp: str) -> str:
    """
    Formats time in the format HH:MM:SS AM/PM
    """
    time, suffix = timestamp.split(' ')
    if len(time) == 4: # time is less than 10:00 w/ length 5
        time = '0{0}'.format(time)
    return '{0}:00 {1}'.format(time, suffix)

def gen_new_row_dict(dataframe: pd.DataFrame, num_cases: int, num_deaths: int, time_updated: str) -> Dict:
    """
    Generates a new row for a dataframe in dict format and calculates the new cases and deaths for the new data
    """
    cases_idx = 2
    deaths_idx = 4

    prev_cases = dataframe.iloc[-1, cases_idx]
    prev_deaths = dataframe.iloc[-1, deaths_idx]

    return {
        'date': gen_date(),
        'time_updated': format_time(time_updated),
        'total_positive_cases': num_cases,
        'new_daily_cases': (num_cases - prev_cases),
        'total_deaths': num_deaths,
        'new_daily_deaths': (num_deaths - prev_deaths),
        'city': 'San Francisco',
        'county': 'San Francisco',
        'state': 'CA'
    }

url = 'https://www.sfdph.org/dph/alerts/coronavirus.asp'
sfdph_soup = get_html(url)
cases, deaths, time = find_tags(sfdph_soup)

covid_data = pd.read_csv('data/covid_19_sf.csv', dtype={'total_positive_cases': 'Int64', 'total_deaths': 'Int64'})
new_row = gen_new_row_dict(covid_data, cases, deaths, time)
covid_data = covid_data.append(new_row, ignore_index=True)
covid_data.to_csv('data/covid_19_sf.csv', index=False)
