from datetime import datetime
from typing import Any, Dict, List

from .daily import Daily
from .cumulative import Cumulative

class TimeSeriesDeaths():
    def get_data(self) -> List[Dict[str, Any]]:
        daily_deaths = dict(Daily().get_data())
        cumulative_deaths = dict(Cumulative().get_data())
        self._assert_daily_and_cumulative_deaths_match(daily_deaths, cumulative_deaths)

        return [{
            'date': self._timestamp_to_date(timestamp),
            'deaths': daily_deaths[timestamp],
            'cumul_deaths': cumulative_deaths[timestamp]
        } for timestamp in daily_deaths.keys()]

    def _timestamp_to_date(self, timestamp_in_milliseconds: int) -> str:
        return datetime.utcfromtimestamp(timestamp_in_milliseconds / 1000).strftime('%Y-%m-%d')

    def _assert_daily_and_cumulative_deaths_match(self, daily_deaths: Dict[int, int], cumulative_deaths: Dict[int, int]) -> None:
        if daily_deaths.keys() != cumulative_deaths.keys():
            raise(ValueError('The cumulative and daily deaths do not have the same timestamps!'))
