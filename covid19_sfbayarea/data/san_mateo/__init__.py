import csv
import json
import requests

from datetime import datetime, date
from typing import Any, Dict, List, cast
from covid19_sfbayarea.utils import dig, parse_datetime

from .cases_by_age import CasesByAge
from .cases_by_ethnicity import CasesByEthnicity
from .cases_by_gender import CasesByGender

from .meta import Meta

from .deaths_by_age import DeathsByAge
from .deaths_by_ethnicity import DeathsByEthnicity
from .deaths_by_gender import DeathsByGender

from .time_series_cases import TimeSeriesCases
from .time_series_tests import TimeSeriesTests

from ..utils import get_data_model
from ...errors import FormatError

LANDING_PAGE = 'https://www.smchealth.org/post/san-mateo-county-covid-19-data-1'

def get_county() -> Dict:
    out = get_data_model()
    out.update(fetch_data())
    return out

def fetch_data() -> Dict:
    data : Dict = {
        'name': 'San Mateo County',
        'source_url': LANDING_PAGE,
        'meta_from_source': Meta().get_data(),
        'meta_from_baypd': """
            See power_bi_scraper.py for methods.
            San Mateo does not provide a timestamp for their last dataset
            update, so BayPD uses midnight of the latest day in the cases
            timeseries as a proxy.

            San Mateo does not provide a deaths timeseries. Instead, the deaths
            timeseries is from data published by LA Times, which appears to be
            built by saving the county's listed total each day. See more on the
            LA Times data at:
            https://github.com/datadesk/california-coronavirus-data
         """,
        'series': {
            'cases': TimeSeriesCases().get_data(),
            'deaths': get_timeseries_deaths(),
            'tests': TimeSeriesTests().get_data()
        },
        'case_totals': {
            'gender': CasesByGender().get_data(),
            'age_group': CasesByAge().get_data(),
            'race_eth': CasesByEthnicity().get_data()
        },
        'death_totals': {
            'gender': DeathsByGender().get_data(),
            'age_group': DeathsByAge().get_data(),
            'race_eth': DeathsByEthnicity().get_data()
        }
    }
    last_updated = most_recent_case_time(data)
    data.update({ 'update_time': last_updated.isoformat() })
    return data


def most_recent_case_time(data: Dict[str, Any]) -> datetime:
    most_recent_cases = cast(Dict[str, str], dig(data, ['series', 'cases', -1]))
    return parse_datetime(most_recent_cases['date'])


def get_timeseries_deaths() -> List:
    """
    Get a timeseries of deaths by day from LA Times (since the county does not
    publish a timeseries). Their data appears to track the day-to-day totals
    from the county, while other sources we have used do not. Notably, the
    state no longer publishes this data at all.

    Because the LA Times data has generally matched the county dashboard, it
    should be fairly consistent with the rest of our data. View the dataset in
    a browser at:
    https://github.com/datadesk/california-coronavirus-data/blob/master/latimes-county-totals.csv
    """
    timeseries: List[Dict[str, Any]] = []
    url = 'https://raw.githubusercontent.com/datadesk/california-coronavirus-data/master/latimes-county-totals.csv'
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        lines = (line.decode('utf-8') for line in response.iter_lines())
        for row in csv.DictReader(lines):
            if row['county'] == 'San Mateo':
                timeseries.append({
                    'date': row['date'],
                    'deaths': int(row['new_deaths'] or 0),
                    'cumul_deaths': int(row['deaths'] or 0),
                })

    timeseries.sort(key=lambda row: row['date'])

    # Sanity-check the results.
    total = 0
    for entry in timeseries:
        total += entry['deaths']
        if total != entry['cumul_deaths']:
            raise FormatError(f'Death totals do not match in {entry}')

    return timeseries


if __name__ == '__main__':
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(get_county(), indent=4))
