import dateutil.parser
import dateutil.tz
import re
from datetime import datetime, tzinfo
from functools import reduce
from typing import Any, Dict, Iterable, List, Optional, Union
from .errors import FormatError


US_SHORT_DATE_PATTERN = re.compile(r'^\s*\d+/\d+/\d+\s*$')
PACIFIC_TIME = dateutil.tz.gettz('America/Los_Angeles')
CURRENT_YEAR = datetime.utcnow().year


def friendly_county(county_id: str) -> str:
    '''
    Transform a county ID (e.g. "san_francisco") into a more human-friendly
    name (e.g. "San Francisco").
    '''
    return county_id.replace('_', ' ').title()


def dig(items: Union[Dict[Any, Any], List[Any]], json_path: List[Any]) -> Any:
    try:
        return reduce(lambda subitem, next_step: subitem[next_step], json_path, items)
    except (KeyError, TypeError, IndexError) as err:
        print('Error reading returned JSON, check path: ', err)
        raise(err)


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


def assert_equal_sets(a: Iterable, b: Iterable, description: str = 'items') -> None:
    """
    Raise a nicely formatted exception if the two arguments do not contain the
    same items. Arguments can be any iterable; the order of items in them does
    not matter (they are treated like sets).
    """
    a_set = isinstance(a, set) and a or set(a)
    b_set = isinstance(b, set) and b or set(b)
    if a_set != b_set:
        removed = a_set - b_set
        added = b_set - a_set
        raise FormatError(f"{description} are different -- removed: {removed}, added: {added}")
