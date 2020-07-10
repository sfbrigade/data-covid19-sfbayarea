#!/usr/bin/env python3

import json
import logging
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
CAGOV_BASEURL = "https://data.ca.gov"
CAGOV_API = "/api/3/action/datastore_search"
HOSPITALS_RESOURCE_ID = "42d33765-20fd-44b8-a978-b083b7542225"
RESULTS_LIMIT = 50

logging.basicConfig(level=logging.INFO)


def get_county(county: str) -> Dict:
    """Return data just for the selected county. Include field notes."""
    data = get_timeseries(county)

    return data


def get_timeseries(county: str = "all") -> Dict:
    """Fetch all pages of timeseries data from API endpoint"""
    ts_data = {}
    timeseries = []

    params = {"resource_id": HOSPITALS_RESOURCE_ID, "limit": RESULTS_LIMIT}

    if county != "all":
        params.update({"q": county})

    url = CAGOV_BASEURL + CAGOV_API

    try:
        # Handle the pagination
        while True:
            if params:
                r = requests.get(url, params=params)
            else:
                r = requests.get(url)

            r.raise_for_status()
            results = r.json().get("result")
            total = int(results.get("total"))

            # Get notes only on the first pull
            if not ts_data.get("field_notes"):
                notes = results.get("fields")
                ts_data["field_notes"] = notes

            else:
                pass

            records = results.get("records")
            timeseries.extend(records)

            results_count = len(timeseries)
            logging.info(f"Got {results_count} results out of {total} ...")
            more = results.get("_links").get("next")

            # Don't ask for more pages than there are
            if more and results_count < total:
                url = CAGOV_BASEURL + more
                params = None

            else:
                break

        ts_data["timeseries"] = timeseries
        logging.info("Collected all pages")

        return ts_data

    except AttributeError:
        logging.exception("Error parsing response")

    except requests.Exceptions.RequestExceptions:
        logging.exception("Error fetching from API")


if __name__ == "__main__":
    """ When run as a script, prints the data to stdout"""
    print(json.dumps(get_timeseries("San Francisco"), indent=4))
