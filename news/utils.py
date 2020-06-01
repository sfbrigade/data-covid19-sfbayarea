from bs4 import BeautifulSoup, element  # type: ignore
import dateutil.tz
import re
from typing import Optional
from urllib.parse import urljoin


HEADING_PATTERN = re.compile(r'h\d')
ISO_DATETIME_PATTERN = re.compile(r'^\d{4}-\d\d-\d\d(T|\s)\d\d:\d\d:\d\d(\.\d+)?(Z|\d{4}|\d\d:\d\d)$')
PACIFIC_TIME = dateutil.tz.gettz('America/Los_Angeles')


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
