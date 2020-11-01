from bs4 import BeautifulSoup, element, NavigableString  # type: ignore
from datetime import datetime
from logging import getLogger
from typing import List, Optional
from urllib.parse import urljoin
from ..utils import parse_datetime
from ..webdriver import get_firefox
from .base import NewsScraper
from .errors import FormatError
from .feed import NewsItem
from .utils import get_base_url


logger = getLogger(__name__)


# Maps the various forms of language names in the page's text to ISO language
# codes so we can determine the language of a link.
# TODO: Actually use these to handle more than just English links.
LANGUAGES = {
    'english': 'en',
    'spanish': 'es',
    'español': 'es',
    'chinese': 'zh_HANS',
    'chinese (simplified)': 'zh_HANS',   # 'zh_CN' is common, but less correct.
    'chinese (traditional)': 'zh_HANT',  # 'zh_TW' is common, but less correct.
    'korean': 'ko',
    'vietnamese': 'vi',
    'amharic': 'am',
    'arabic': 'ar',
    'farsi': 'fa',
    'persian': 'fa',
    'pashto': 'ps',
    'urdu': 'ur',
}

LANGUAGE_NAMES = set(name.casefold() for name in LANGUAGES)


def date_from_node_text(node: element.Tag) -> Optional[datetime]:
    """
    If an element contains a date as text, return the parsed date.
    """
    try:
        date_string = node.get_text().strip()
        return parse_datetime(date_string)
    except ValueError:
        return None


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
        """
        try:
            item = ItemParser.parse_node(node, base_url)
        except NotNews:
            return None

        # Some news items do not link to an English version at all, in which
        # case there will not have been a URL attached to the item. For now,
        # that's OK and we just want to skip them (but still log a notice).
        if item.url:
            return item
        else:
            logger.warning('No URL found for news item on %s', item.date_published)
            return None


class NotNews(ValueError):
    """Indicates that an HTML node did not represent a news item."""
    ...


class SkipIterationTo(Exception):
    """
    Instructs an item parser to move to a specific HTML node, rather than just
    moving to the next node in the document.

    Parameters
    ----------
    target
        The HTML node to skip to.
    """
    def __init__(self, target: element.Tag):
        self.target = target


class ItemParser:
    """
    Parses a single news item from the page, given the first element of that
    news item. This should usually be used by calling the `parse_node` class
    method like so:

        news_item = ItemParser.parse_node(document.find('strong'))

    Parsing news items in Alameda's news page is a little rough because
    each news item is not contained in a separate element. Instead, they
    are a stream of elements. Each news item is sometimes separated by a
    double `<br>` tag, but not always. News items may have a `<br>` tag
    separating the title from the lede/subhead. These `<br>` tags may also be
    nested inside various other elements! Additionally, news items with
    multiple languages will have the title as regular text followed by one link
    for each language.

    For example:

        <strong>July 17, 2020</strong>
        <a href="/path/to/news/item/page.html">Title of news item</a>
        <br>
        <br>
        <strong>July 10, 2020</strong>
        Title of multilingual news item<br>
        With a subhead:
        <a href="/path/to/news/item2/en.html">English</a> |
        <a href="/path/to/news/item2/es.html">Spanish</a> |
        <a href="/path/to/news/item2/cn.html">Chinese</a>
        <br>
        <strong>July 9, 2020</strong>
        <a href="/path/to/news/item3.html">Title of news item<br></a>
        <br>
        ...

    Because there's nothing to identify whether a `<strong>` is the start
    of a news item, this parser first attempts to determine whether it looks
    like it's actually dealing with a news item and raises a `NotNews` error if
    not. Otherwise, the parser starts iterating forward until it hits a double
    `<br>` or something that looks like the start of another news item.

    Internally, the parser is implemented as a finite state machine (FSM), and
    its `state` attribute indicates which part of the news item it is parsing.
    Actual parsing logic is implemented in methods named `parse_{state}(node)`,
    which are called as the parser iterates through HTML nodes.
    """
    START_STATE = 'date'

    @classmethod
    def parse_node(cls, node: element.Tag, base_url: str) -> NewsItem:
        """
        Parse the news item that starts with the given HTML node. Raises
        `NotNews` if the HTML node isn't actually the start of a news item.

        Parameters
        ----------
        node
            The HTML node that indicates the start of the news item. Usually a
            `<strong>` element.
        base_url
            The URL of the page the news item is being parsed from. This is
            used to make an absolute URL for news items when the markup is only
            a relative link.

        Returns
        -------
        NewsItem
            The news item that was parsed from the markup.
        """
        return cls(node, base_url).parse()

    def __init__(self, node: element.Tag, base_url: str):
        self.start_node = node
        self.base_url = base_url
        # The resulting news item
        self.item = NewsItem(id='', url='', title='', summary='')
        # Controls how the current HTML node is handled. For each node, the
        # parser calls the method named `parse_{state}`.
        self.state = ''

    def parse(self) -> NewsItem:
        """
        Parse the news item that starts with the given HTML node. Raises
        `NotNews` if the HTML node isn't actually the start of a news item.
        """
        logger.debug('Parsing node %s', self.start_node)
        self.state = self.START_STATE
        node = self.start_node
        root = node.parent
        # For some news items, the start tag is inside another element, like:
        #   <div><strong>October 28, 2020</strong></div> News Title
        # So we can't treat its parent as the root container of the whole news
        # item. Instead, we look for the nearest ancestor with a class name and
        # treat that as the root. It's a rough heuristic, but seems to work.
        while root.get('class') is None:
            if root.parent:
                root = root.parent
            else:
                root = node.parent
                break

        while node and root in node.parents:
            try:
                self.before_node(node)
                getattr(self, f'parse_{self.state}')(node)
                node = node.next_element
            except StopIteration:
                break
            except SkipIterationTo as error:
                node = error.target

        self.post_process()
        return self.item

    def before_node(self, node: element.Tag) -> None:
        # Stop if it looks like we've hit a new news item.
        if (node != self.start_node
                and node.name == 'strong'
                and date_from_node_text(node)):
            raise StopIteration()

    def parse_date(self, node: element.Tag) -> None:
        """Parse date information from the first node."""
        date = date_from_node_text(node)
        # If the first element didn't contain a date (and only a date), it
        # probably wasn't actually the start of a news item.
        if date is None:
            raise NotNews(str(node))
        else:
            self.item.date_published = date
            # Switch to parsing the title and jump forward to the next node
            # (since we don't need to look at this node's children).
            self.state = 'title'
            # Ideally, this would just be:
            #   raise SkipIterationTo(node.next_sibling)
            # But in some news entries on the page, the date is embedded in a
            # few wrapping elements, like:
            #   <div><strong>October 28, 2020</strong></div>
            raise SkipIterationTo(list(node.descendants)[-1].next_element)

    def parse_title(self, node: element.Tag) -> None:
        """Parse the news item's title."""
        if node.name == 'br':
            self.state = 'br'
        elif self.is_language_link(node):
            self.state = 'languages'
            return self.parse_languages(node)
        elif node.name == 'a':
            self.item.url = node['href']
        elif isinstance(node, NavigableString):
            self.item.title += node

    def parse_summary(self, node: element.Tag) -> None:
        """Parse the news item's summary."""
        if node.name == 'br':
            self.state = 'br'
        elif self.is_language_link(node):
            self.state = 'languages'
            return self.parse_languages(node)
        elif isinstance(node, NavigableString):
            self.item.summary += node

    def parse_languages(self, node: element.Tag) -> None:
        """Parse a language-specific link for the news item."""
        if node.name == 'br':
            self.state = 'br'
        elif (node.name == 'a'
              and node.get_text(strip=True).lower() == 'english'):
            self.item.url = node['href']

    def parse_br(self, node: element.Tag) -> None:
        """
        Determine how to handle things after hitting a `<br>` tag, which could
        be the end of the news item or a delimiter between different sections
        of the item, like date, title, and summary.
        """
        # Two `<br>`s in a row signal the end of the news item.
        if node.name == 'br':
            raise StopIteration()
        # If we've encountered title data, this was a delimiter between title
        # and summary, so switch to summary parsing.
        elif self.item.title.strip():
            self.state = 'summary'
            return self.parse_summary(node)
        # ...but if we haven't scanned a title yet, keep looking for it.
        else:
            self.state = 'title'
            return self.parse_title(node)

    def post_process(self) -> None:
        """Clean up the news item before returning it as a final result."""
        if self.item.url:
            self.item.url = urljoin(self.base_url, self.item.url)

        # ID is the same as URL in this case.
        self.item.id = self.item.url

        # Titles and summaries are sometimes followed by a colon (usually when
        # they are followed by language-specific links). If so, drop it.
        self.item.title = self.item.title.strip().strip(':')
        if not self.item.title:
            raise FormatError(f'No title content found for {self.start_node}')

        if self.item.summary:
            self.item.summary = self.item.summary.strip().strip(':')

    def is_language_link(self, node: element.Tag) -> bool:
        """
        Determine if an element looks like a link to a language-specific
        version of the news item.
        """
        if node.name != 'a':
            return False

        text = node.get_text().strip().casefold()
        return text in LANGUAGE_NAMES
