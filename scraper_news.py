#!/usr/bin/env python3
import click
from covid19_sfbayarea import news
from pathlib import Path
from typing import cast, Tuple


COUNTY_NAMES = cast(Tuple[str], tuple(news.scrapers.keys()))


@click.command(help='Create a news feed for one or more counties. Supported '
                    f'counties: {", ".join(COUNTY_NAMES)}.')
@click.argument('counties', metavar='[COUNTY]...', nargs=-1,
                type=click.Choice(COUNTY_NAMES, case_sensitive=False))
@click.option('--format', default=('json_feed',),
              type=click.Choice(('json_feed', 'json_simple', 'rss')),
              multiple=True)
@click.option('--output', help='write output file(s) to this directory')
def main(counties: Tuple[str], format: str, output: str) -> None:
    if len(counties) == 0:
        counties = COUNTY_NAMES

    # Do the work!
    for county in counties:
        feed = news.scrapers[county].get_news()

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
