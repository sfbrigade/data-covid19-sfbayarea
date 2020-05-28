from bs4 import BeautifulSoup, element  # type: ignore
import dateutil.parser
from typing import List
from urllib.parse import urljoin
from .base import NewsScraper
from .errors import FormatError
from .feed import NewsItem
from .utils import get_base_url, HEADING_PATTERN


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
        title_link = item.find(HEADING_PATTERN).find('a')

        url = title_link['href']
        if not url:
            raise FormatError('No URL found')
        else:
            url = urljoin(base_url, url)

        title = title_link.get_text(strip=True)
        if not title:
            raise FormatError('No title content found')

        date_string = item.find('time')['datetime']
        date = dateutil.parser.parse(date_string)

        return NewsItem(id=url, url=url, title=title, date_published=date)
