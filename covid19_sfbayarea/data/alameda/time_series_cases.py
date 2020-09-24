from datetime import datetime
from typing import Any, Dict, List, cast

from .time_series_daily import TimeSeriesDaily
from .time_series_cumulative import TimeSeriesCumulative

class TimeSeriesCases():
    def get_data(self) -> List[Dict[str, Any]]:
        daily_cases = dict(TimeSeriesDaily().get_data())
        cumulative_cases =dict(TimeSeriesCumulative().get_data())
        self._assert_daily_and_cumulative_cases_match(daily_cases, cumulative_cases)

        return [{
            'date': self._timestamp_to_date(timestamp),
            'cases': daily_cases[timestamp],
            'cumul_cases': cumulative_cases[timestamp]
        } for timestamp in daily_cases.keys()]

    def _timestamp_to_date(self, timestamp_in_milliseconds: int) -> str:
        return datetime.utcfromtimestamp(timestamp_in_milliseconds / 1000).strftime('%Y-%m-%d')

    def _assert_daily_and_cumulative_cases_match(self, daily_cases: Dict[int, int], cumulative_cases: Dict[int, int]) -> None:
        if daily_cases.keys() != cumulative_cases.keys():
            raise(ValueError('The cumulative and daily cases do not have the same timestamps!'))
