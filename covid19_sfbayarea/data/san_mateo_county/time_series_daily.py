from datetime import datetime
from power_bi_querier import PowerBiQuerier

class TimeSeriesDaily(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c'
        self.name = 'cases_by_day'
        self.property = 'date_result'
        super().__init__()

    def _parse_data(self, response_json) -> None:
        results = super()._parse_data(response_json)
        return [ { 'date': self._timestamp_to_date(timestamp), 'cases': cases } for timestamp, cases in results ]

    def _timestamp_to_date(self, timestamp_in_milliseconds) -> None:
        return datetime.utcfromtimestamp(timestamp_in_milliseconds / 1000).strftime('%Y-%m-%d')
