from bs4 import BeautifulSoup, element  # type: ignore
import dateutil.parser
from selenium import webdriver  # type: ignore
from typing import List
from urllib.parse import urljoin
from .base import NewsScraper
from .feed import NewsItem
from .utils import get_base_url, PACIFIC_TIME


class SantaClaraNews(NewsScraper):
    """
    Scrape official county COVID-related news from Santa Clara County. The
    county's public health department site does not have RSS, so this scrapes
    HTML.

    This implementation pulls news from the county public health department
    "newsroom" page. Other sources that could be added:
    - The county Office of Public Affairs newsroom. This appears to be a
      superset of the public health department's newsroom and includes
      non-COVID-related news.
      https://www.sccgov.org/sites/opa/newsroom/Pages/default.aspx
    - Announcements listed at the bottom of the county COVID-19 home page.
      https://www.sccgov.org/sites/covid19/Pages/home.aspx

    Examples
    --------
    >>> scraper = SantaClaraNews()
    >>> scraper.scrape()
    """

    FEED_INFO = dict(
        title='Santa Clara County COVID-19 News',
        home_page_url='https://www.sccgov.org/sites/phd/news/Pages/newsroom.aspx'
    )

    START_URL = 'https://www.sccgov.org/sites/phd/news/Pages/newsroom.aspx'

    def load_html(self, url: str) -> str:
        with webdriver.Firefox() as driver:
            driver.get(self.START_URL)
            driver.implicitly_wait(10)
            content = driver.find_element_by_class_name('sccgov-alerts-archive-item')
            if not content:
                raise ValueError(f'Page did not load properly: {self.START_URL}')

            return driver.page_source

    def parse_page(self, html: str, url: str) -> List[NewsItem]:
        soup = BeautifulSoup(html, 'html5lib')
        base_url = get_base_url(soup, url)
        articles = soup.select('.sccgov-alerts-archive-item')
        return [self.parse_article(index, article, base_url)
                for index, article in enumerate(articles)]

    def parse_article(self, index: int, article: element.Tag,
                      base_url: str) -> NewsItem:
        title_link = article.find('a')

        url = title_link['href']
        if not url:
            raise ValueError(f'No URL found for article {index}')
        else:
            url = urljoin(base_url, url)

        title = title_link.get_text(strip=True)
        if not title:
            raise ValueError(f'No title content found for article {index}')

        date_tag = article.select_one('.sccgov-alerts-archive-date')
        date_string = date_tag.get_text(strip=True)
        try:
            date = dateutil.parser.parse(date_string)
            if date.tzinfo is None:
                date = date.replace(tzinfo=PACIFIC_TIME)
        except ValueError:
            raise ValueError(f'Article {index} date is not in a known format: '
                             f'"{date_string}"')

        category_tag = article.select_one('.sccgov-alerts-archive-category')
        category = category_tag.get_text(strip=True)
        tags = [category] if category else []

        return NewsItem(id=url, url=url, title=title, date_published=date,
                        tags=tags)
