#!/usr/bin/env python3
import click
from typing import Tuple

BAY_AREA_COUNTIES = [
    'alameda',
    'contra_costa',
    'marin',
    'napa',
    'san_francisco',
    'san_mateo',
    'santa_clara',
    'sonoma',
    'solano'
]


@click.command(
    help="Pull down COVID-19-related hospitalization data "
         "from the California Dept. of Public Health"
)
@click.argument(
    "counties",
    metavar='[COUNTY]...',
    nargs=-1,
    type=click.Choice(BAY_AREA_COUNTIES, case_sensitive=False)
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
