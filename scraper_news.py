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
def main(counties: Tuple[str]) -> None:
    if len(counties) == 0:
        counties = ('san_francisco',)

    # Do the work!
    for county in counties:
        scraper = news.scrapers[county]()
        feed_items = scraper.scrape()
        feed = {'newsItems': feed_items}
        print(json.dumps(feed, indent=2))


if __name__ == '__main__':
    main()
