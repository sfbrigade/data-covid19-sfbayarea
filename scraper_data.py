#!/usr/bin/env python3
import click
import json
from covid19_sfbayarea import data as data_scrapers
from sys import stderr, exit
from typing import Tuple
from pathlib import Path


COUNTY_NAMES : Tuple[str,...]= tuple(data_scrapers.scrapers.keys())


@click.command(help='Create a .json with data for one or more counties. Supported '
                    f'counties: {", ".join(COUNTY_NAMES)}.')
@click.argument('counties', metavar='[COUNTY]...', nargs=-1,
                type=click.Choice(COUNTY_NAMES, case_sensitive=False))
@click.option('--output', metavar='PATH',
              help='write output file to this directory')
def main(counties: Tuple[str,...], output: str) -> None:
    out = dict()
    failed_counties = False
    if len(counties) == 0:
        counties = COUNTY_NAMES

    # Run each scraper's get_county() method. Assign the output to out[county]
    for county in counties:
        try:
            out[county] = data_scrapers.scrapers[county].get_county()
        except Exception as e:
            failed_counties = True
            print(f'{county} failed to scrape: {e}', file = stderr)

    if output:
        parent = Path(output)
        parent.mkdir(exist_ok = True) # if output directory does not exist, create it
        with parent.joinpath('data.json').open('w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

    else:
        print(json.dumps(out,indent=2))

    if not out: exit(70) # all counties failed
    if failed_counties: exit(1) # some counties failed

if __name__ == '__main__':
    main()
