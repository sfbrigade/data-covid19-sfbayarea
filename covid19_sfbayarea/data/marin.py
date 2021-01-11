from typing import List, Dict, Iterable
from datetime import datetime
from ..errors import FormatError
from ..utils import assert_equal_sets, parse_datetime
from .utils import SocrataApi


API_IDS = {
    # This timeseries includes cases, deaths, and hospitalizations (not tests)
    'cases': 'wg8s-i3c7',
    'tests': 'kr8c-izzb',

    # Cumulative demographics for age, race/ethnicity, and gender across cases,
    # hospitalizations, and deaths are all published in one dataset.
    # Breakdowns by transmission vector and comorbidities are not available.
    # NOTE: Cases (but not hospitalizations or deaths) are also available as a
    # separate timeseries for each demographic breakdown, but we do not
    # use those at the moment. Most other counties do not publish demographic
    # timeseries.
    'demographics': 'uu8g-ckxh'

    # Marin does not publish demographic breakdowns for testing.
}


def get_county() -> Dict:
    """Main method for populating county data"""
    api = SocrataApi('https://data.marincounty.org/')
    notes = ('This data only accounts for Marin residents and does not '
             'include inmates at San Quentin State Prison. '
             'The tests timeseries only includes the number of tests '
             'performed and not how many were positive or negative. '
             'Demographic breakdowns for testing are not available.')

    return {
        'name': 'Marin',
        'update_time': get_latest_update(api).isoformat(),
        # The county's data dashboard is at:
        #   https://coronavirus.marinhhs.org/surveillance
        # Which links to the data portal category with the data sets we
        # actually use at:
        #   https://data.marincounty.org/browse?q=covid
        'source_url': 'https://coronavirus.marinhhs.org/surveillance',
        'meta_from_source': '',
        'meta_from_baypd': notes,
        'series': {
            'cases': get_timeseries_cases(api),
            'deaths': get_timeseries_deaths(api),
            'tests': get_timeseries_tests(api),
        },
        'case_totals': get_case_totals(api),
        'death_totals': get_death_totals(api),
        # Marin does not currently provide demographic breakdowns for
        # testing, so no test totals right now.
    }


def get_latest_update(api: SocrataApi) -> datetime:
    times = [parse_datetime(api.metadata(api_id)['dataUpdatedAt'])
             for api_id in API_IDS.values()]
    return max(*times)


def get_api_cases(api: SocrataApi, disposition: str) -> Iterable[dict]:
    # https://data.marincounty.org/Public-Health/COVID-19-Case-Disposition/wg8s-i3c7
    data = api.resource(API_IDS['cases'], params={'$order': 'test_date ASC'})
    total = 0
    for entry in data:
        if entry['status'] == disposition:
            total += 1
            yield entry

    # Sanity-check that we filtered the `status` column on a real value.
    if total == 0:
        raise FormatError(f'There were no cases with `status == "{disposition}"`')


def get_timeseries_cases(api: SocrataApi) -> List[dict]:
    return [
        {
            'date': parse_datetime(entry['test_date']).date().isoformat(),
            'cases': int(entry['new_confirmed_cases']),
            'cumul_cases': int(entry['cumulative_case_count']),
        }
        for entry in get_api_cases(api, 'Confirmed')
    ]


def get_timeseries_deaths(api: SocrataApi) -> List[dict]:
    return [
        {
            'date': parse_datetime(entry['test_date']).date().isoformat(),
            'deaths': int(entry['new_confirmed_cases']),
            'cumul_deaths': int(entry['cumulative_case_count']),
        }
        for entry in get_api_cases(api, 'Death')
    ]


def get_timeseries_tests(api: SocrataApi) -> List[dict]:
    # https://data.marincounty.org/Public-Health/Marin-County-COVID-19-Testing-Data-CDPH-/kr8c-izzb
    data = api.resource(API_IDS['tests'], params={'$order': 'date ASC'})

    total = 0
    result = []
    for entry in data:
        # Percent positive tests is also available in this timeseries when:
        #     variable == 'test_pos_nopris_7day_total_!no_lag'
        # Unfortunately the naming and documentation implies this is the
        # positivity rate over the past 7 days, so it's probably not accurate
        # to calculate an absolute number of positive/negative tests from it.
        if entry['variable'] != 'total_tests_nopris_!no_lag':
            continue

        # Since the same column is used for percent positive and tests, the
        # total tests comes through as a float rather than an int.
        value = float(entry['value'])
        tests = int(value)
        assert tests == value

        total += tests
        result.append({
            'date': parse_datetime(entry['date']).date().isoformat(),
            'tests': tests,
            'positive': -1,
            'negative': -1,
            'pending': -1,
            'cumul_tests': total,
            'cumul_pos': -1,
            'cumul_neg': -1,
            'cumul_pend': -1,
        })

    return result


