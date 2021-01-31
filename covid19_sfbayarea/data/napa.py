from collections import defaultdict
from datetime import date, datetime
import re
import requests
from typing import Dict, List, Iterable
from ..errors import FormatError
from ..utils import assert_equal_sets, PACIFIC_TIME
from .arcgis import ArcGisFeatureServer


# Most data comes from this ArcGIS server.
ARCGIS_SERVER_URL = 'https://services1.arcgis.com/Ko5rxt00spOfjMqj'
# The 'CaseDataDemographics' service is used for most of our data; it lists
# *every case* the county knows about!
CASES_SERVICE = 'CaseDataDemographics'
# Tests data comes from a Google Sheet proxies through livestories.com.
TESTS_SPREADSHEET_URL = 'https://legacy.livestories.com/dataset.json?dashId=6014a050c648870017b6dc84'


def get_county() -> Dict:
    """
    Get data for Santa Napa County.
    """
    notes = ('Cases are dated by the time a test specimen was collected (i.e. '
             'the earliest known time of a case\'s infection). In some cases, '
             'the specimen collection date is unknown, and the test result '
             'time is used instead. '
             'Napa also provides a narrow range of race/ethnicity groups than '
             'most other counties. Many groups (e.g. african-american, asian, '
             'pacific islander) are collected under "other". '
             'Additionally, Napa County does not provide information about '
             'comorbidities/underlying conditions or methods of transmission. '
             'Test data is only provided on a weekly basis; we attribute '
             'tests to the last day of the week in which the test was taken. '
             'Test data is updated on Tuesdays, but a test week is '
             'Sunday-Saturday.')

    api = ArcGisFeatureServer(ARCGIS_SERVER_URL)

    return {
        'name': 'Napa',
        'update_time': get_latest_update(api).isoformat(),
        # The dashboard loads data from ArcGIS and from several Google Sheets
        # proxied through livestories.com (see URLs in constants above).
        'source_url': 'https://legacy.livestories.com/s/v2/coronavirus-report-for-napa-county-ca/9065d62d-f5a6-445f-b2a9-b7cf30b846dd/',
        'meta_from_source': '',
        'meta_from_baypd': notes,
        'series': {
            'cases': get_timeseries_cases(api),
            'deaths': get_timeseries_deaths(api),
            'tests': get_timeseries_tests(),
        },
        'case_totals': get_case_totals(api),
        'death_totals': get_death_totals(api),
        # Napa does not currently provide demographic breakdowns for testing,
        # so no test totals right now.
    }


def get_latest_update(api: ArcGisFeatureServer) -> datetime:
    data = api.query(CASES_SERVICE,
                     outFields='MAX(EditDate_1) as edit_date')
    result = next(data)
    return datetime.fromtimestamp(result['edit_date'] / 1000, tz=PACIFIC_TIME)


def get_timeseries_cases(api: ArcGisFeatureServer) -> List:
    """
    Get a timeseries of cases.

    Some cases in Napa's data have a test result date, but not a test specimen
    collection date. Napa's dashboard works around this by showing cases by
    test result date.

    However, we and Wikimedia Commons take a different approach: We list cases
    by specimen collection date. If it's not available, we fall back to the
    test result date as the next most accurate thing.
    """
    dated = {
        row['DtLabCollect']: row['count']
        for row in api.query(CASES_SERVICE,
                             where='DtLabCollect <> NULL',
                             outFields='DtLabCollect,COUNT(*) AS count',
                             groupByFieldsForStatistics='DtLabCollect',
                             orderByFields='DtLabCollect asc')
    }

    undated = {
        row['DtLabResult']: row['count']
        for row in api.query(CASES_SERVICE,
                             where='DtLabCollect IS NULL',
                             outFields='DtLabResult,COUNT(*) AS count',
                             groupByFieldsForStatistics='DtLabResult',
                             orderByFields='DtLabResult asc')
    }

    dates = sorted(set(list(dated.keys()) + list(undated.keys())))

    # Cumulative counts are provided by the county, but because of how we are
    # mixing date regimes, we need to calculate our own.
    total = 0
    timeseries  = []
    for case_date in dates:
        count = dated.get(case_date, 0) + undated.get(case_date, 0)
        total += count
        timeseries.append({
            'date': date.fromtimestamp(case_date / 1000).isoformat(),
            'cases': count,
            'cumul_cases': total,
        })

    return timeseries


def get_timeseries_deaths(api: ArcGisFeatureServer) -> List:
    """
    Get a timeseries of deaths.
    """
    # First build a lookup table for records with no collection date.
    data = api.query(CASES_SERVICE,
                     where='DtDeath <> NULL',
                     outFields='DtDeath,COUNT(*) AS deaths',
                     groupByFieldsForStatistics='DtDeath',
                     orderByFields='DtDeath asc')
    total = 0
    deaths = []
    for entry in data:
        total += entry['deaths']
        deaths.append({
            'date': date.fromtimestamp(entry['DtDeath'] / 1000).isoformat(),
            'deaths': entry['deaths'],
            'cumul_deaths': total
        })

    return deaths


