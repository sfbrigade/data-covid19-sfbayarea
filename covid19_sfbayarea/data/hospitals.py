#!/usr/bin/env python3

import json
import requests
from typing import Dict, List

# This module fetches COVID-19 hospital data from the CA.gov open data portal.
# The input data is fetched from an API endpoint, and appears to be updated at
# least daily.  Hospital stats, such as number of available ICU beds, are
# provided at the county level. This module's top-level function takes a county
# as an arg and returns the data for that county as JSON.

# TODO Document data model

# URLs and APIs
HOSPITALS_LANDING_PAGE = "https://data.ca.gov/dataset/covid-19-hospital-data#"
CAGOV_API_BASEURL = "https://data.ca.gov/api/3/action/datastore_search"
HOSPITALS_RESOURCE_ID = "42d33765-20fd-44b8-a978-b083b7542225"
RESULTS_LIMIT = 50


def get_timeseries() -> List:
    """Fetch all pages of timeseries data from API endpoint"""
    timeseries = []

    params = {"resource_id": HOSPITALS_RESOURCE_ID, "limit": RESULTS_LIMIT}
    r = requests.get(CAGOV_API_BASEURL, params=params).json()

    # TODO get notes for each field

    records = r["result"].get("records")
    timeseries.extend(records)

    return timeseries


if __name__ == "__main__":
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(get_timeseries(), indent=4))
