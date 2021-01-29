import json

from datetime import datetime
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

from ..ckan import Ckan
from ..utils import get_data_model

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
            San Mateo does not provide a timestamp for their last dataset update,
            so BayPD uses midnight of the latest day in the cases timeseries as a proxy.

            San Mateo does not provide a deaths timeseries. Instead, the deaths
            timeseries is pulled from Californa’s statewide data portal at
            https://data.ca.gov/.
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
    Get a timeseries of deaths by day from the state (since they county does
    not publish this info). View the dataset in a browser at:
    https://data.ca.gov/dataset/covid-19-cases/resource/926fd08f-cc91-4828-af38-bd45de97f8c3
    """
    state_api = Ckan('https://data.ca.gov')
    records = state_api.data('926fd08f-cc91-4828-af38-bd45de97f8c3',
                             filters={'county': 'San Mateo'},
                             sort='date asc')
    return [
        {
            'date': parse_datetime(record['date']).date().isoformat(),
            'deaths': int(record['newcountdeaths']),
            'cumul_deaths': int(record['totalcountdeaths'])
        }
        for record in records
    ]


if __name__ == '__main__':
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(get_county(), indent=4))