def get_timeseries_tests() -> List:
    # Testing data comes from a Google Sheet proxies through livestories.com,
    # rather than ArcGIS.
    data = requests.get(TESTS_SPREADSHEET_URL).json()

    # Validate that the series are what we expect.
    if 'number of tests' not in data['series'][0]['name'].lower():
        raise FormatError('Tests data series 0 should have been # of tests, '
                          f'but got: "{data["series"][0]["name"]}"')
    if 'positivity rate' not in data['series'][1]['name'].lower():
        raise FormatError('Tests data series 1 should have been positivity, '
                          f'but got: "{data["series"][1]["name"]}"')

    # X values are formatted like "2020 11/8 - 11/14"
    x_pattern = re.compile(r'''
        ^
        (\d+)                          # Year
        \s+
        (\d+)/(\d+)                    # Month/Day for start of week
        \s*[\-\u00a0\u2010-\u2015]\s*  # Dash (of various sorts) optionally surrounded by spaces
        (\d+)/(\d+)                    # Month/Day for end of week
    ''', re.IGNORECASE | re.VERBOSE)
    x_values = data['categories']
    test_counts = data['series'][0]['data']
    test_positives = data['series'][1]['data']

    total = 0
    total_positive = 0
    timeseries = []
    for index, week in enumerate(x_values):
        x_data = x_pattern.match(week)
        if not x_data:
            raise FormatError(f'Could not parse week {index} name: "{week}"')

        result_date = date(int(x_data.group(1)),
                           int(x_data.group(4)),
                           int(x_data.group(5)))
        count = test_counts[index]['y']
        total += count
        rate = test_positives[index]['y']
        positive_count = round(count * rate / 100)
        total_positive += positive_count
        timeseries.append({
            'date': result_date.isoformat(),
            'tests': count,
            'positive': positive_count,
            'cumul_tests': total,
            'cumul_pos': total_positive,
            # This field isn't really standard, but it's here because it's the
            # "true" value, while `positive` is a rounded calculation.
            'positivity': rate,
        })

    return timeseries


def format_gender_results(data: Iterable[Dict]) -> Dict[str, int]:
    """
    Format the output of an API call for counts of rows by gender.
    """
    # We can't use a comprehension here because values are not completely
    # standardized across rows (e.g. both "unknown" and None == "unknown").
    result: Dict[str, int] = defaultdict(int)
    for row in data:
        key = (row['Sex'] or 'unknown').strip().lower()
        result[key] += row['count']
    try:
        assert 'male' in result
        assert 'female' in result
    except AssertionError:
        raise FormatError('Missing explicity male/female gender categories, '
                          f'got: {list(result.keys())}')
    return result


def format_race_results(data: Iterable[Dict]) -> Dict[str, int]:
    """
    Format the output of an API call for counts of rows by gender.
    """
    # Napa groups several other race/ethnicity groups we normally break out
    # into "other".
    mapping = {
        'hispanic': 'Latinx_or_Hispanic',
        'non-hispanic white': 'White',
        'other': 'Other',
        'unknown': 'Unknown'
    }

    # We can't use a comprehension here because values are not completely
    # standardized across rows (e.g. both "unknown" and None == "unknown").
    result: Dict[str, int] = defaultdict(int)
    for row in data:
        key = (row['RaceEthn'] or 'unknown').strip().lower()
        result[key] += row['count']

    # Validate expected keys and remap them to our keys.
    assert_equal_sets(mapping.keys(), result.keys())
    return {mapping[key]: value
            for key, value in result.items()}


def format_age_results(data: Iterable[Dict]) -> List[Dict]:
    # NOTE: values aren't totally standardized, so we can't use a comprehension
    # here (we need need to add the results of some rows together).
    groups: Dict[str, int] = defaultdict(int)
    for row in data:
        key = (row['AgeGroup'] or 'unknown').strip()
        # Remove leading zeroes from ages, e.g. "05-09"
        ages = [age.strip().lstrip('0') or '0'
                for age in key.split('-')]
        key = '-'.join(ages)
        groups[key] += row['count']

    # Sort groups by the int value of the first age (e.g. by `5` in `"5-9"`).
    def sortable_group(group: Dict) -> int:
        return int(group['group'].split('-')[0].strip('+'))

    results = [{'group': key, 'raw_count': value}
               for key, value in groups.items()]
    return sorted(results, key=sortable_group)


def get_case_totals(api: ArcGisFeatureServer) -> Dict:
    return get_totals(api, count_by='*')


def get_death_totals(api: ArcGisFeatureServer) -> Dict:
    return get_totals(api, count_by='DtDeath')


def get_totals(api: ArcGisFeatureServer, count_by: str) -> Dict:
    return {
        'gender': format_gender_results(
            api.query(
                CASES_SERVICE,
                outFields=f'Sex,COUNT({count_by}) AS count',
                groupByFieldsForStatistics='Sex'
            )
        ),
        'age_group': format_age_results(
            api.query(
                CASES_SERVICE,
                outFields=f'AgeGroup,COUNT({count_by}) AS count',
                groupByFieldsForStatistics='AgeGroup'
            )
        ),
        'race_eth': format_race_results(
            api.query(
                CASES_SERVICE,
                outFields=f'RaceEthn,COUNT({count_by}) AS count',
                groupByFieldsForStatistics='RaceEthn'
            )
        ),
        # NOTE: Napa does not appear to have any source of information about
        # comorbidities/underlying conditions or type of transmission, so no
        # `underlying_cond` or `transmission_cat` fields.
    }
