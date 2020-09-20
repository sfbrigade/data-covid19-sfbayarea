#!/usr/bin/env python3

import logging
import requests
from datetime import datetime
from dateutil import tz
from dateutil.parser import parse
from typing import Any, Dict, List, Union

from covid19_sfbayarea.utils import friendly_county

# This module fetches COVID-19 hospital data from the CA.gov open data portal.
# The input data is fetched from an API endpoint, and appears to be updated at
# least daily.  Hospital stats, such as number of available ICU beds, are
# provided at the county level. This module's top-level function takes a county
# as an arg and returns the data for that county as JSON.


# URLs and APIs
HOSPITALS_LANDING_PAGE = "https://data.ca.gov/dataset/covid-19-hospital-data#"
CAGOV_BASEURL = "https://data.ca.gov"
CAGOV_API = "/api/3/action/datastore_search"
HOSPITALS_RESOURCE_ID = "42d33765-20fd-44b8-a978-b083b7542225"
RESULTS_LIMIT = 200

# For the output data
SERIES_NAME = "CA COVID-19 Hospitalization Data"
BAYPD_META = "This data was pulled from the data.ca.gov CKAN Data API"

logger = logging.getLogger(__name__)


# =======================
# Data Manipulation Utils
# =======================


def truncate_ts(ts: str) -> str:
    """Truncate a timestamp to an ISO 8601-formatted date"""
    trunc_ts = parse(ts).date().isoformat()
    return trunc_ts


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
            record[field] = int(val)

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

    Also, the key 'todays_date' is converted to 'report_date' for clarity.
    """
    record["report_date"] = truncate_ts(record.pop("todays_date"))
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

        processed_series[county_name] = county_records

    return processed_series


# ====================
# Data API Interaction
# ====================


def get_timeseries(counties: List) -> Dict:
    """Fetch all pages of timeseries data from API endpoint"""
    ts_data: Dict[Any, Any] = {}
    timeseries_raw: List[Dict[str, Any]] = []

    now = datetime.now(tz.tzutc()).isoformat(timespec="minutes")

    # Add header data
    ts_data["name"] = SERIES_NAME
    ts_data["update_time"] = now
    ts_data["source_url"] = HOSPITALS_LANDING_PAGE
    ts_data["meta_from_baypd"] = BAYPD_META

    # Call may be made without params on subsequent calls
    params: Dict[str, Union[int, str]] = {
        "resource_id": HOSPITALS_RESOURCE_ID,
        "limit": RESULTS_LIMIT
    }

    url = CAGOV_BASEURL + CAGOV_API

    try:
        # Handle the pagination
        while True:
            # pass params if we don't have timeseries data yet
            if not timeseries_raw:
                r = requests.get(url, params=params)

            else:
                r = requests.get(url)

            r.raise_for_status()
            results = r.json().get("result")
            total = int(results.get("total"))

            # Get notes only on the first pull
            if not ts_data.get("meta_from_source"):
                notes = results.get("fields")
                ts_data["meta_from_source"] = notes

            else:
                pass

            records = results.get("records")
            timeseries_raw.extend(records)

            results_count = len(timeseries_raw)
            logger.info(f"Got {results_count} results out of {total} ...")
            more = results.get("_links").get("next")

            # Don't ask for more pages than there are
            if more and results_count < total:
                url = CAGOV_BASEURL + more

            else:
                break
        logger.info("Collected all pages")

        # standardize the format of the data and key it by county name
        ts_data["series"] = process_data(timeseries_raw, counties)

    except AttributeError:
        logger.exception("Error parsing response")

    except requests.exceptions.RequestException:
        logger.exception("Error fetching from API")

    finally:
        return ts_data
