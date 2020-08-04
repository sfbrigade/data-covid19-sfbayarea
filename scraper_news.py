#!/usr/bin/env python3
import click
from datetime import datetime, timedelta
from covid19_sfbayarea import news
from covid19_sfbayarea.news.utils import parse_datetime
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
def main(counties: Tuple[str], from_: datetime, format: str, output: str) -> None:
    if len(counties) == 0:
        counties = COUNTY_NAMES

    # Do the work!
    for county in counties:
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
                print(data)


if __name__ == '__main__':
    main()
