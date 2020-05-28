import requests
from typing import Dict, List
from .feed import NewsFeed, NewsItem


class NewsScraper:
    """
    Base class for news scrapers. Common scraping/news feed functionality used
    across multiple counties should be implemented here. This class should be
    inherited and never used directly.

    To run a scraper, first instantiate it, then call `scrape()`:
    >>> class SomeCounty(NewsScraper):
    >>>     ...
    >>> scraper = SomeCounty()
    >>> news_feed = scraper.scrape()

    Classes inheriting from this should set ``START_URL`` to the URL from which
    scraping should start, then implement `parse_page()`, which returns a list
    of news items given some HTML.
    """
    FEED_INFO: Dict = {}
    START_URL = ''

    def create_feed(self) -> NewsFeed:
        return NewsFeed(**self.FEED_INFO)

    def scrape(self) -> NewsFeed:
        """
        Create and return a news feed.

        Returns
        -------
        list of dict

        Examples
        --------
        >>> scraper = SanFranciscoNews()
        >>> scraper.scrape()
        [{'url': 'https://sf.gov/news/expansion-coronavirus-testing-all-essential-workers-sf',
          'text': 'Expansion of coronavirus testing for all essential workers in SF',
          'date': '2020-04-23T04:11:56Z'}]
        """
        feed = self.create_feed()
        # TODO: we may want to iterate through multiple pages in the future
        html = self.load_html(self.START_URL)
        news = self.parse_page(html, self.START_URL)
        feed.items.extend(news)
        return feed

    def load_html(self, url: str) -> str:
        response = requests.get(self.START_URL)
        response.raise_for_status()
        return response.text

    def parse_page(self, html: str, url: str) -> List[NewsItem]:
        raise NotImplementedError()
