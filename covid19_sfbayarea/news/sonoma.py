from bs4 import BeautifulSoup, element  # type: ignore
from typing import List
from urllib.parse import urljoin
from .base import NewsScraper
from .errors import FormatError
from .feed import NewsItem
from .utils import (get_base_url, is_covid_related, normalize_whitespace,
                    parse_datetime)


class SonomaNews(NewsScraper):
    """
    Scrape official county COVID-related news from Sonoma County. This scrapes
    the county's main news page (there's no RSS feed) for news and filters out
    non-COVID news based on key terms.

    NOTE: this page includes spanish-language versions of some articles, but
    we don't have an effective way to link them up with the english ones and
    they tend to get filtered out because our key terms are in english.

    There are some other sources that might be useful to look into here:

    - The county emergency site (socoemergency.org) has a news page and a
      public health orders page:
        - https://socoemergency.org/emergency/novel-coronavirus/latest-news/
        - https://socoemergency.org/emergency/novel-coronavirus/health-orders/
      These pages are specific to COVID, but they tend to be a little more
      technical in approach (compare these two about the same topic:
      https://sonomacounty.ca.gov/CAO/Press-Releases/Sonoma-County-Public-Health-Officer-Amends-Shelter-in-Place-Order-to-Allow-Additional-Businesses-to-Reopen/
      vs. https://socoemergency.org/amendment-no-3-to-health-order-no-c19-09/).
      These pages are *largely* a subset of items on main county feed, but not
      exclusively. If we could find a good way to reconcile matching articles,
      it might be good. to join these feeds together.

    - The county emergency site also has an RSS feed, but it appears to be
      about any/every page on the site (i.e. it tracks page updates, rather
      than focusing on what we might think of as "news" here).
      https://socoemergency.org/feed

    Examples
    --------
    >>> scraper = SonomaNews()
    >>> scraper.scrape()
    """

    FEED_INFO = dict(
        title='Sonoma County COVID-19 News',
        home_page_url='https://sonomacounty.ca.gov/News/'
    )

    URL = 'https://sonomacounty.ca.gov/News/'

    def parse_page(self, html: str, url: str) -> List[NewsItem]:
        soup = BeautifulSoup(html, 'html5lib')
        base_url = get_base_url(soup, url)
        articles = soup.select('.teaserContainer.srchResults .teaserContainer')
        if len(articles) == 0:
            raise FormatError('Could not find any news items on page')

        parsed = (self.parse_news_item(article, base_url)
                  for article in articles)
        return list(filter(is_covid_related, parsed))

    def parse_news_item(self, item_element: element.Tag, base_url: str) -> NewsItem:
        title_element = item_element.select_one('.titlePrimary')
        title_link = title_element.find('a')

        url = title_link['href']
        if not url:
            raise FormatError('No URL found for article')
        else:
            url = urljoin(base_url, url)

        title = title_link.get_text(strip=True)
        if not title:
            raise FormatError('No title content found')

        date_string = item_element.select_one('.published .date').get_text(strip=True)
        time_element = item_element.select_one('.published .time')
        if time_element:
            time_string = time_element.get_text(strip=True)
            date_string = f'{date_string} at {time_string}'
        date = parse_datetime(date_string)

        summary = item_element.select_one('.summary').get_text().strip()

        tags = []
        source_element = item_element.select_one('.source')
        if source_element:
            tags.append(normalize_whitespace(source_element.get_text()))

        return NewsItem(id=url, url=url, title=title, date_published=date,
                        summary=summary, tags=tags)
