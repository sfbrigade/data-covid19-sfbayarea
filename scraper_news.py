#!/usr/bin/env python3
import click
import json
import news
from typing import Tuple


COUNTY_NAMES = tuple(news.scrapers.keys())


@click.command(help='Create a news feed for one or more counties. Supported '
                    f'counties: {", ".join(COUNTY_NAMES)}.')
@click.argument('counties', metavar='[COUNTY]...', nargs=-1,
                type=click.Choice(COUNTY_NAMES, case_sensitive=False))
@click.option('--format', default='json_simple',
              type=click.Choice(('json_feed', 'json_simple')))
def main(counties: Tuple[str], format: str) -> None:
    if len(counties) == 0:
        counties = ('san_francisco',)

    # Do the work!
    for county in counties:
        scraper = news.scrapers[county]()
        feed = scraper.scrape()

        if format == 'json_simple':
            data = feed.format_json_simple()
        else:
            data = feed.format_json_feed()
        print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
