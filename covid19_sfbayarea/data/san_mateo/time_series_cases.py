from datetime import datetime
from typing import Any, Dict, List

from .power_bi_querier import PowerBiQuerier

class TimeSeriesCases(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c'
        self.name = 'cases_by_day'
        self.property = 'date_result'
        super().__init__()

    def _parse_data(self, response_json: Dict) -> List[Dict[str, Any]]:
        data_pairs = super()._parse_data(response_json)
        results = [ { 'date': self._timestamp_to_date(timestamp), 'cases': cases } for timestamp, cases in data_pairs ]
        self._add_cumulative_data(results)
        return results

    def _timestamp_to_date(self, timestamp_in_milliseconds: int) -> str:
        return datetime.utcfromtimestamp(timestamp_in_milliseconds / 1000).strftime('%Y-%m-%d')

    def _add_cumulative_data(self, results: List[Dict[str, Any]]) -> None:
        running_total = 0
        for result in results:
            running_total += result['cases']
            result['cumul_cases'] = running_total
