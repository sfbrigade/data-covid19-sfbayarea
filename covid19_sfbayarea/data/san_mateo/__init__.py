import json

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
            timeseries is pulled from CHHS’s statewide data portal at
            https://data.chhs.ca.gov/. Deaths for which a date is not yet
            determined are included in the latest date of the timeseries.
            Please note that, because data is coming from disparate sources,
            total count of deaths may not add up between the timeseries (from
            CHHS) and the demographic data (from the county).
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
    https://data.chhs.ca.gov/dataset/covid-19-time-series-metrics-by-county-and-state/resource/046cdd2b-31e5-4d34-9ed3-b48cdbc4be7a
    """
    state_api = Ckan('https://data.chhs.ca.gov')
    records = state_api.data('046cdd2b-31e5-4d34-9ed3-b48cdbc4be7a',
                             filters={'area': 'San Mateo'},
                             sort='date asc')
    # Rows in this dataset include `deaths` and `reported_deaths`, neither of
    # which is a total. The data dictionary does not describe the specifics
    # around these, but they appear to be deaths attributed to a given day and
    # then the day there actually *reported* to the state.
    total_deaths = 0
    timeseries: List[Dict[str, Any]] = []
    unknown_date_deaths = 0
    for record in records:
        deaths = int(float(record['deaths']))
        # There is one entry with no date for records that do not (yet) have an
        # identified date. Hold on to it for adding at the end.
        if record['date']:
            total_deaths += deaths
            timeseries.append({
                'date': parse_datetime(record['date']).date().isoformat(),
                'deaths': deaths,
                'cumul_deaths': total_deaths
            })
        else:
            unknown_date_deaths = deaths

    # Attribute unknown date deaths to today.
    if unknown_date_deaths:
        total_deaths += unknown_date_deaths
        today = date.today().isoformat()
        latest_entry = timeseries[-1]
        if latest_entry['date'] == today:
            latest_entry['deaths'] += unknown_date_deaths
            latest_entry['cumul_deaths'] += total_deaths
        else:
            timeseries.append({
                'date': today,
                'deaths': unknown_date_deaths,
                'cumul_deaths': total_deaths
            })

    return timeseries


if __name__ == '__main__':
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(get_county(), indent=4))
