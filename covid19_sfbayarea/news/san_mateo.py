from bs4 import element  # type: ignore
from lxml import etree  # type: ignore
import re
from typing import List
from .base import NewsScraper
from .feed import NewsItem, NewsFeed
from .utils import parse_datetime


SUMMARY_PREFIX_PATTERN = re.compile(r'''
    ^Redwood\sCity             # Redwood city is the county seat, so news items
                              # are often "sourced" there
    (,\sCA\w*\.?)?            # Sometimes followed by "CA", "Calif.", etc.
    \s*                       # Optional spaces around the separator
    [\-\u00a0\u2010-\u2015]?  # Optional dashes of various kinds as separator
    \s*
''', re.IGNORECASE | re.VERBOSE)

# Titles are often prefixed with a date, and we want to remove it.
DATE_PREFIX_PATTERN = re.compile(r'''
    ^\w+\s\d+,\s\d+           # Date in format "month, dd, yyyy"
    \s*                       # Optional spaces around the separator
    [\-\u00a0\u2010-\u2015]?  # Optional dashes of various kinds as separator
    \s*
''', re.VERBOSE)


# NOTE: this is currently the only scraper that reads in RSS. If we wind up
# finding RSS feeds we should be using from other counties, we should extract
# most of this into a base class for transforming RSS. The vast majority of the
# code here is about handling RSS and is not specific to San Mateo.
class SanMateoNews(NewsScraper):
    """
    Scrape official county COVID-related news from San Mateo County. It's based
    on the RSS feed from the County Manager's Office (CMO), though the items
    are cleaned up a bit for readability and to fit with the format of the rest
    of out feeds.

    There are some other sources that might be useful to look into here:
    - The county health office has health orders and health officer statements:
      https://smchealth.org/post/health-officer-statements-and-orders-0
    - The county health office also has "local news," but it’s much less timely
      and detailed than the CMO office's press releases. (Actually, it looks
      like a subset.)
      https://smchealth.org/post/local-news-you-need
    - The Joint Information Center (JIC) has a bunch of stuff, but ultimately
      just shows the CMO press releases for news:
      https://cmo.smcgov.org/jic

    Examples
    --------
    >>> scraper = SanMateoNews()
    >>> scraper.scrape()
    """

    FEED_INFO = dict(
        title='San Mateo County COVID-19 News',
        home_page_url='https://cmo.smcgov.org/press-releases'
    )

    URL = 'https://cmo.smcgov.org/news/feed'

    def scrape(self) -> NewsFeed:
        """
        Create and return a news feed.
        """
        feed = self.create_feed()
        xml = self.load_xml(self.URL)
        news = self.parse_feed(xml, self.URL)
        feed.append(*(item
                      for item in news
                      if self._in_time_range(item)))
        return feed

    def load_xml(self, url: str) -> bytes:
        import requests
        response = requests.get(self.URL)
        response.raise_for_status()
        return response.content

    def parse_feed(self, xml: bytes, url: str) -> List[NewsItem]:
        root = etree.fromstring(xml)
        return [self.parse_news_item(item) for item in root.iter('item')]

    def parse_news_item(self, item_element: element.Tag) -> NewsItem:
        # Items are mostly standard RSS. Example in practice:
        # <item>
        #     <title>May 29, 2020 - Rough Waters Ahead: County of San Mateo  Releases 2020-21 Recommended Budget</title>
        #     <link>https://cmo.smcgov.org/press-release/may-29-2020-rough-waters-ahead-county-san-mateo-releases-2020-21-recommended-budget</link>
        #     <description><![CDATA[REDWOOD CITY, Calif. – County Manager Mike Callagy expects the Fiscal Year 2020-21 Recommended Budget released today, Friday, May 29, 2020, will undergo substantial changes once the full health and economic impacts of the response to the coronavirus pandemic are known.]]></description>
        #     <pubDate>Fri, 29 May 2020 16:18:06 +0000</pubDate>
        #     <dc:creator>mwilson</dc:creator>
        #     <guid isPermaLink="false">11806 at https://cmo.smcgov.org</guid>
        # </item>
        title = item_element.find('title').text.strip()
        # Most titles are prefixed with a date, which is a bit redundant.
        title = DATE_PREFIX_PATTERN.sub('', title)

        url = item_element.find('link').text.strip()
        date = parse_datetime(item_element.find('pubDate').text.strip())
        guid = item_element.find('guid').text.strip()

        # The <description> element can contain HTML snippets. Since we are
        # translating this to our feed's `summary`, which is plain text, we
        # do some quick-n-dirty HTML parsing.
        description = item_element.find('description').text.strip()
        description = re.sub(r'<br\s*/?>', '\n', description)
        description = re.sub(r'</?\w+[^>]*>', '', description)
        # Strip meaningless prefixes from the front of the text.
        description = SUMMARY_PREFIX_PATTERN.sub('', description.strip())

        # NOTE: it looks like San Mateo doesn't use <category>, but if we make
        # this more generic, it'd be smart to add parsing for it.

        return NewsItem(id=guid, url=url, title=title, date_published=date,
                        summary=description)
