#!/usr/bin/env python3

"""Script for pulling down CA COVID-19 hospitalization stats"""

import click
import json
from typing import Tuple
from covid19_sfbayarea.utils import cli_friendly_county


# prep lists of counties the user can choose to filter the data
# format county strings so they're command line-friendly
with open("counties.json") as f:
    ca_county_list = json.load(f)

bay_area_counties = [
    cli_friendly_county(county) for county in ca_county_list.get("Bay Area")
]

other_ca_counties = [
    cli_friendly_county(county) for county in ca_county_list.get("Other CA")
]

all_ca_counties = bay_area_counties + other_ca_counties


@click.command(
    help="Pull down COVID-19-related hospitalization data "
         "from the California Dept. of Public Health"
)
@click.argument(
    "counties",
    metavar='[COUNTY]...',
    nargs=-1,
    type=click.Choice(all_ca_counties, case_sensitive=False)
)
@click.option(
    '--output',
    metavar='PATH',
    help='write output file to this directory'
)
def main(counties: Tuple[str, ...], output: str) -> None:
    print(counties)


if __name__ == '__main__':
    main()
