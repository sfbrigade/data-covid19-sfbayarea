from datetime import datetime
from power_bi_querier import PowerBiQuerier

class TimeSeriesCases(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c'
        self.name = 'cases_by_day'
        self.property = 'date_result'
        super().__init__()

    def _parse_data(self, response_json) -> None:
        data_pairs = super()._parse_data(response_json)
        results = [ { 'date': self._timestamp_to_date(timestamp), 'cases': cases } for timestamp, cases in data_pairs ]
        self._add_cumulative_data(results)
        return results

    def _timestamp_to_date(self, timestamp_in_milliseconds) -> None:
        return datetime.utcfromtimestamp(timestamp_in_milliseconds / 1000).strftime('%Y-%m-%d')

    def _add_cumulative_data(self, results) -> None:
        running_total = 0
        for result in results:
            running_total += result['cases']
            result['cumul_cases'] = running_total
