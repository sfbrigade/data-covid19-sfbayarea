from datetime import datetime
from typing import Any, Dict, List
from .power_bi_querier import PowerBiQuerier

class TimeSeriesTests(PowerBiQuerier):
    def __init__(self) -> None:
        self.function = 'Sum'
        self.model_id = 275728
        self.powerbi_resource_key = '1b96a93b-9500-44cf-a3ce-942805b455ce'
        self.source = 'l'
        self.name = 'lab_tests_by_day'
        self.property = 'early_spec_date'
        super().__init__()

    def _parse_data(self, response_json: Dict) -> List[Dict[str, Any]]:
        data_pairs = super()._parse_data(response_json)
        results = [
            {
                'date': self._timestamp_to_date(timestamp),
                'tests': positive + negative + pending,
                'positive': positive,
                'negative': negative,
                'pending': pending
            } for timestamp, positive, pending, negative in data_pairs
        ]
        self._add_cumulative_data(results)
        return results

    def _timestamp_to_date(self, timestamp_in_milliseconds: int) -> str:
        return datetime.utcfromtimestamp(timestamp_in_milliseconds / 1000).strftime('%Y-%m-%d')

    def _add_cumulative_data(self, results: List[Dict[str, Any]]) -> None:
        running_totals = { 'cumul_tests': 0, 'cumul_pos': 0, 'cumul_neg': 0, 'cumul_pend': 0 }
        for result in results:
            running_totals['cumul_tests'] += result['tests']
            running_totals['cumul_pos'] += result['positive']
            running_totals['cumul_neg'] += result['negative']
            running_totals['cumul_pend'] += result['pending']
            result.update(running_totals)

    def _select(self) -> List[Dict[str, Any]]:
        return [
            {
                'Column': self._column_expression(self.property),
                'Name': f'{self.name}.{self.property}'
            },
            self._aggregation('Positive'),
            self._aggregation('Inconclusive'),
            self._aggregation('Negative')
        ]

    def _binding(self) -> Dict[str, Any]:
        return {
            'Primary': { 'Groupings': [{ 'Projections': [0, 1, 2, 3] }] },
            'DataReduction': {
                'DataVolume': 4,
                'Primary': { 'Sample': {} }
            },
            'Version': 1
        }
