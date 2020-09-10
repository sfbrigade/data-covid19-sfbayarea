from typing import Any, Dict, List

from .power_bi_querier import PowerBiQuerier

class TimeSeriesDaily(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'v'
        self.name = 'V_Combined_data'
        self.property = 'DtCreate'
        super().__init__()

    def _parse_data(self, response_json: Dict) -> Dict[int, int]:
        data_pairs = super()._parse_data(response_json)
        return { timestamp: cases for timestamp, cases in data_pairs }

    def _select(self) -> List[Dict[str, Any]]:
        measure = 'NumberOfCases'
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
