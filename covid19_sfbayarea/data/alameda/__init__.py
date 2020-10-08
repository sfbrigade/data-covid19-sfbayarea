import json

from datetime import datetime
from dateutil import tz
from typing import Any, Dict, cast
from .utils import dig

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

LANDING_PAGE = 'https://covid-19.acgov.org/data.page'

def get_county() -> Dict:
    out = get_data_model()
    out.update(fetch_data())
    return out

def fetch_data() -> Dict:
    data : Dict = {
        'name': 'Alameda County',
        'source_url': LANDING_PAGE,
        'meta_from_source': Meta().get_data(),
        'meta_from_baypd': """
            See power_bi_scraper.py for methods.
            Alameda does not provide a timestamp for their last dataset update,
            so BayPD uses midnight of the latest day in the cases timeseries as a proxy.
         """,
        'series': {
            'cases': TimeSeriesCases().get_data(),
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
    pacific_time = tz.gettz('America/Los_Angeles')
    # Offset by 8 hours to ensure the correct day is shown
    start_of_day_pacific = datetime.strptime(most_recent_cases['date'] + '-8', '%Y-%m-%d-%H')
    return start_of_day_pacific.astimezone(pacific_time)

if __name__ == '__main__':
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(get_county(), indent=4))
