from covid19_sfbayarea.data import scrapers
from numbers import Number
import os
import pytest
from pytest_voluptuous import S, Partial, Exact
from typing import List
from voluptuous.validators import Date, Match, Url
from voluptuous.schema_builder import Optional
import warnings


# These tests only run if the environment variable `LIVE_TESTS` is set.
# The value should be `*` to test all scrapers:
#
#    $ LIVE_TESTS='*' python -m pytest -v .
#
# Or a comma-separated list to test only particular scrapers, e.g:
#
#    $ LIVE_TESTS='alameda,san_francisco' python -m pytest -v .
#
LIVE_TESTS = os.getenv('LIVE_TESTS', '').lower().strip()
TEST_COUNTIES: List[str] = []
if LIVE_TESTS in ('1', 't', 'true', '*', 'all'):
    TEST_COUNTIES = list(scrapers.keys())
elif LIVE_TESTS:
    TEST_COUNTIES = [county
                     for county in (county.strip()
                                    for county in LIVE_TESTS.split(','))
                     if county]


# A validator for an ISO 8601 datetime. This is really similar to
# voluptuous.validators.Datetime, but it accepts time zone offsets (e.g.
# `+0300`) instead of just `Z` (the short-form version of `+0000`).
DatetimeIso = Match(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(.\d+)?(Z|[+\-]\d\d:?\d\d)$')


@pytest.mark.parametrize('county', TEST_COUNTIES)
def test_scraper_output_format_is_valid(county: str) -> None:
    if county not in scrapers:
        pytest.fail(f'Unknown county: "{county}"')
    try:
        result = scrapers[county].get_county()
    except Exception as error:
        message = (f'Cannot validate "{county}" format because it failed to '
                   f'scrape: {error}')
        warnings.warn(message)
        pytest.skip(message)
        return

    # All the totals sections have basically the same schema.
    totals_section = Partial({
        Optional('gender'): Exact({
            # Gender must always at least have male and female.
            'male': int,
            'female': int,
            # Any remaining values should be integers.
            Optional(str): int
        }),
        Optional('age_group'): [Exact({
            'group': str,
            'raw_count': int
        })],
        Optional('race_eth'): Exact({
            # We have some mostly-standard keys, but not all scrapers/data
            # sources conform to them. Just validate that values are integers.
            str: int
        }),
        Optional('transmission_cat'): Exact({
            # The keys here are not standardized.
            str: int
        })
    })

    assert S({
        'name': str,
        'update_time': DatetimeIso,
        'source_url': Url,
        'meta_from_source': str,
        'meta_from_baypd': str,
        'series': Exact({
            'cases': [Exact({
                'date': Date(),
                Optional('cases'): int,
                Optional('cumul_cases'): int
            })],
            'deaths': [Exact({
                'date': Date(),
                Optional('deaths'): int,
                Optional('cumul_deaths'): int
            })],
            Optional('tests'): [Partial({
                'date': Date(),
                str: Number
            })]
        }),
        'case_totals': totals_section,
        Optional('death_totals'): totals_section,
        Optional('population_totals'): totals_section
    }) <= result
