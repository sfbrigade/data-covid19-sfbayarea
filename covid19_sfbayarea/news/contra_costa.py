from bs4 import BeautifulSoup, element  # type: ignore
import re
from typing import List, Optional
from urllib.parse import urljoin
from .base import NewsScraper
from .feed import NewsItem
from .utils import get_base_url, parse_datetime, HEADING_PATTERN


MONTHS = (
    'january',
    'february',
    'march',
    'april',
    'may',
    'june',
    'july',
    'august',
    'september',
    'october',
    'november',
    'december',
)

# There's not a great way to identify a news item listing on the page (and very
# few CSS classes or attributes in general), so we find news items by looking
# for the month-based headings and finding all the <li> tags after them.
MONTH_HEADING_PATTERN = re.compile(
    # NOTE: this funky character class for whitespace is needed because `\s`
    # does not match things like em squares, zero-width spaces, etc. and those
    # kinds of whitespace *do* show up on this page.
    r'^\s*(' + '|'.join(MONTHS) + r')[\s\u2000-\u200d]+\d{4}\s*$',
    re.IGNORECASE
)

# The text of a news item is formatted roughly as "title - date".
ARTICLE_TITLE_PATTERN = re.compile(r'^\s*(.*?)\s*-\s*(\d+/\d+/\d+)\s*$')


class ContraCostaNews(NewsScraper):
    """
    Scrape official county COVID-related news from Contra Costa County. The
    county's official site does not have RSS, so this scrapes HTML.

    The current content comes from the Health Services Department's updates
    page. Othe potentially relevant sources might include:
    - The county's "news flash" RSS feed (much broader topics than just COVID):
      https://www.contracosta.ca.gov/RSSFeed.aspx?ModID=1&CID=All-newsflash.xml
    - The county's COVID-specific "news flash" page (no RSS for this category
      of news flashes). The formatting of these is not the greatest fit for
      a list of linkable news items.
      https://www.contracosta.ca.gov/CivicAlerts.aspx?AID=2180
    - The Health Services Department's "news room."
      https://cchealth.org/newsroom/

    Examples
    --------
    >>> scraper = ContraCostaNews()
    >>> scraper.scrape()
    """

    FEED_INFO = dict(
        title='Contra Costa County COVID-19 News',
        home_page_url='https://www.coronavirus.cchealth.org/health-services-updates'
    )

    URL = 'https://www.coronavirus.cchealth.org/health-services-updates'

    def is_news_heading(self, element: element.Tag) -> bool:
        return (HEADING_PATTERN.match(element.name) and
                MONTH_HEADING_PATTERN.match(element.get_text())) is not None

    def parse_page(self, html: str, url: str) -> List[NewsItem]:
        soup = BeautifulSoup(html, 'lxml')
        base_url = get_base_url(soup, url)
        news = []
        month_headings = soup.find_all(self.is_news_heading)
        index = 0
        for heading in month_headings:
            articles = heading.parent.find_all('li')
            for article in articles:
                index += 1
                item = self.parse_article(index,
                                          article,
                                          base_url)
                if item:
                    news.append(item)

        return news

    def parse_article(self, index: int, article: element.Tag,
                      base_url: str) -> Optional[NewsItem]:
        text = article.get_text()
        # The text of articles is formatted as "title - date", so we need a
        # little extra to pull the title and date apart.
        text_parts = ARTICLE_TITLE_PATTERN.match(text)
        # Some entries just don't have dates, so there's not much we can do
        # except give up and drop them from the feed.
        if not text_parts:
            return None

        title, date_string = text_parts.groups()
        try:
            date = parse_datetime(date_string)
        except ValueError:
            raise ValueError(f'Article {index} date was in an unknown format: '
                             f'"{date_string}"')

        url = article.find('a')['href']
        if not url:
            raise ValueError(f'No URL found for article {index}')
        else:
            url = urljoin(base_url, url)

        return NewsItem(id=url, url=url, title=title, date_published=date)
