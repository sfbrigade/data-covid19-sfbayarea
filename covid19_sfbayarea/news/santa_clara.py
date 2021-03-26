from bs4 import BeautifulSoup, element  # type: ignore
from logging import getLogger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from typing import List
from urllib.parse import urljoin
from ..utils import parse_datetime
from ..webdriver import get_firefox
from .base import NewsScraper
from .errors import FormatError
from .feed import NewsItem
from .utils import get_base_url


logger = getLogger(__name__)


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

    URL = 'https://www.sccgov.org/sites/phd/news/Pages/newsroom.aspx'

    def load_html(self, url: str) -> str:
        with get_firefox() as driver:
            driver.get(self.URL)
            driver.implicitly_wait(10)
            page_sources = []
            while True:
                content = driver.find_element_by_css_selector(
                    '.view-news article')
                if not content:
                    raise ValueError(f'Page did not load properly: {self.URL}')
                page_sources.append(driver.page_source)

                # If we've gone earlier than the time range, stop.
                earliest_time = parse_datetime(
                    driver.find_elements_by_css_selector(
                        '.view-news article time'
                    )[-1].get_attribute('datetime')
                )
                if not self.from_date or self.from_date >= earliest_time:
                    break

                # Navigate to the next page if there is one.
                next_link = driver.find_element_by_css_selector(
                    '.pager__item--next')
                if not next_link:
                    break

                logger.info('Checking next news page...')
                next_link.click()
                WebDriverWait(driver, 5).until(
                    expected_conditions.invisibility_of_element_located(
                        (By.CSS_SELECTOR, '.ajax-progress')))

            return ''.join(page_sources)

    def parse_page(self, html: str, url: str) -> List[NewsItem]:
        soup = BeautifulSoup(html, 'html5lib')
        base_url = get_base_url(soup, url)
        articles = soup.select('.view-news article')
        return [self.parse_article(index, article, base_url)
                for index, article in enumerate(articles)]

    def parse_article(self, index: int, article: element.Tag,
                      base_url: str) -> NewsItem:
        title_link = article.find('a')

        url = title_link['href']
        if not url:
            raise FormatError(f'No URL found for article {index}')
        else:
            url = urljoin(base_url, url)

        title = title_link.get_text(strip=True)
        if not title:
            raise FormatError(f'No title content found for article {index}')

        date_tag = article.select_one('time')
        date_string = date_tag['datetime']
        date = parse_datetime(date_string)

        category_tag = article.select('.coh-column')[1]
        category = category_tag.get_text(strip=True)
        tags = [category] if category else []

        return NewsItem(id=url, url=url, title=title, date_published=date,
                        tags=tags)
