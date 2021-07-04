from datetime import datetime
import logging
from typing import Dict, List
from ..errors import FormatError
from ..utils import assert_equal_sets, parse_datetime
from .socrata import SocrataApi

logger = logging.getLogger(__name__)


API_IDS = {
    # Timeseries
    'cases': '6cnm-gchg',
    'deaths': 'tg4j-23y2',
    'tests': 'dvgc-tzgq',

    # Case demographics
    'cases_by_gender': 'ibdk-7rf5',
    'cases_by_age': 'ige8-ixqu',
    'cases_by_race': 'ccm2-45w3',
    # No data on cases by comorbidities/conditions.
    'cases_by_transmission': 'xar3-th86',

    # Death demographics
    'deaths_by_gender': 'v49w-v4a7',
    'deaths_by_age': 'pg8z-gbgv',
    'deaths_by_race': 'nd69-4zii',
    'deaths_by_condition': 'mejj-pzbm',
    # No data on deaths by transmission type.

    # Santa Clara does not publish demographic breakdowns for testing. (There
    # are breakdowns by facility and location.)
}


def get_county() -> Dict:
    """
    Get data for Santa Clara County.
    """
    api = SocrataApi('https://data.sccgov.org/')
    notes = ('Santa Clara does not report pending tests in its data, so '
             '`series.tests[].pending` will always be -1. '
             'An "outbreak" (in the `transmission_cat` breakdown) is defined '
             'as 3+ cases linked to exposures at a particular location/event '
             '(usually a workplace) like a factory, construction site, '
             'restaurant, etc. Santa Clara does not distinguish cases with an '
             'unkown transmission vector from community spread, so unknown '
             'and community spread cases are both categorized as "unknown" '
             'and "community" is set to -1. '
             'In race/ethnicity breakdowns, American Indian/Alaska Native and '
             'people who identify as multi-racial are included in the "other" '
             'category.')

    return {
        'name': 'Santa Clara',
        'update_time': get_latest_update(api).isoformat(),
        # The county's data dashboard is at:
        #   https://www.sccgov.org/sites/covid19/Pages/dashboard.aspx
        # Which links to the data portal category with the data sets we
        # actually use at:
        #   https://data.sccgov.org/browse?category=COVID-19
        'source_url': 'https://www.sccgov.org/sites/covid19/Pages/dashboard.aspx',
        'meta_from_source': '',
        'meta_from_baypd': notes,
        'series': {
            'cases': get_timeseries_cases(api),
            'deaths': get_timeseries_deaths(api),
            'tests': get_timeseries_tests(api),
        },
        'case_totals': get_case_totals(api),
        'death_totals': get_death_totals(api),
        # Santa Clara does not currently provide demographic breakdowns for
        # testing, so no test totals right now.
    }


def get_latest_update(api: SocrataApi) -> datetime:
    times = [parse_datetime(api.metadata(api_id)['dataUpdatedAt'])
             for api_id in API_IDS.values()]
    return max(*times)


def get_timeseries_cases(api: SocrataApi) -> List[dict]:
    # https://data.sccgov.org/COVID-19/COVID-19-case-counts-by-date/6cnm-gchg
    data = api.resource(API_IDS['cases'], params={'$order': 'date ASC'})
    return [
        {
            'date': parse_datetime(entry['date']).date().isoformat(),
            'cases': int(entry['new_cases']),
            'cumul_cases': int(entry['total_cases']),
        }
        for entry in data
    ]


def get_timeseries_deaths(api: SocrataApi) -> List[dict]:
    data = api.resource(API_IDS['deaths'], params={'$order': 'date ASC'})
    result = []
    for index, entry in enumerate(data):
        if 'date' not in entry:
            logger.warn(f'Row {index} of deaths data (id: "{API_IDS["deaths"]}") has no `date` field')
            continue

        result.append({
            'date': parse_datetime(entry['date']).date().isoformat(),
            # This is "total" because the data is broken down into deaths at
            # long-term care facilities (e.g. nursing homes) vs. elsewhere. We
            # do not surface that data here yet because most other counties
            # don't provide it.
            'deaths': int(entry['total']),
            'cumul_deaths': int(entry['cumulative']),
        })

    if len(result) == 0:
        raise FormatError(f'No valid rows in deaths data (id: "{API_IDS["deaths"]}")')

    return result


def get_timeseries_tests(api: SocrataApi) -> List[dict]:
    # https://data.sccgov.org/COVID-19/COVID-19-testing-by-date/dvgc-tzgq
    data = api.resource(API_IDS['tests'], params={'$order': 'collection_date ASC'})

    total = 0
    total_positive = 0
    total_negative = 0
    result = []
    for entry in data:
        tests = int(entry['total'])
        positive = int(entry['post_rslt'])
        negative = int(entry['neg_rslt'])
        total += tests
        total_positive += positive
        total_negative += negative
        result.append({
            'date': parse_datetime(entry['collection_date']).date().isoformat(),
            'tests': tests,
            'positive': positive,
            'negative': negative,
            'pending': -1,
            'cumul_tests': total,
            'cumul_pos': total_positive,
            'cumul_neg': total_negative,
            'cumul_pend': -1,
        })

    return result


def get_case_totals(api: SocrataApi) -> Dict:
    return {
        'gender': get_cases_by_gender(api),
        'age_group': get_cases_by_age(api),
        'race_eth': get_cases_by_race(api),
        # 'underlying_cond': get_cases_by_condition(api),
        'transmission_cat': get_cases_by_transmission(api),
    }


