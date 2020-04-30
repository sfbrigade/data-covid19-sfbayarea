#!/usr/bin/env python3
import json
import news
import sys


def message(text):
    print(text, file=sys.stderr)


def main():
    # TODO: use Click or argparse so we can manage more complex options
    counties = sys.argv[1:]

    # Validate args before starting to scrape
    for county in counties:
        if county not in news.scrapers:
            message(f'Unknown county: "{county}"')
            sys.exit(1)
        elif news.scrapers[county] is None:
            message(f'Scraper for {county} has not yet been written')
            sys.exit(1)

    if len(counties) == 0:
        counties = ['san_francisco']

    # Do the work!
    for county in counties:
        scraper = news.scrapers[county]()
        feed_items = scraper.scrape()
        feed = {'newsItems': feed_items}
        print(json.dumps(feed, indent=2))


if __name__ == '__main__':
    main()
