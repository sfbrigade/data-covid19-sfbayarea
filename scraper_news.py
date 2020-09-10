#!/usr/bin/env python3
import click
from datetime import datetime, timedelta
from covid19_sfbayarea import news
from covid19_sfbayarea.utils import friendly_county
from covid19_sfbayarea.news.utils import parse_datetime
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import cast, Tuple


COUNTY_NAMES = cast(Tuple[str], tuple(news.scrapers.keys()))


def cli_date(date_string: str) -> datetime:
    '''Parse a CLI date or number of days into a TZ-aware datetime.'''
    try:
        days = float(date_string)
        if days <= 0:
            raise click.BadParameter('must be a positive number or date')
        return datetime.now().astimezone() - timedelta(days=days)
    except ValueError:
        pass

    try:
        value = parse_datetime(date_string)
    except Exception:
        raise click.BadParameter(f'"{date_string}" is not a date')
    if value >= datetime.now().astimezone():
        raise click.BadParameter('must be a date in the past.')

    return value


def run_county_news(county: str, from_: datetime, format: Tuple[str], output: str) -> None:
    '''Run the scraper for a given county and output the results.'''
    feed = news.scrapers[county].get_news(from_date=from_)

    for format_name in format:
        if format_name == 'json_simple':
            data = feed.format_json_simple()
            extension = '.simple.json'
        elif format_name == 'json_feed':
            data = feed.format_json_feed()
            extension = '.json'
        else:
            data = feed.format_rss()
            extension = '.rss'

        if output:
            parent = Path(output)
            parent.mkdir(exist_ok=True)
            with parent.joinpath(f'{county}{extension}').open('wb') as f:
                f.write(data)
        else:
            click.echo(data)


@click.command(help='Create a news feed for one or more counties. Supported '
                    f'counties: {", ".join(COUNTY_NAMES)}.')
@click.argument('counties', metavar='[COUNTY]...', nargs=-1,
                type=click.Choice(COUNTY_NAMES, case_sensitive=False))
@click.option('--from', 'from_', type=cli_date, default='31',
              help='Only include news items newer than this date. Instead of '
                   'a date, you can specify a number of days ago, e.g. "14" '
                   'for 2 weeks ago.')
@click.option('--format', default=('json_feed',),
              type=click.Choice(('json_feed', 'json_simple', 'rss')),
              multiple=True)
@click.option('--output', metavar='PATH',
              help='write output file(s) to this directory')
def main(counties: Tuple[str], from_: datetime, format: Tuple[str], output: str) -> None:
    if len(counties) == 0:
        counties = COUNTY_NAMES

    # Do the work!
    error_count = 0
    for county in counties:
        try:
            run_county_news(county, from_, format, output)
        except Exception as error:
            error_count += 1
            message = click.style(f'{friendly_county(county)} county failed',
                                  fg='red')
            click.echo(f'{message}: {error}', err=True)
            traceback.print_exc()

    if error_count == len(counties):
        sys.exit(70)
    elif error_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(level=os.getenv('LOG_LEVEL', 'WARN').upper())
    main()
