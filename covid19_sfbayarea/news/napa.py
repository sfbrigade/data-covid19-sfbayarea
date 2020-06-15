from bs4 import BeautifulSoup, element  # type: ignore
import re
from typing import List
from urllib.parse import urljoin
from .base import NewsScraper
from .errors import FormatError
from .feed import NewsItem
from .utils import get_base_url, is_covid_related, parse_datetime


SUMMARY_PREFIX_PATTERN = re.compile(r'''
    ^
    \(?                       # Prefix may be wrapped in parentheses
    NAPA,\sCA\w*\.?           # Variations on "Napa, <state>"
    \)?
    \s*                       # Optional spaces around the separator
    [\-\u00a0\u2010-\u2015]?  # Optional dashes of various kinds as separator
    \s*
''', re.IGNORECASE | re.VERBOSE)


class NapaNews(NewsScraper):
    """
    Scrape official county COVID-related news from Napa County. It scrapes HTML
    from the county news page to generate a news feed. It also attempts to
    narrow down a subset of news items since this page covers a variety of
    topics beyond COVID.

    There are some other sources that might be useful to look into here:
    - Napa has an RSS feed for news, but it appears to only contain items from
      the *current* month, which makes it pretty useless near the start of a
      month, which is why we aren't using it.
      https://www.countyofnapa.org/RSSFeed.aspx?ModID=1&CID=All-newsflash.xml
    - The county coronavirus site has daily "situation updates," but these are
      less news oriented and more just an update on the numbers:
      https://www.countyofnapa.org/2770/Situation-Updates

    Examples
    --------
    >>> scraper = NapaNews()
    >>> scraper.scrape()
    """

    FEED_INFO = dict(
        title='Napa County COVID-19 News',
        home_page_url='https://www.countyofnapa.org/CivicAlerts.aspx?sort=date'
    )

    URL = 'https://www.countyofnapa.org/CivicAlerts.aspx?sort=date'

    def parse_page(self, html: str, url: str) -> List[NewsItem]:
        soup = BeautifulSoup(html, 'html5lib')
        base_url = get_base_url(soup, url)
        articles = soup.select('.contentMain .listing .item.intro')
        if len(articles) == 0:
            raise ValueError('Could not find any news items on page')

        parsed = (self.parse_news_item(article, base_url)
                  for article in articles)
        return list(filter(is_covid_related, parsed))

    def parse_news_item(self, item_element: element.Tag, base_url: str) -> NewsItem:
        title_element = item_element.find('h3')
        title_link = title_element.find('a')

        url = title_link['href']
        if not url:
            raise FormatError('No URL found for article')
        else:
            url = urljoin(base_url, url)

        title = title_link.get_text(strip=True)
        if not title:
            raise FormatError('No title content found')

        date_string = item_element.find(class_='date').get_text().strip()
        date_string = date_string.replace('Posted on: ', '')
        date = parse_datetime(date_string)

        categories = []
        for category_element in item_element.select('.category'):
            categories.append(category_element.get_text(strip=True))
            # Remove the link so we can more easily pull out summary text
            category_link = category_element.find_parent('a') or category_element
            category_link.extract()

        more_link = item_element.find(class_='more')
        if more_link:
            more_link.extract()

        # TODO: can/should we preserve HTML here?
        summaries = (element if isinstance(element, str) else element.get_text(strip=True)
                     for element in title_element.next_siblings)
        summaries = (SUMMARY_PREFIX_PATTERN.sub('', summary)
                     for summary in summaries)
        summary = ' '.join(summaries).strip()

        return NewsItem(id=url, url=url, title=title, date_published=date,
                        summary=summary)
