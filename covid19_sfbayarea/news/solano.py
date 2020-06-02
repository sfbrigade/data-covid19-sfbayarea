from bs4 import BeautifulSoup, element  # type: ignore
import re
from typing import List
from urllib.parse import urljoin
from .base import NewsScraper
from .errors import FormatError
from .feed import NewsItem
from .utils import get_base_url, parse_datetime


SUMMARY_PREFIX_PATTERN = re.compile(r'^SOLANO COUNTY\s*[\-\u2013]\s*', re.I)


class SolanoNews(NewsScraper):
    """
    Scrape official county COVID-related news from Solano County. This pulls
    from from the county's main news page, which does not have RSS, so this
    scrapes HTML. It also attempts to narrow down a subset of news items since
    this page covers a variety of topics beyond COVID.

    There are some other sources that might be useful to look into here:
    - The news *archive* has more items going farther back in time. However, it
      doesn't show dates.
      http://www.solanocounty.com/news/displayarchive.asp?Type=1&targetID=1
      (That page pulls actual content from:
       POST http://www.solanocounty.com/custom/0000/aja/news/mainnews.asp
       with request body:
           archive=0&target=1&type=1&cnt=20 [set cnt higher for more results])
    - Coronaviurs press releases page. This has a much narrower set of
      information and lacks some important COVID news that is on the main news
      page, though it is always all COVID-focused:
      http://www.solanocounty.com/depts/ph/coronavirus_links/coronavirus_press_releases_and_information.asp

    Examples
    --------
    >>> scraper = SolanoNews()
    >>> scraper.scrape()
    """

    FEED_INFO = dict(
        title='Solano County COVID-19 News',
        home_page_url='http://www.solanocounty.com/news/default.asp'
    )

    URL = 'http://www.solanocounty.com/news/default.asp'

    def parse_page(self, html: str, url: str) -> List[NewsItem]:
        soup = BeautifulSoup(html, 'html5lib')
        base_url = get_base_url(soup, url)
        headers = soup.find_all('a', class_='newsheader')
        if len(headers) == 0:
            raise FormatError('Could not find any news items on page')

        parsed = (self.parse_news_item(header, base_url)
                  for header in headers)
        return list(filter(self.is_covid_related, parsed))

    def parse_news_item(self, title_link: element.Tag, base_url: str) -> NewsItem:
        cell = title_link.find_parent('td')

        url = title_link['href']
        if not url:
            raise FormatError('No URL found for article')
        else:
            url = urljoin(base_url, url)

        title = title_link.get_text(strip=True)
        if not title:
            raise FormatError('No title content found')

        date_string = cell.find(class_='newsdate').get_text().strip()
        date = parse_datetime(date_string)

        summary_element = cell.find(class_='newsbody')
        more_link = summary_element.find(class_='more')
        if more_link:
            more_link.extract()

        summary = summary_element.get_text(strip=True)
        summary = SUMMARY_PREFIX_PATTERN.sub('', summary)

        return NewsItem(id=url, url=url, title=title, date_published=date,
                        summary=summary)

    def is_covid_related(self, item: NewsItem) -> bool:
        comparable = ' '.join([
            item.title,
            item.summary or '',
            item.url
        ]).lower()
        terms = ('covid', 'coronavirus', 'health')
        return any(term in comparable for term in terms)
