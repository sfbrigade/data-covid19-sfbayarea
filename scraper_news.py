#!/usr/bin/env python3
import click
import json
from covid19_sfbayarea import news
from pathlib import Path
from typing import Tuple


COUNTY_NAMES = tuple(news.scrapers.keys())


@click.command(help='Create a news feed for one or more counties. Supported '
                    f'counties: {", ".join(COUNTY_NAMES)}.')
@click.argument('counties', metavar='[COUNTY]...', nargs=-1,
                type=click.Choice(COUNTY_NAMES, case_sensitive=False))
@click.option('--format', default=('json_simple',),
              type=click.Choice(('json_feed', 'json_simple', 'rss')),
              multiple=True)
@click.option('--output', help='write output file(s) to this directory')
def main(counties: Tuple[str], format: str, output: str) -> None:
    if len(counties) == 0:
        # FIXME: this should be COUNTY_NAMES, but we need to fix how the
        # stop-covid19-sfbayarea project uses this first.
        counties = ('san_francisco',)

    # Do the work!
    for county in counties:
        feed = news.scrapers[county].get_news()

        for format_name in format:
            if format_name == 'json_simple':
                data = json.dumps(feed.format_json_simple(), indent=2)
                extension = '.simple.json'
            elif format_name == 'json_feed':
                data = json.dumps(feed.format_json_feed(), indent=2)
                extension = '.json'
            else:
                data = feed.format_rss()
                extension = '.rss'

            if output:
                parent = Path(output)
                parent.mkdir(exist_ok=True)
                with parent.joinpath(f'{county}{extension}').open('w+') as f:
                    f.write(data)
            else:
                print(data)


if __name__ == '__main__':
    main()