def get_demographic_totals(api: SocrataApi, demographic: str) -> List[Dict]:
    # https://data.marincounty.org/Public-Health/COVID-19-Cumulative-Demographics/uu8g-ckxh
    data = api.resource(API_IDS['demographics'])
    prefix = f'{demographic} - '
    prefix_length = len(prefix)

    result = []
    for entry in data:
        if entry['grouping'].startswith(prefix):
            entry = entry.copy()
            entry['grouping'] = entry['grouping'][prefix_length:]
            result.append(entry)

    # Sanity-check that we filtered the `status` column on a real value.
    if len(result) == 0:
        raise FormatError(f'There were no cases with demographic "{demographic}"')

    return result


def get_case_totals(api: SocrataApi) -> Dict:
    return {
        'gender': get_cases_by_gender(api),
        'age_group': get_cases_by_age(api),
        'race_eth': get_cases_by_race(api),
        # These are not currently provided by Marin:
        # 'underlying_cond': get_cases_by_condition(api),
        # 'transmission_cat': get_cases_by_transmission(api),
    }


def get_cases_by_gender(api: SocrataApi) -> Dict:
    data = get_demographic_totals(api, 'Gender')
    result = {row['grouping'].lower(): int(row['cumulative'])
              for row in data}

    # Sanity-check the output at least has male/female.
    try:
        assert 'male' in result
        assert 'female' in result
    except AssertionError:
        raise FormatError('Missing explicity male/female gender categories '
                          f'for cases, got: {list(result.keys())}')

    return result


def get_cases_by_age(api: SocrataApi) -> List[Dict]:
    data = get_demographic_totals(api, 'Age')
    return [{'group': row['grouping'], 'raw_count': int(row['cumulative'])}
            for row in data]


def get_cases_by_race(api: SocrataApi) -> Dict:
    data = get_demographic_totals(api, 'Race')
    mapping = {
        'american indian/alaska native': 'Native_Amer',
        'asian': 'Asian',
        'black/african american': 'African_Amer',
        'hispanic/latinx': 'Latinx_or_Hispanic',
        'multiracial': 'Multiple_Race',
        'native hawaiian/pacific islander': 'Pacific_Islander',
        'unknown': 'Unknown',
        'other': 'Other',
        'white': 'White',
    }
    assert_equal_sets(mapping.keys(), (row['grouping'].lower() for row in data))
    result = {mapping[row['grouping'].lower()]: int(row['cumulative'])
              for row in data}
    return result


def get_cases_by_condition(api: SocrataApi) -> Dict:
    # NO DATA
    raise NotImplementedError()


def get_cases_by_transmission(api: SocrataApi) -> Dict:
    # NO DATA
    raise NotImplementedError()


def get_death_totals(api: SocrataApi) -> Dict:
    return {
        'gender': get_deaths_by_gender(api),
        'age_group': get_deaths_by_age(api),
        'race_eth': get_deaths_by_race(api),
        # These are not currently provided by Marin:
        # 'underlying_cond': get_deaths_by_condition(api),
        # 'transmission_cat': get_deaths_by_transmission(api),
    }


def get_deaths_by_gender(api: SocrataApi) -> Dict:
    data = get_demographic_totals(api, 'Gender')
    result = {row['grouping'].lower(): int(row['deaths'])
              for row in data}

    # Sanity-check the output at least has male/female.
    try:
        assert 'male' in result
        assert 'female' in result
    except AssertionError:
        raise FormatError('Missing explicity male/female gender categories '
                          f'for deaths, got: {list(result.keys())}')

    return result


def get_deaths_by_age(api: SocrataApi) -> List[Dict]:
    data = get_demographic_totals(api, 'Age')
    return [{'group': row['grouping'], 'raw_count': int(row['deaths'])}
            for row in data]


def get_deaths_by_race(api: SocrataApi) -> Dict:
    data = get_demographic_totals(api, 'Race')
    mapping = {
        'american indian/alaska native': 'Native_Amer',
        'asian': 'Asian',
        'black/african american': 'African_Amer',
        'hispanic/latinx': 'Latinx_or_Hispanic',
        'multiracial': 'Multiple_Race',
        'native hawaiian/pacific islander': 'Pacific_Islander',
        'unknown': 'Unknown',
        'other': 'Other',
        'white': 'White',
    }
    assert_equal_sets(mapping.keys(), (row['grouping'].lower() for row in data))
    result = {mapping[row['grouping'].lower()]: int(row['deaths'])
              for row in data}
    return result


def get_deaths_by_condition(api: SocrataApi) -> Dict:
    # NO DATA
    raise NotImplementedError()


def get_deaths_by_transmission(api: SocrataApi) -> Dict:
    # NO DATA
    raise NotImplementedError()
