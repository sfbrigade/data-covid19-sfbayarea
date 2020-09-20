#!/usr/bin/env python3

"""Script for pulling down CA COVID-19 hospitalization stats"""

import click
import json
import logging
import os
import traceback
from pathlib import Path
from typing import Tuple

from covid19_sfbayarea.data import hospitals
from covid19_sfbayarea.utils import cli_friendly_county


# prep lists of counties the user can choose to filter the data
# format county strings so they're command line-friendly
with open("covid19_sfbayarea/counties.json") as f:
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

    try:
        if counties:
            out = hospitals.get_timeseries(counties)

        else:
            out = hospitals.get_timeseries(bay_area_counties)

        if output:
            parent = Path(output)
            parent.mkdir(exist_ok=True)  # if output directory does not exist, create it
            with parent.joinpath('hospital_data.json').open('w', encoding='utf-8') as f:
                json.dump(out, f, ensure_ascii=False, indent=2)

        else:
            print(json.dumps(out, indent=2))

    except Exception as error:
        message = click.style(
            'Hospitalization data fetch failed', fg='red'
        )
        click.echo(f'{message}: {error}', err=True)
        traceback.print_exc()


if __name__ == '__main__':
    logging.basicConfig(level=os.getenv('LOG_LEVEL', 'WARN').upper())
    main()
