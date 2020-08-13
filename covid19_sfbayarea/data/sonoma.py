import requests
import json
import re
import dateutil.parser
from typing import List, Dict, Union
from bs4 import BeautifulSoup, element # type: ignore
from ..errors import FormatError

TimeSeriesItem = Dict[str, Union[str, int]]
TimeSeries = List[TimeSeriesItem]
UnformattedSeriesItem = Dict[str, str]
UnformattedSeries = List[UnformattedSeriesItem]

def get_section_by_title(header: str, soup: BeautifulSoup) -> element.Tag:
    """
    Takes in a header string and returns the parent element of that header
    """
    header_tag = soup.find(lambda tag: tag.name == 'h3' and header in tag.get_text())
    if not header_tag:
        raise FormatError('The header "{0}" no longer corresponds to a section'.format(header))

    return header_tag.find_parent()

def get_table(header: str, soup: BeautifulSoup) -> element.Tag:
    """
    Takes in a header and a BeautifulSoup object and returns the table under
    that header
    """
    tables = get_section_by_title(header, soup).find_all('table')
    # this lets us get the second cases table
    return tables[-1]

def get_cells(row: element.ResultSet) -> List[str]:
    """
    Gets all th and tr elements within a single tr element
    """
    return [el.text for el in row.find_all(['th', 'td'])]

<<<<<<< HEAD
<<<<<<< HEAD
def row_list_to_dict(row: List[str], headers: List[str]) -> UnformattedSeriesItem:
    """
    Takes in a list of headers and a corresponding list of cells
    and returns a dictionary associating the headers with the cells
    """
    return dict(zip(headers, row))

def parse_table(tag: element.Tag) -> UnformattedSeries:
    """
    Takes in a BeautifulSoup table tag and returns a list of dictionaries 
    where the keys correspond to header names and the values to corresponding cell values
    """
=======
def row_list_to_dict(row: List[str], headers: List[str]) -> TimeSeriesItem:
    return dict(zip(headers, row))

def parse_table(tag: element.Tag) -> TimeSeries:
>>>>>>> Refactor test and gender functions
=======
def row_list_to_dict(row: List[str], headers: List[str]) -> UnformattedSeriesItem:
    """
    Takes in a list of headers and a corresponding list of cells
    and returns a dictionary associating the headers with the cells
    """
    return dict(zip(headers, row))

def parse_table(tag: element.Tag) -> UnformattedSeries:
<<<<<<< HEAD
>>>>>>> Fix types
=======
    """
    Takes in a BeautifulSoup table tag and returns a list of dictionaries 
    where the keys correspond to header names and the values to corresponding cell values
    """
>>>>>>> Add docstrings
    rows = tag.find_all('tr')
    header = rows[0]
    body = rows[1:]
    header_cells = get_cells(header)
    body_cells = (get_cells(row) for row in body)
    return [row_list_to_dict(row, header_cells) for row in body_cells]

def parse_int(text: str) -> int:
    """
    Takes in a number in string form and returns that string in integer form 
    and handles zeroes represented as dashes
    """
    text = text.strip()
    if text == '-':
        return 0
    else:
        return int(text.replace(',', ''))

def generate_update_time(soup: BeautifulSoup) -> str:
    """
    Generates a timestamp string (e.g. May 6, 2020 10:00 AM) for when the scraper is run
    """
    update_time_text = soup.find('time', {'class': 'updated'})['datetime']
    try:
        date = dateutil.parser.parse(update_time_text)
    except ValueError:
        raise ValueError(f'Date is not in ISO 8601'
                         f'format: "{update_time_text}"')
    return date.isoformat()

def get_source_meta(soup: BeautifulSoup) -> str:
    """
    Finds the 'Definitions' header on the page and gets all of the text in it.
    """
    definitions_section = get_section_by_title('Definitions', soup)
    definitions_text = definitions_section.text
    return definitions_text.replace('\n', '/').strip()

def transform_cases(cases_tag: element.Tag) -> Dict[str, TimeSeries]:
    """
    Takes in a BeautifulSoup tag for the cases table and returns all cases
    (historic and active), deaths, and recoveries in the form:
    { 'cases': [], 'deaths': [] }
    Where each list contains dictionaries (representing each day's data)
    of form (example for cases):
    { 'date': '', 'cases': -1, 'cumul_cases': -1 }
    """
    cases = []
    cumul_cases = 0
    deaths = []
    cumul_deaths = 0

    rows = list(reversed(parse_table(cases_tag)))
    for row in rows:
        date = dateutil.parser.parse(row['Date']).date().isoformat()
        new_infected = parse_int(row['New'])
        dead = parse_int(row['Deaths'])

        cumul_cases += new_infected
        case_dict: TimeSeriesItem = { 'date': date, 'cases': new_infected, 'cumul_cases': cumul_cases }
        cases.append(case_dict)

        new_deaths = dead - cumul_deaths
        cumul_deaths = dead
        death_dict: TimeSeriesItem = { 'date': date, 'deaths': new_deaths, 'cumul_deaths': dead }
        deaths.append(death_dict)

    return { 'cases': cases, 'deaths': deaths }

