#!/usr/bin/env python3
import click
import json
from covid19_sfbayarea import data as data_scrapers
from typing import Tuple
from pathlib import Path


COUNTY_NAMES : Tuple[str,...]= tuple(data_scrapers.scrapers.keys())


@click.command(help='Create a .json with data for one or more counties. Supported '
                    f'counties: {", ".join(COUNTY_NAMES)}.')
@click.argument('counties', metavar='[COUNTY]...', nargs=-1,
                type=click.Choice(COUNTY_NAMES, case_sensitive=False))
@click.option('--output', metavar='PATH',
              help='write output file to this directory')
def main(counties: Tuple[str,...], output:str) -> None:
    out = dict()
    if len(counties) == 0:
        counties = COUNTY_NAMES

    # Run each scraper's get_county() method. Assign the output to out[county]
    for county in counties:
        out[county] = data_scrapers.scrapers[county].get_county()

    if output:
        parent = Path(output)
        parent.mkdir(exist_ok = True) # if output directory does not exist, create it
        with parent.joinpath('data.json').open('w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

    else:
        print(json.dumps(out,indent=2))

if __name__ == '__main__':
    main()
