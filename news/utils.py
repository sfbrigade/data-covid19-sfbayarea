import re
from urllib.parse import urljoin


HEADING_PATTERN = re.compile(r'h\d')
ISO_DATETIME_PATTERN = re.compile(r'^\d{4}-\d\d-\d\d(T|\s)\d\d:\d\d:\d\d(\.\d+)?(Z|\d{4}|\d\d:\d\d)$')


def get_base_url(soup, url):
    base = soup.find('base')
    if base and base['href']:
        return urljoin(url, base['href'].strip())
    else:
        return url