def transform_transmission(transmission_tag: element.Tag) -> Dict[str, int]:
    """
    Takes in a BeautifulSoup tag for the transmissions table and breaks it into
    a dictionary of type:
    {'community': -1, 'from_contact': -1, 'travel': -1, 'unknown': -1}
    """
    transmissions = {}
    rows = parse_table(transmission_tag)
    # turns the transmission categories on the page into the ones we're using
    transmission_type_conversion = {'Community': 'community', 'Close Contact': 'from_contact', 'Travel': 'travel', 'Under Investigation': 'unknown'}
    for row in rows:
        type = row['Source']
        number = parse_int(row['Cases'])
        if type not in transmission_type_conversion:
            raise FormatError(f'The transmission type {type} was not found in transmission_type_conversion')
        type = transmission_type_conversion[type]
        transmissions[type] = number
    return transmissions

def transform_tests(tests_tag: element.Tag) -> Dict[str, int]:
    """
    Transform function for the tests table.
    Takes in a BeautifulSoup tag for a table and returns a dictionary
    """
    tests = {}
    rows = parse_table(tests_tag)
    for row in rows:
        lower_res = row['Results'].lower()
        tests[lower_res] = parse_int(row['Number'])
    return tests;

def transform_gender(tag: element.Tag) -> Dict[str, int]:
    """
    Transform function for the cases by gender table.
    Takes in a BeautifulSoup tag for a table and returns a dictionary
    in which the keys are strings and the values integers
    """
    genders = {}
    rows = parse_table(tag)
    gender_string_conversions = {'Males': 'male', 'Females': 'female'}
    for row in rows:
        gender = row['Gender']
        cases = parse_int(row['Cases'])
        if gender not in gender_string_conversions:
            raise FormatError('An unrecognized gender has been added to the gender table')
        genders[gender_string_conversions[gender]] = cases
    return genders

def transform_age(tag: element.Tag) -> TimeSeries:
    """
    Transform function for the cases by age group table.
    Takes in a BeautifulSoup tag for a table and returns a list of
    dictionaries in which the keys are strings and the values integers
    """
    categories: TimeSeries = []
    rows = parse_table(tag)
    for row in rows:
        raw_count = parse_int(row['Cases'])
        group = row['Age Group']
        element: TimeSeriesItem = {'group': group, 'raw_count': raw_count}
        categories.append(element)
    return categories

def get_unknown_race(race_eth_tag: element.Tag) -> int:
    """
    Gets the notes under the 'Cases by race and ethnicity' table to find the
    number of cases where the person's race is unknown
    """
    parent = race_eth_tag.parent
    note = parent.find('p').text
    matches = re.search(r'(\d+) \(\d{1,3}%\) missing race/ethnicity', note)
    if not matches:
        raise FormatError('The format of the note with unknown race data has changed')
    return(parse_int(matches.groups()[0]))

def transform_race_eth(race_eth_tag: element.Tag) -> Dict[str, int]:
    """
    Takes in the BeautifulSoup tag for the cases by race/ethnicity table and
    transforms it into an object of form:
    'race_eth': {'Asian': -1, 'Latinx_or_Hispanic': -1, 'Other': -1, 'White':-1, 'Unknown': -1}
    NB: These are the only races reported seperatley by Sonoma county at this time
    """
    race_cases = {
        'Asian': 0,
        'Latinx_or_Hispanic': 0,
        'Other': 0,
        'White': 0,
        'Unknown': 0
    }
    race_transform = {'Asian/Pacific Islander, non-Hispanic': 'Asian', 'Hispanic/Latino': 'Latinx_or_Hispanic', 'Other*, non-Hispanic': 'Other', 'White, non-Hispanic': 'White'}
    rows = parse_table(race_eth_tag)
    for row in rows:
        group_name = row['Race/Ethnicity']
        cases = parse_int(row['Cases'])
        if group_name not in race_transform:
            raise FormatError('The racial group {0} is new in the data -- please adjust the scraper accordingly')
        internal_name = race_transform[group_name]
        race_cases[internal_name] = cases
    race_cases['Unknown'] = get_unknown_race(race_eth_tag)
    return race_cases

def get_table_tags(soup: BeautifulSoup) -> List[element.Tag]:
    """
    Takes in a BeautifulSoup object and returns an array of the tables we need
    """
    headers = ['Cases by Date', 'Test Results', 'Cases by Source', 'Cases by Age Group', 'Cases by Gender', 'Cases by Race']
    return [get_table(header, soup) for header in headers]

def get_county() -> Dict:
    """
    Main method for populating county data .json
    """
    url = 'https://socoemergency.org/emergency/novel-coronavirus/coronavirus-cases/'
    # need this to avoid 403 error ¯\_(ツ)_/¯
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    page = requests.get(url, headers=headers)
    page.raise_for_status()
    sonoma_soup = BeautifulSoup(page.content, 'html5lib')

    hist_cases, total_tests, cases_by_source, cases_by_age, cases_by_gender, cases_by_race = get_table_tags(sonoma_soup)

    model = {
        'name': 'Sonoma County',
        'update_time': generate_update_time(sonoma_soup),
        'source': url,
        'meta_from_source': get_source_meta(sonoma_soup),
        'meta_from_baypd': 'Racial "Other" category includes "Black/African American, American Indian/Alaska Native, and Other"',
        'series': transform_cases(hist_cases),
        'case_totals': {
            'transmission_cat': transform_transmission(cases_by_source),
            'age_group': transform_age(cases_by_age),
            'race_eth': transform_race_eth(cases_by_race),
            'gender': transform_gender(cases_by_gender)
        },
        'tests_totals': {
            'tests': transform_tests(total_tests),
        },
    }
    return model

if __name__ == '__main__':
    print(json.dumps(get_county(), indent=4))
