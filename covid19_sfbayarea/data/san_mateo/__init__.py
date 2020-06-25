import json

from typing import Dict

from .cases_by_age import CasesByAge
from .cases_by_ethnicity import CasesByEthnicity
from .cases_by_gender import CasesByGender

from .deaths_by_age import DeathsByAge
from .deaths_by_ethnicity import DeathsByEthnicity
from .deaths_by_gender import DeathsByGender

from .time_series_cases import TimeSeriesCases
from .time_series_tests import TimeSeriesTests

LANDING_PAGE = 'https://www.smchealth.org/post/san-mateo-county-covid-19-data-1'
def get_county() -> Dict:
    return {
        'name': 'San Mateo County',
        'source_url': LANDING_PAGE,
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

if __name__ == '__main__':
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(get_county(), indent=4))
