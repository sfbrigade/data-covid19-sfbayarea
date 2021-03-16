#!/usr/bin/env python3

import logging
from datetime import datetime
from dateutil import tz
from dateutil.parser import parse
from typing import Any, Dict, List, Union

from covid19_sfbayarea.utils import friendly_county
from .ckan import Ckan

# This module fetches COVID-19 hospital data from the CA.gov open data portal.
# The input data is fetched from an API endpoint, and appears to be updated at
# least daily.  Hospital stats, such as number of available ICU beds, are
# provided at the county level.


# URLs and APIs
HOSPITALS_LANDING_PAGE = "https://data.chhs.ca.gov/dataset/covid-19-hospital-data"
CAGOV_BASEURL = "https://data.chhs.ca.gov"
HOSPITALS_RESOURCE_ID = "47af979d-8685-4981-bced-96a6b79d3ed5"
RESULTS_LIMIT = 200

# For the output data
SERIES_NAME = "CA COVID-19 Hospitalization Data"
BAYPD_META = "This data was pulled from the data.ca.gov CKAN Data API"

logger = logging.getLogger(__name__)


# =======================
# Data Manipulation Utils
# =======================


def truncate_timestamp(timestamp: str) -> str:
    """Truncate a timestamp to an ISO 8601-formatted date"""
    truncated_timestamp = parse(timestamp).date().isoformat()
    return truncated_timestamp


def convert_null(record: Dict) -> Dict:
    """Convert any null values to -1"""
    for k, v in record.items():

        if v is None:
            record[k] = -1

        else:
            continue

    return record


def floats_to_ints(record: Dict) -> Dict:
    """Convert zero-point floats for numeric fields to ints"""
    fields: List = [
        "all_hospital_beds",
        "hospitalized_covid_confirmed_patients",
        "hospitalized_covid_patients",
        "hospitalized_suspected_covid_patients",
        "icu_available_beds",
        "icu_covid_confirmed_patients",
        "icu_suspected_covid_patients",
    ]

    for field in fields:
        val = record.get(field)

        if val is None:
            continue

        else:
            try:
                record[field] = int(val)

            except ValueError:
                # Handle floats stored as strings
                record[field] = int(float(val))

    return record


# ===================
# Data Transformation
# ===================


def standardize_data(record: Dict) -> Dict:
    """Transform certain data fields to make them conform to BAPD style

    Specifically:
    - truncate timestamps to ISO 8601-formatted dates
    - remove "rank" field, if it exists
    - convert all 'null' values to -1
    - cast zero-point floats as int

    Also, the key 'todays_date' is converted to 'date' for clarity.
    """
    record["date"] = truncate_timestamp(record.pop("todays_date"))
    record.pop("rank", None)
    record = convert_null(record)
    record = floats_to_ints(record)

    return record


def process_data(series: List, counties: List) -> Dict:
    """Transform the timeseries data (a list of dicts) into a dict
    with keys for each county name, and a list of dicts with records
    for that particular county"""
    processed_series: Dict[str, Union[str, Any]] = {}

    for county in counties:
        county_name = friendly_county(county)
        county_records = [
            standardize_data(record) for record in series
            if record.get("county") == county_name
        ]

        processed_series[county] = county_records

    return processed_series


# ====================
# Data API Interaction
# ====================


def get_timeseries(counties: List) -> Dict:
    """Fetch all pages of timeseries data from API endpoint"""
    timeseries_data: Dict[Any, Any] = {}

    now = datetime.now(tz.tzutc()).isoformat(timespec="minutes")

    # Add header data
    timeseries_data["name"] = SERIES_NAME
    timeseries_data["update_time"] = now
    timeseries_data["source_url"] = HOSPITALS_LANDING_PAGE
    timeseries_data["meta_from_baypd"] = BAYPD_META

    state_api = Ckan(CAGOV_BASEURL)
    data_raw = state_api.data(HOSPITALS_RESOURCE_ID,
                              limit=RESULTS_LIMIT,
                              yield_meta=True)
    meta = next(data_raw)
    records = list(data_raw)

    timeseries_data["meta_from_source"] = []
    for field in meta["fields"]:
        if field.get("id") == "todays_date":
            field = {
                "info": {
                    "notes": "Report date",
                    "type_override": "date",
                    "label": "Date"
                },
                "type": "date",
                "id": "date"
            }

        timeseries_data["meta_from_source"].append(field)

    # standardize the format of the data and key it by county name
    timeseries_data["series"] = process_data(records, counties)

    return timeseries_data
