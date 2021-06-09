import requests
import json
import dateutil.parser
from datetime import datetime, timezone
from typing import List, Dict, Union
from bs4 import BeautifulSoup, element # type: ignore
from ..errors import FormatError
from ..utils import assert_equal_sets

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

def transform_transmission(
        transmission_tag: element.Tag,
        total_cases: int,
        standardize: bool = True
) -> Dict[str, int]:
    """
    Takes in a BeautifulSoup tag for the transmissions table and breaks it into
    a dictionary. Fields are either the original from data source or are normalized
    into groups consistent with other datasets, by using `standardize=True` (default).

    Parameters
    ----------
    transmission_tag : element.Tag
        A BeautifulSoup table tag containing transmission source data

    total_cases: int
        The total number of COVID-19 cases reported by the county

    standardize: bool
        Flag to standardize the data into BAPD-consistent fields

    Returns
    -------
    transmissions : dict
        A dictionary keyed by transmission source, with calculated 
        number of cases as the values. By default the fields are:
        {'community': -1, 'from_contact': -1, 'travel': -1, 'unknown': -1}
    """
    transmissions = {}
    rows = parse_table(transmission_tag)

    # turns the transmission categories on the page into the ones we're using
    transmission_type_conversion = {
        'congregate care': 'congregate_care',
        'health care': 'health_care',
        'household': 'household',
        'large gathering': 'gathering_large',
        'other': 'other',
        'small gathering': 'gathering_small',
        'travel': 'travel',
        'unknown': 'unknown',
        'workplace': 'workplace'
    }

    assert_equal_sets(transmission_type_conversion.keys(),
                      (row['Exposure Location'].lower() for row in rows),
                      description='Transmission types')

    for row in rows:
        type = row['Exposure Location'].lower()
        percent_cases = float(row['All Time'].replace('%', '')) / 100
        case_count = int(percent_cases * total_cases)
        type = transmission_type_conversion[type]
        transmissions[type] = case_count

    if standardize:
        # standardize categories into groups consistent with other datasets
        # those groups are "from_contact", "travel", "unknown" and "community"

        from_contact_categories = [
            "congregate_care",
            "household",
            "workplace",
            "gathering_small"
        ]

        community_categories = [
            "health_care",
            "gathering_large",
            "other"
        ]

        standardized_transmissions = {
            "from_contact": sum(transmissions[category]
                                for category in from_contact_categories),
            "community": sum(transmissions[category]
                             for category in community_categories),
            "travel": transmissions.get("travel", 0),
            "unknown": transmissions.get("unknown", 0)
        }

        # check that we have all the math right
        assert sum(standardized_transmissions.values()) == sum(transmissions.values())
        transmissions = standardized_transmissions

    else:
        pass

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
    assert_equal_sets(gender_string_conversions.keys(),
                      (row['Gender'] for row in rows),
                      description='Genders')
    for row in rows:
        gender = row['Gender']
        cases = parse_int(row['Cases'])
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

def transform_race_eth(race_eth_tag: element.Tag) -> Dict[str, int]:
    """
    Takes in the BeautifulSoup tag for the cases by race/ethnicity table and
    transforms it into an object of form:
    'race_eth': {'Asian': -1, 'Latinx_or_Hispanic': -1, 'Other': -1, 'White':-1, 'Unknown': -1}
    """
    race_cases = {
        'Asian': 0,
        'Latinx_or_Hispanic': 0,
        'Other': 0,
        'White': 0,
        'Unknown': 0,
        'Multiple_Race': 0,
        'African_Amer': 0,
    }

    race_transform = {
        'Asian, non-Hispanic': 'Asian',
        'Hispanic / Latino': 'Latinx_or_Hispanic',
        'White, non-Hispanic': 'White',
        'Multi-racial, non-Hispanic': 'Multiple_Race',
        'Black/African American, non-Hispanic': 'African_Amer',
        'American Indian/Alaska Native, non-Hispanic': 'Native_Amer',
        'Native Hawaiian and other Pacific Islander, non-Hispanic': 'Pacific_Islander',
        'Other, non-Hispanic': 'Other',
        'Unknown': 'Unknown',
    }

    rows = parse_table(race_eth_tag)
    assert_equal_sets(race_transform.keys(),
                      (row['Race/Ethnicity'] for row in rows),
                      description='Racial groups')

    for row in rows:
        group_name = row['Race/Ethnicity']
        cases = parse_int(row['Cases'])
        internal_name = race_transform[group_name]
        race_cases[internal_name] = cases
    return race_cases


def get_table_tags(soup: BeautifulSoup) -> List[element.Tag]:
    """
    Takes in a BeautifulSoup object and returns an array of the tables we need
    """
    headers = [
        'Cases by Date',
        'Test Results',
        'Proportion of Cases Attributable to Specific Exposure Locations',
        'Cases by Age Group',
        # 'Cases by Gender',   Data by gender no longer available
        'Cases by Race'
    ]
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

    hist_cases, total_tests, cases_by_source, cases_by_age, cases_by_race = get_table_tags(sonoma_soup)

    # calculate total cases to compute values from percentages
    # we previously summed the cases across all genders, but with gender data unavailable,
    # now we calculate the the sum of the cases across all age groups
    total_cases = sum([int(group['raw_count']) for group in transform_age(cases_by_age)])

    meta_from_baypd = (
        "On or about 2021-06-03, Sonoma County stopped providing case totals "
        "by gender. Null values are inserted as placeholders for consistency."
    )

    model = {
        'name': 'Sonoma County',
        'update_time': datetime.now(timezone.utc).isoformat(),
        'source_url': url,
        'meta_from_source': get_source_meta(sonoma_soup),
        'meta_from_baypd': meta_from_baypd,
        'series': transform_cases(hist_cases),
        'case_totals': {
            'transmission_cat': transform_transmission(cases_by_source, total_cases),
            'transmission_cat_orig': transform_transmission(cases_by_source, total_cases, standardize=False),
            'age_group': transform_age(cases_by_age),
            'race_eth': transform_race_eth(cases_by_race),
            # 'gender': transform_gender(cases_by_gender)     # Gender breakdown is no longer available
            'gender': {'male': -1, 'female': -1}              # Insert a placeholder for compatibility
        },
        'tests_totals': {
            'tests': transform_tests(total_tests),
        },
    }
    return model

if __name__ == '__main__':
    print(json.dumps(get_county(), indent=4))
