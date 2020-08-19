from bs4 import BeautifulSoup, element, NavigableString  # type: ignore
from typing import List, Optional
from urllib.parse import urljoin
from ..webdriver import get_firefox
from .base import NewsScraper
from .errors import FormatError
from .feed import NewsItem
from .utils import get_base_url, parse_datetime


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
        home_page_url='https://covid-19.acgov.org/press.page'
    )

    URL = 'https://covid-19.acgov.org/press.page'

    def load_html(self, url: str) -> str:
        with get_firefox() as driver:
            # This page does a kind of nutty thing: it loads some javascript
            # that sets a cookie, then reloads the page, which then gives us
            # the actual content. Soooooo, we have to look for something that
            # looks like page content before continuing on (or fail if it never
            # shows up). This is also why we are using Selenium. :(
            driver.get(self.URL)
            driver.implicitly_wait(10)
            content = driver.find_element_by_id('mainCol')
            if not content:
                raise ValueError(f'Page did not load properly: {self.URL}')

            return driver.page_source

    def parse_page(self, html: str, url: str) -> List[NewsItem]:
        soup = BeautifulSoup(html, 'html5lib')
        base_url = get_base_url(soup, url)
        # Article listings do not have a containing element, but they start
        # with `<strong>date</strong>`. Look for these candidates and try to
        # parse each one.
        article_starts = soup.select_one('#mainCol').find_all('strong')

        # Because we only have items that *might* be news items, we have to
        # filter out the `None` items (those that weren't actually news).
        parsed = (self.parse_news_item(starter, base_url)
                  for starter in article_starts)
        articles = [item for item in parsed if item is not None]

        # Sanity check that we are parsing correctly. Because we silently
        # filter out things that parsed incorrectly (since we only
        # know *candidates* for news items, not things that are news items),
        # we might not have errors if the page changes. It's more likely that
        # we are parsing incorrectly in this case than that there was no news.
        if len(articles) == 0:
            raise FormatError('No news items found for Alameda County')

        return articles

    def parse_news_item(self, node: element.Tag, base_url: str) -> Optional[NewsItem]:
        """
        Parse a single news item from the page based on the first element of
        the news item.

        Parsing news items in Alameda's news page is a little rough because
        each news item is not contained in a separate element. Instead, they
        are a stream of elements, where each news item is separated by a double
        `<br>` tag like so:

            <strong>July 17, 2020</strong>
            <a href="/path/to/news/item/page.html">Title of news item</a>
            <br>
            <strong>July 10, 2020</strong>
            <a href="/path/to/news/item2/page.html">Title of news item 2</a>
            <br>
            ...

        Because there's nothing to identify whether a `<strong>` is the start
        of a news item, we first test whether its content is parseable as a
        date. If not, it's probably not a news item and we return `None`.
        Otherwise, we start iterating forward from the first tag until we hit
        a `<br>`.
        """
        try:
            date_string = node.get_text(strip=True)
            date = parse_datetime(date_string)
        except ValueError:
            # If the first element didn't contain a date, it probably wasn't
            # actually the start of an article. Bail out.
            return None

        # Iterate forward through the elements after the initial date to find
        # the different parts of the news item. These generally come in one of
        # two flavors:
        #
        #     <strong>July 17, 2020</strong>
        #     <a href="/path/to/article.html">Title of news item</a>
        #     <br>
        #
        # Or for items with multiple languages:
        #
        #     <strong>July 17, 2020</strong>
        #     The title of the news article
        #     <a href="/path/to/english/article.html">English</a> |
        #     <a href="/path/to/spanish/article.html">Spanish</a> |
        #     <br>
        #
        url = None
        title = ''
        for sibling in node.next_siblings:
            # <br> tags signal the end of the news item.
            if sibling.name == 'br':
                break
            # A link might contain the title, or it might be the language-
            # specific link to the article that comes after the title (for
            # articles with multiple languages).
            elif sibling.name == 'a':
                url = sibling['href']
                link_text = sibling.get_text()
                if link_text.lower() != 'english':
                    title = link_text
                break
            # Anything else is probably part of the title.
            elif isinstance(sibling, NavigableString):
                title += sibling
            else:
                title += sibling.get_text()

        # These titles are sometimes followed by a colon. If so, drop it.
        title = title.strip().strip(':')

        if url:
            url = urljoin(base_url, url)
        else:
            raise FormatError('No URL found')

        if not title:
            raise FormatError('No title content found')

        return NewsItem(id=url, url=url, title=title, date_published=date)
