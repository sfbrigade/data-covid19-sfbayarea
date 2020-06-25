from datetime import datetime
from power_bi_querier import PowerBiQuerier

class TimeSeries(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c'
        self.name = 'cases_by_day'
        self.property = 'date_result'
        super()

    def _parse_data(self, response_json) -> None:
        results = self._dig_results(response_json)
        data_pairs = map(self._extract_pair, results)
        return [ { 'date': self._timestamp_to_date(timestamp), 'cases': cases } for timestamp, cases in data_pairs ]

    def _extract_pair(self, result) -> None:
        if len(result) == 2:
            return result
        else:
            return [result[0], 0]

    def _timestamp_to_date(self, timestamp_in_milliseconds) -> None:
        return datetime.utcfromtimestamp(timestamp_in_milliseconds / 1000).strftime('%Y-%m-%d')
