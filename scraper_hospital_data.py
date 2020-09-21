#!/usr/bin/env python3

"""Script for pulling down CA COVID-19 hospitalization stats"""

import click
import json
import logging
import os
import traceback
import sys
from pathlib import Path
from typing import Tuple

from covid19_sfbayarea import ca_counties
from covid19_sfbayarea.data import hospitals


all_ca_counties = sorted(ca_counties.bay_area_counties + ca_counties.other_ca_counties)


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
def main(counties: Tuple[str], output: str) -> None:

    try:
        if counties:
            out = hospitals.get_timeseries(list(counties))

        else:
            out = hospitals.get_timeseries(ca_counties.bay_area_counties)

        if not out:
            message = click.style(
                'Hospitalization data fetch came back empty ', fg='red'
            )
            click.echo(message, err=True)
            sys.exit(1)

        if output:
            parent = Path(output)
            parent.mkdir(exist_ok=True)  # if output directory does not exist, create it
            with parent.joinpath('hospital_data.json').open('w', encoding='utf-8') as f:
                json.dump(out, f, ensure_ascii=False, indent=2)

        else:
            print(json.dumps(out, indent=2))

    except Exception as error:
        message = click.style(
            'Hospitalization data fetch encountered error', fg='red'
        )
        click.echo(f'{message}: {error}', err=True)
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(level=os.getenv('LOG_LEVEL', 'WARN').upper())
    main()
