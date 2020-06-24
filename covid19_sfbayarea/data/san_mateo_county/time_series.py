from datetime import datetime
from power_bi_querier import PowerBiQuerier

class TimeSeries(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c'
        self.name = 'cases_by_day'
        self.property = 'date_result'
        self.json_path = ['results', 0, 'result', 'data', 'dsr', 'DS', 0, 'PH', 0, 'DM0']
        super()

    def _parse_data(self, response_json) -> None:
        results = self._dig(self.json_path, response_json)
        data_pairs = map(self._extract_pair, results)
        return [ { 'date': self._timestamp_to_date(timestamp), 'cases': cases } for timestamp, cases in data_pairs ]

    def _extract_pair(self, result) -> None:
        if len(result['C']) == 2:
            return result['C']
        else:
            return [result['C'][0], 0]

    def _timestamp_to_date(self, timestamp_in_milliseconds) -> None:
        return datetime.utcfromtimestamp(timestamp_in_milliseconds / 1000).strftime('%Y-%m-%d')


pbq = TimeSeries()
import pdb
pdb.set_trace()
print(pbq.fetch_data())