def get_cases_by_gender(api: SocrataApi) -> Dict:
    # https://data.sccgov.org/COVID-19/COVID-19-cases-by-gender/ibdk-7rf5
    data = api.resource(API_IDS['cases_by_gender'])
    result = {row['gender'].lower(): int(row['count'])
              for row in data}
    try:
        assert 'male' in result
        assert 'female' in result
    except AssertionError:
        raise FormatError('Missing explicity male/female gender categories '
                          f'for cases, got: {list(result.keys())}')
    return result


def get_cases_by_age(api: SocrataApi) -> List[Dict]:
    # https://data.sccgov.org/COVID-19/COVID-19-cases-by-age-group/ige8-ixqu
    # There is also a detailed breakdown by individual year for ages 0-13 at:
    # https://data.sccgov.org/COVID-19/COVID-19-cases-among-children-by-age/dxgq-7kuf
    data = api.resource(API_IDS['cases_by_age'])
    return [{'group': row['age_group'], 'raw_count': int(row['count'])}
            for row in data]


def get_cases_by_race(api: SocrataApi) -> Dict:
    # https://data.sccgov.org/COVID-19/COVID-19-cases-by-race-ethnicity/ccm2-45w3
    data = api.resource(API_IDS['cases_by_race'])
    mapping = {
        'african american': 'African_Amer',
        'asian': 'Asian',
        'latino': 'Latinx_or_Hispanic',
        'native hawaiian & other pacific islander': 'Pacific_Islander',
        'white': 'White',
        'other': 'Other',
        'unknown': 'Unknown'
    }
    assert_equal_sets(mapping.keys(), (row['race_eth'].lower() for row in data))
    result = {mapping[row['race_eth'].lower()]: int(row['count'])
              for row in data}
    # These are included in "other".
    result['Native_Amer'] = -1
    result['Multiple_Race'] = -1
    return result


def get_cases_by_condition(api: SocrataApi) -> Dict:
    # NO DATA
    raise NotImplementedError()


def get_cases_by_transmission(api: SocrataApi) -> Dict:
    # https://data.sccgov.org/COVID-19/COVID-19-cases-by-method-of-transmission/xar3-th86
    data = api.resource(API_IDS['cases_by_transmission'])
    mapping = {
        # NOTE: In this parlance, an "outbreak" is 3+ cases linked to exposures
        # at a particular location/event -- usually a workplace like a factory,
        # construction site, restaurant, etc.
        # http://sccgov.iqm2.com/Citizens/FileOpen.aspx?Type=4&ID=203728&MeetingID=12796
        # https://www.cdph.ca.gov/Programs/CID/DCDC/Pages/Electronic-Case-Reporting-eCR.aspx
        'Outbreak Associated': 'outbreak_associated',
        'Contact to a Case': 'from_contact',
        'Travel': 'travel',
        'Unknown/Presumed Community Transmission': 'unknown',
    }

    assert_equal_sets(mapping.keys(), (row['category'] for row in data))
    result = {mapping[row['category']]: int(row['counts'])
              for row in data}
    # Santa Clara does not distinguish unkown from community spread, so we've
    # counted all cases as community spread.
    result['community'] = -1
    return result


def get_death_totals(api: SocrataApi) -> Dict:
    return {
        'gender': get_deaths_by_gender(api),
        'age_group': get_deaths_by_age(api),
        'race_eth': get_deaths_by_race(api),
        'underlying_cond': get_deaths_by_condition(api),
        # 'transmission_cat': get_deaths_by_transmission(api),
    }


def get_deaths_by_gender(api: SocrataApi) -> Dict:
    # https://data.sccgov.org/COVID-19/Deaths-with-COVID-19-by-gender/v49w-v4a7
    data = api.resource(API_IDS['deaths_by_gender'])
    result = {row['gender'].lower(): int(row['counts'])
              for row in data}
    try:
        assert 'male' in result
        assert 'female' in result
    except AssertionError:
        raise FormatError('Missing explicity male/female gender categories '
                          f'for deaths, got: {list(result.keys())}')
    return result


def get_deaths_by_age(api: SocrataApi) -> List[Dict]:
    # https://data.sccgov.org/COVID-19/Deaths-with-COVID-19-by-age-group/pg8z-gbgv
    data = api.resource(API_IDS['deaths_by_age'])
    return [{'group': row['age_group'], 'raw_count': int(row['count'])}
            for row in data]


def get_deaths_by_race(api: SocrataApi) -> Dict:
    # https://data.sccgov.org/COVID-19/Deaths-with-COVID-19-by-race-ethnicity/nd69-4zii
    data = api.resource(API_IDS['deaths_by_race'])
    mapping = {
        'african american': 'African_Amer',
        'asian': 'Asian',
        'latino': 'Latinx_or_Hispanic',
        'native hawaiian & other pacific islander': 'Pacific_Islander',
        'white': 'White',
        'other': 'Other',
        'unknown': 'Unknown'
    }
    assert_equal_sets(mapping.keys(), (row['race_eth'].lower() for row in data))
    result = {mapping[row['race_eth'].lower()]: int(row['counts'])
              for row in data}
    # These are included in "other".
    result['Native_Amer'] = -1
    result['Multiple_Race'] = -1
    return result


def get_deaths_by_condition(api: SocrataApi) -> Dict:
    # https://data.sccgov.org/COVID-19/Deaths-with-COVID-19-by-comorbidity-status/mejj-pzbm
    data = api.resource(API_IDS['deaths_by_condition'])
    mapping = {
        '1 or more comorbidities': 'greater_than_1',
        'none': 'none',
        'unknown': 'unknown',
    }

    assert_equal_sets(mapping.keys(), (row['comorbidities'].lower() for row in data))
    return {mapping[row['comorbidities'].lower()]: int(row['counts'])
            for row in data}


def get_deaths_by_transmission(api: SocrataApi) -> Dict:
    # NO DATA
    raise NotImplementedError()
