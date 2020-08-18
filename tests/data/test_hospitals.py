#!/usr/bin/env python3

"""
Tests for functions in hospitals.py
"""

from covid19_sfbayarea.data import hospitals


SAMPLE_RECORD = {
    'icu_covid_confirmed_patients': 4.0,
    'icu_suspected_covid_patients': 2.0,
    'hospitalized_covid_patients': None,
    'hospitalized_suspected_covid_patients': 9.0,
    'icu_available_beds': 16.0,
    'rank': 0.0573088,
    'county': 'Marin',
    'hospitalized_covid_confirmed_patients': 10.0,
    '_id': 103,
    'all_hospital_beds': None,
    'todays_date': '2020-03-30T00:00:00'
}

SAMPLE_OUTPUT = {
    'icu_covid_confirmed_patients': 4,
    'icu_suspected_covid_patients': 2,
    'hospitalized_covid_patients': -1,
    'hospitalized_suspected_covid_patients': 9,
    'icu_available_beds': 16,
    'county': 'Marin',
    'hospitalized_covid_confirmed_patients': 10,
    '_id': 103,
    'all_hospital_beds': -1,
    'report_date': '2020-03-30'
}


def test_truncate_ts():
    ts = SAMPLE_RECORD.get("todays_date")
    trunc_ts = hospitals.truncate_ts(ts)
    assert trunc_ts == "2020-03-30"


def test_convert_null():
    converted = hospitals.convert_null(SAMPLE_RECORD)
    assert converted.get("hospitalized_covid_patients") == -1
    assert converted.get("all_hospital_beds") == -1
    assert converted.get("icu_available_beds") == 16.0


def test_floats_to_ints():
    converted = hospitals.floats_to_ints(SAMPLE_RECORD)
    assert type(converted.get("icu_covid_confirmed_patients")) is int
    assert converted.get("icu_covid_confirmed_patients") == int(4)
    assert converted.get("icu_available_beds") == int(16)


def test_standardize_data():
    standardized = hospitals.standardize_data(SAMPLE_RECORD)
    assert standardized == SAMPLE_OUTPUT
