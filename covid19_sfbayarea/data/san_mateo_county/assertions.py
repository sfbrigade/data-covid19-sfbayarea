import re
from bs4.element import Tag
from typing import Dict, List

class Assertions:
    """
    Class to encapsulate assertions.

    These are mostly designed to ensure the webpage hasn't changed and was loaded correctly.
    """
    def iframes_match(self, iframes: List[Tag]) -> None:
        if len(iframes) != 5:
            raise FutureWarning('The number of dashboards on the start page has changed. It was 5.')

        if sum('https://app.powerbigov.us' in iframe['src'] for iframe in iframes) != 4:
            raise FutureWarning('iframes no longer recognized, check contents of page at START_URL.')

    def charts_match(self, charts: List[Tag]) -> None:
        if len(charts) != 8:
            raise FutureWarning('This page has changed. There were previously eight bar charts.')


    def regex_match(self, regex: str, match_string: str, message='String failed to match regular expression.') -> None:
        if not re.match(regex, match_string):
            raise FutureWarning(message)

    def dates_match(self, cumulative_cases: List[Dict[str, int]], daily_cases: List[Dict[str, int]]) -> None:
        if [day['date'] for day in cumulative_cases] != [day['date'] for day in daily_cases]:
            raise(FutureWarning('Cumulative and daily cases have inconsistent dates.'))
