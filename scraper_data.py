#!/usr/bin/env python3
import click
import json
from covid19_sfbayarea import data as data_scrapers
from covid19_sfbayarea.utils import friendly_county
from sys import exit
import traceback
from typing import Tuple
from pathlib import Path


COUNTY_NAMES: Tuple[str, ...] = tuple(data_scrapers.scrapers.keys())


@click.command(
    help='Create a .json with data for one or more counties. '
    f'Supported counties: {", ".join(COUNTY_NAMES)}.'
)
@click.argument(
    'counties',
    metavar='[COUNTY]...',
    nargs=-1,
    type=click.Choice(COUNTY_NAMES, case_sensitive=False)
)
@click.option(
    '--hospitals',
    is_flag=True,
    default=False,
    help='fetch hospitalization data for given county'
)
@click.option(
    '--output',
    metavar='PATH',
    help='write output file to this directory'
)
def main(counties: Tuple[str, ...], output: str, hospitals: bool) -> None:
    out = dict()
    failed_counties = False

    # Handle hospitalization data
    hospital_out = []
    failed_hospital_counties = False

    if len(counties) == 0:
        counties = COUNTY_NAMES

    # Run each scraper's get_county() method. Assign the output to out[county]
    for county in counties:
        try:
            out[county] = data_scrapers.scrapers[county].get_county()
        except Exception as error:
            failed_counties = True
            message = click.style(f'{friendly_county(county)} county failed',
                                  fg='red')
            click.echo(f'{message}: {error}', err=True)
            traceback.print_exc()

    # Fetch hospitalization data for selected counties, or all counties
    if hospitals:
        try:
            if len(counties) == 0:
                hospital_data = hz.get_county('all')
                hospital_out.append(hospital_data)

            else:
                for county in counties:
                    hospital_data = hz.get_county(county)
                    hospital_out.append(hospital_data)

        except Exception as e:
            failed_hospital_counties = True
            print(
                f'hospitalization data fetch error for {county}: {e}',
                file=stderr
            )

    if output:
        parent = Path(output)
        parent.mkdir(exist_ok=True)   # if output directory does not exist, create it

        with parent.joinpath('data.json').open('w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        if hospitals:
            with parent.joinpath('hospital_data.json').open('w', encoding='utf-8') as f:
                json.dump(hospital_out, f, ensure_ascii=False, indent=2)

    else:
        print(json.dumps(out, indent=2))
        if hospitals:
            print(json.dumps(hospital_out, indent=2))

    if not out:
        exit(70)  # all counties failed

    if failed_counties or failed_hospital_counties:
        exit(1)   # some counties failed


if __name__ == '__main__':
    main()
