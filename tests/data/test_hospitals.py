#!/usr/bin/env python3

"""
Tests for functions in hospitals.py
"""

from covid19_sfbayarea.data import hospitals


def test_truncate_ts():
    ts = "2020-03-29T00:00:00"
    trunc_ts = hospitals.truncate_ts(ts)
    assert trunc_ts == "2020-03-29"


def test_convert_null():
    record = {
        'icu_covid_confirmed_patients': 4.0,
        'icu_suspected_covid_patients': 2.0,
        'hospitalized_covid_patients': None,
        'hospi talized_suspected_covid_patients': 9.0,
        'icu_available_beds': 16.0,
        'rank': 0.0573088,
        'county': 'Marin',
        'hospitalized_covid_confirmed_patients': 10.0,
        '_id': 103,
        'all_hospital_beds': None,
        'report_date': '2020-03-30'
    }

    converted = hospitals.convert_null(record)
    assert converted.get("hospitalized_covid_patients") == -1
    assert converted.get("all_hospital_beds") == -1
    assert converted.get("icu_available_beds") == 16.0
