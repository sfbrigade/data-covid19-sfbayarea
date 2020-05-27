from bs4 import BeautifulSoup  # type: ignore
import dateutil.parser
import dateutil.tz
from typing import List
from urllib.parse import urljoin
from .base import NewsScraper
from .feed import NewsItem
from .utils import first_text_in_element, get_base_url


PACIFIC_TIME = dateutil.tz.gettz('America/Los_Angeles')


class AlamedaNews(NewsScraper):
    """
    Scrape official Alameda county COVID-related press releases. The county's
    official site does not have RSS, so this scrapes HTML.

    There are some other pages that might be relevant, but it's a bit tough to
    determine how to scrape them well or narrow them down to useful info:
    - County news & announcements RSS coves much more than COVID info, so we'd
      need to figure out how to narrow it down:
      https://public.govdelivery.com/topics/CAALAME_1/feed.rss
    - Emergency News RSS doesn't appear to be updated:
      https://public.govdelivery.com/topics/CAALAME_49/feed.rss
    - Situation updates on the COVID-19 home page are a bit messy, and it's not
      clear how best to utilize them. They are also *partially* duplicative of
      the press releases we are already scraping:
      http://www.acphd.org/2019-ncov.aspx

    Examples
    --------
    >>> scraper = AlamedaNews()
    >>> scraper.scrape()
    """

    FEED_INFO = dict(
        title='Alameda County COVID-19 News',
        home_page_url='http://www.acphd.org/2019-ncov/press-releases.aspx'
    )

    START_URL = 'http://www.acphd.org/2019-ncov/press-releases.aspx'

    def parse_page(self, html: str, url: str) -> List[NewsItem]:
        soup = BeautifulSoup(html, 'html5lib')
        base_url = get_base_url(soup, url)
        news = []
        article_rows = soup.select_one('.board').find_all('tr')
        for index, row in enumerate(article_rows):
            date_cell, info_cell = row.find_all('td')

            date_string = date_cell.get_text(strip=True)
            try:
                date = dateutil.parser.parse(date_string)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=PACIFIC_TIME)
            except ValueError:
                raise ValueError(f'Article {index} date could not be parsed: '
                                 f'"{date_string}"')

            # Some info cells just have the title as a link, while others have
            # the title as text followed by links for each language.
            english_link = info_cell.find('a', string='English')
            if english_link:
                url = english_link['href']
                # These titles are sometimes followed by a colon. If so, drop
                # it. (Whitespace will already have been stripped.)
                title = first_text_in_element(info_cell)
                if title:
                    title = title.strip(':')
            else:
                title_link = info_cell.find('a')
                url = title_link['href']
                title = title_link.get_text(strip=True)

            if url:
                url = urljoin(base_url, url)
            else:
                raise ValueError(f'Not URL found for article {index}')

            if not title:
                raise ValueError(f'No title content found for article {index}')

            news.append(NewsItem(id=url, url=url, title=title,
                                 date_published=date))

        return news
