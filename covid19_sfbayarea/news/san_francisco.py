from bs4 import BeautifulSoup, element  # type: ignore
from copy import copy
import dateutil.parser
from typing import List
from urllib.parse import urljoin
from ..errors import FormatError
from .base import NewsScraper
from .feed import NewsItem
from .utils import get_base_url, HEADING_PATTERN, normalize_whitespace


class SanFranciscoNews(NewsScraper):
    """
    Scrape official county COVID-related news from San Francisco. The county's
    official site does not have RSS, so this scrapes HTML.

    City folks have suggested we may also want to consider adding items from at
    these sources in the future:
    - Mayor's press releases: https://sfmayor.org/news (which has RSS)
    - DPH: https://www.sfdph.org/dph/comupg/aboutdph/newsMedia/default.asp
    - SF General Hospital: https://zuckerbergsanfranciscogeneral.org/about-us/news/
    - Laguna Honda Hospital: https://lagunahonda.org/press-releases

    Examples
    --------
    >>> scraper = SanFranciscoNews()
    >>> scraper.scrape()
    [{'url': 'https://sf.gov/news/expansion-coronavirus-testing-all-essential-workers-sf',
      'text': 'Expansion of coronavirus testing for all essential workers in SF',
      'date': '2020-04-23T04:11:56Z'}]
    """

    FEED_INFO = dict(
        title='San Francisco County COVID-19 News',
        home_page_url='https://sf.gov/news/topics/794'
    )

    URL = 'https://sf.gov/news/topics/794'

    def parse_page(self, html: str, url: str) -> List[NewsItem]:
        soup = BeautifulSoup(html, 'html5lib')
        base_url = get_base_url(soup, url)
        articles = soup.main.find_all('article')
        return [self.parse_news_item(article, base_url)
                for article in articles]

    def parse_news_item(self, item: element.Tag, base_url: str) -> NewsItem:
        item = copy(item)
        title_link = item.find(HEADING_PATTERN).find('a')

        url = title_link['href']
        if not url:
            raise FormatError('No URL found')
        else:
            url = urljoin(base_url, url)

        title = normalize_whitespace(title_link.get_text())
        if not title:
            raise FormatError('No title content found')

        date_element = item.find('time')
        date_string = date_element['datetime']
        date = dateutil.parser.parse(date_string)

        # The summary text is everything except the title and date.
        title_link.extract()
        date_element.extract()
        summary = normalize_whitespace(item.get_text())

        return NewsItem(id=url, url=url, title=title, date_published=date, summary=summary)
