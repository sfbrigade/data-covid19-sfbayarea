from bs4 import BeautifulSoup, element  # type: ignore
from typing import List
from urllib.parse import urljoin
from .base import NewsScraper
from .errors import FormatError
from .feed import NewsItem
from .utils import find_with_text, get_base_url, parse_datetime


class MarinNews(NewsScraper):
    """
    Scrape official county COVID-related news from Marin County. This scrapes
    the county's press releases page (there's no RSS feed) for news from the
    health & human services department.

    NOTE: this source page does not have summaries or excerpts, so the feed
    this outputs does not, either.

    There are some other sources that might be useful to look into here:

    - Other departments on this page. They require some artful filtering to get
      just the COVID-related news, though.

    - The Health & Human Services department has its own "updates" page, but
      news is broken up in a more complex way that is harder to deal with.
      https://coronavirus.marinhhs.org/updates?field_categories_target_id=All
        - Items are broken up by type: press releases, public health orders,
          and daily status updates.
        - Press releases is not being updated at the moment and so does not
          list all the press releases the county press releases page does.
        - Public health orders are the actual text of the orders, which is
          probably not the most readable or informative for most people.
        - Daily updates actually contain nicely worded, useful blurbs on all
          the press releases and news (the best of all sources in terms of
          approachability and readability), buuuut they are hard to parse:
            - The excerpt on the main listing doesn't tell us anything useful
              about the news inside (or if there even is any), so we'd actually
              have to parse a page for each date.
            - The page for each status update has updated stats, followed by
              some explanation, followed by news, followed other recaps and
              links to resources. We only care about the news part, and it's
              tough to separate that out in a reliable way.
            - News items are repeated on subsequent days. For example, both
              May 29th and May 30th list "Additional Businesses Greenlighted"
              and "New Orders for Parks":
              - https://coronavirus.marinhhs.org/covid-19-status-update-05292020
              - https://coronavirus.marinhhs.org/covid-19-status-update-05302020
            - One way to handle this might be to parse the press releases page
              like we do now, but combine all releases that were on the same
              day and link to the status update for that day.

    Examples
    --------
    >>> scraper = MarinNews()
    >>> scraper.scrape()
    """

    FEED_INFO = dict(
        title='Sonoma County COVID-19 News',
        home_page_url='https://www.marincounty.org/main/county-press-releases'
    )

    URL = 'https://www.marincounty.org/main/county-press-releases?sort=dept'

    def parse_page(self, html: str, url: str) -> List[NewsItem]:
        soup = BeautifulSoup(html, 'html5lib')
        base_url = get_base_url(soup, url)
        department = 'Health & Human Services'
        table_label = find_with_text(soup, department, 'caption')
        table = table_label and table_label.parent
        if not table:
            raise FormatError(f'Could find articles for "{department}"')

        header, *rows = table.find_all('tr')
        if not header.find(class_='pr-list-date-header'):
            raise FormatError('The first row does not appear to be a header')

        if len(rows) == 0:
            raise FormatError('Could not find any news items on page')

        return [self.parse_news_item(article, base_url)
                for article in rows]

    def parse_news_item(self, item_element: element.Tag, base_url: str) -> NewsItem:
        title_link = item_element.select_one('.pr-list-title a')

        url = title_link['href']
        if not url:
            raise FormatError('No URL found for article')
        else:
            url = urljoin(base_url, url)

        title = title_link.get_text(strip=True)
        if not title:
            raise FormatError('No title content found')

        date_string = item_element.select_one('.pr-list-date').get_text(strip=True)
        date = parse_datetime(date_string)

        return NewsItem(id=url, url=url, title=title, date_published=date)
