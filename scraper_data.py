#!/usr/bin/env python3
import click
import json
import data_scrapers
from typing import Tuple


COUNTY_NAMES = tuple(data_scrapers.scrapers.keys())


@click.command(help='Create a .json with data for one or more counties. Supported '
                    f'counties: {", ".join(COUNTY_NAMES)}.')
@click.argument('counties', metavar='[COUNTY]...', nargs=-1,
                type=click.Choice(COUNTY_NAMES, case_sensitive=False))
def main(counties: Tuple[str]) -> None:
    out = dict()
    if len(counties) == 0:
        counties = ('alameda',)

    # Run each scraper's get_county() method. Assign the output to out[county]
    for county in counties:
        out[county] = data_scrapers.scrapers[county].get_county()
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
