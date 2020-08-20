from typing import Any, Dict, List
from .power_bi_querier import PowerBiQuerier

class TimeSeriesCumulative(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c'
        self.name = 'cases_by_day'
        self.property = 'date_result'
        super().__init__()

    def _parse_data(self, response_json: Dict) -> Dict[int, int]: # type: ignore
        data_pairs = super()._parse_data(response_json)
        return { timestamp: cases for timestamp, cases in data_pairs }

    def _select(self) -> List[Dict[str, Any]]:
        measure = f'Sum of n running total in {self.property}'
        return [
            {
                'Column': self._column_expression(self.property),
                'Name': f'{self.name}.{self.property}'
            },
            {
                'Measure': {
                    **self._column_expression(self.property),
                    'Property': measure
                },
                'Name': f'{self.name}.{measure}'
            }
        ]

    def _binding(self) -> Dict[str, Any]:
        return {
            'DataReduction': {
                'DataVolume': 4,
                'Primary': { 'Sample': {} }
            },
            'Primary': {
                'Groupings': [{'Projections': [0, 1] }]
            },
            'Version': 1
        }
