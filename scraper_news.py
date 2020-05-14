#!/usr/bin/env python3
import click
import json
import news
from pathlib import Path
from typing import Tuple


COUNTY_NAMES = tuple(news.scrapers.keys())


@click.command(help='Create a news feed for one or more counties. Supported '
                    f'counties: {", ".join(COUNTY_NAMES)}.')
@click.argument('counties', metavar='[COUNTY]...', nargs=-1,
                type=click.Choice(COUNTY_NAMES, case_sensitive=False))
@click.option('--format', default='json_simple',
              type=click.Choice(('json_feed', 'json_simple', 'rss')))
def main(counties: Tuple[str], format: str) -> None:
    if len(counties) == 0:
        counties = ('san_francisco',)

    # Do the work!
    for county in counties:
        scraper = news.scrapers[county]()
        feed = scraper.scrape()

        if format == 'json_simple':
            data = json.dumps(feed.format_json_simple(), indent=2)
        elif format == 'json_feed':
            data = json.dumps(feed.format_json_feed(), indent=2)
        else:
            data = feed.format_rss()

        print(data)


if __name__ == '__main__':
    main()
