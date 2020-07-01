from bs4 import BeautifulSoup, element  # type: ignore
from datetime import datetime, tzinfo
import dateutil.parser
import dateutil.tz
import re
import requests
from typing import Optional
from urllib.parse import urljoin
from .feed import NewsItem


HEADING_PATTERN = re.compile(r'h\d')
ISO_DATETIME_PATTERN = re.compile(r'^\d{4}-\d\d-\d\d(T|\s)\d\d:\d\d:\d\d(\.\d+)?(Z|\d{4}|\d\d:\d\d)$')
US_SHORT_DATE_PATTERN = re.compile(r'^\s*\d+/\d+/\d+\s*$')
PACIFIC_TIME = dateutil.tz.gettz('America/Los_Angeles')
CURRENT_YEAR = datetime.utcnow().year

# Sometimes we can't find a news feed that is specific to COVID-19, so the news
# items we scrape need to be filtered. These key terms are used to test whether
# a news item should be included.
COVID_KEY_TERMS = frozenset((
    'covid',
    'coronavirus',
    'health',
    'reopening',
    'stay at home',
    'stay-at-home',
    'shelter in place',
    'shelter-in-place'
))

# Matches a <meta> tag in HTML used to specify the character encoding:
# <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
# <meta charset="utf-8" />
META_TAG_PATTERN = re.compile(
    b'<meta[^>]+charset\\s*=\\s*[\'"]?([^>]*?)[ /;\'">]',
    re.IGNORECASE)

# Matches an XML prolog that specifies character encoding:
# <?xml version="1.0" encoding="ISO-8859-1"?>
XML_PROLOG_PATTERN = re.compile(
    b'<\\?xml\\s[^>]*encoding=[\'"]([^\'"]+)[\'"].*\\?>',
    re.IGNORECASE)


def get_base_url(soup: BeautifulSoup, url: str) -> str:
    """
    Get the base URL for a BeautifulSoup page, given the URL it was loaded
    from. This can then be used with ``urllib.parse.urljoin`` to make sure any
    link or resource URL on the page to get the absolute URL it refers to.

    Parameters
    ----------
    soup : BeautifulSoup
        A BeautifulSoup-parsed web page.
    url : str
        The URL that the web page was loaded from.

    Returns
    -------
    str
    """
    base = soup.find('base')
    if base and base['href']:
        return urljoin(url, base['href'].strip())
    else:
        return url


def first_text_in_element(parent: element.Tag) -> Optional[str]:
    """
    Get the first piece of non-whitespace text in an element (including deeply
    nested text).

    Parameters
    ----------
    parent
        The BeautifulSoup element to search within.

    Returns
    -------
    str or None

    Examples
    --------
    >>> soup = BeautifulSoup('''
    >>>    <html>
    >>>        <body>
    >>>            <p>
    >>>                <br>
    >>>                Hello
    >>>                <span>Extra Stuff</span>
    >>>            </p>
    >>>        </body>
    >>>    </html>
    >>>    ''')
    >>> first_text_in_element(soup.body)
    'Hello'
    """
    for child in parent.contents:
        if isinstance(child, str):
            clean = child.strip()
            if clean:
                return clean
        elif isinstance(child, element.Tag):
            descendent_text = first_text_in_element(child)
            if descendent_text:
                return descendent_text

    return None


def parse_datetime(date_string: str, timezone: Optional[tzinfo] = PACIFIC_TIME) -> datetime:
    """
    Parse a datetime from a string and ensure it always has a timezone set. Use
    the `timezone` argument to set the timezone to use if none was specified in
    the parsed string.
    """
    # Handle dumb typos that might be in the dates on the page :(
    if US_SHORT_DATE_PATTERN.match(date_string):
        if date_string.endswith('/202'):
            date_string += '0'

    date = dateutil.parser.parse(date_string)
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone)

    # Gut-check whether this date seems reasonable
    if abs(CURRENT_YEAR - date.year) > 5:
        raise ValueError(f'Unknown date format: "{date_string}"')

    return date


# NOTE: This is adapted from:
# https://github.com/edgi-govdata-archiving/web-monitoring-processing
def guess_html_encoding(response: requests.Response) -> Optional[str]:
    """
    Attempt to determine the encoding of an HTML document. This is useful for
    responses that don't include the encoding as a header (where requests will
    automatically pick it up).

    There are a few improvements that could be made here for maximum
    correctness (such as using cchardet), but this covers all our existing
    cases well enough for now.
    """
    encoding = None
    content_type = response.headers.get('Content-Type', '').lower()
    if 'charset=' in content_type:
        encoding = content_type.split('charset=')[-1]
    if not encoding:
        meta_tag_match = META_TAG_PATTERN.search(response.content, endpos=2048)
        if meta_tag_match:
            encoding = meta_tag_match.group(1).decode('ascii', errors='ignore')
    if not encoding:
        prolog_match = XML_PROLOG_PATTERN.search(response.content, endpos=2048)
        if prolog_match:
            encoding = prolog_match.group(1).decode('ascii', errors='ignore')
    if encoding:
        encoding = encoding.strip()

    return encoding


def decode_html_body(response: requests.Response) -> str:
    encoding = guess_html_encoding(response)
    if encoding:
        return response.content.decode(encoding, errors='replace')
    else:
        # If we couldn't guess the encoding, let requests do its best.
        return response.text


def find_with_text(soup: BeautifulSoup, text: str, tag_name: str = None) -> Optional[element.Tag]:
    def match_element(tag: element.Tag) -> bool:
        if text in tag.get_text():
            if not tag_name or tag.name == tag_name:
                return True
        return False

    return soup.find(match_element)


def is_covid_related(item: NewsItem) -> bool:
    comparable = ' '.join([
        item.title,
        item.summary or '',
        item.url,
        *item.tags
    ]).lower()
    return any(term in comparable for term in COVID_KEY_TERMS)
