from bs4 import BeautifulSoup  # type: ignore
import re
from urllib.parse import urljoin


HEADING_PATTERN = re.compile(r'h\d')
ISO_DATETIME_PATTERN = re.compile(r'^\d{4}-\d\d-\d\d(T|\s)\d\d:\d\d:\d\d(\.\d+)?(Z|\d{4}|\d\d:\d\d)$')


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
