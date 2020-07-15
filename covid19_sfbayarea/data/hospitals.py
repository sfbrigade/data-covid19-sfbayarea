#!/usr/bin/env python3

import json
import logging
import requests
from datetime import datetime
from dateutil import tz
from typing import Any, Dict, List, Union

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
RESULTS_LIMIT = 50

# For the output data
SERIES_NAME = "Hospitalization"
BAYPD_META = "This data was pulled from the data.ca.gov CKAN Data API"

logging.basicConfig(level=logging.INFO)


def get_county(county: str) -> Dict:
    """Return data just for the selected county. Include field notes.
    This is basically an alias for `get_timeseries()` provided for consistency.
    """
    data = get_timeseries(county)

    return data


def get_timeseries(county: str = "all") -> Dict:
    """Fetch all pages of timeseries data from API endpoint"""
    ts_data: Dict[str, Union[str, List]] = {}
    timeseries: List[Dict[str, Any]] = []

    # Add header data
    if county == "all":
        ts_data["name"] = f"{SERIES_NAME} - All CA Counties"
    else:
        ts_data["name"] = f"{SERIES_NAME} - {county.title()} County"

    now = datetime.now(tz.tzutc()).isoformat()
    ts_data["update_time"] = now
    ts_data["source_url"] = HOSPITALS_LANDING_PAGE
    ts_data["meta_from_baypd"] = BAYPD_META

    # Call may be made without params on subsequent calls
    params: Dict[str, Union[int, str]] = {
        "resource_id": HOSPITALS_RESOURCE_ID,
        "limit": RESULTS_LIMIT
    }

    if county != "all":
        params["q"] = county.title()

    url = CAGOV_BASEURL + CAGOV_API

    try:
        # Handle the pagination
        while True:
            # pass params if we don't have timeseries data yet
            if not timeseries:
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
            timeseries.extend(records)

            results_count = len(timeseries)
            logging.info(f"Got {results_count} results out of {total} ...")
            more = results.get("_links").get("next")

            # Don't ask for more pages than there are
            if more and results_count < total:
                url = CAGOV_BASEURL + more

            else:
                break

        ts_data["series"] = timeseries
        logging.info("Collected all pages")

    except AttributeError:
        logging.exception("Error parsing response")

    except requests.exceptions.RequestException:
        logging.exception("Error fetching from API")

    finally:
        return ts_data


if __name__ == "__main__":
    """When run as a script, prints all data to stdout"""
    print(json.dumps(get_timeseries(), indent=4))
