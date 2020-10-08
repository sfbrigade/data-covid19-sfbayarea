from typing import Any, Dict, List
from .power_bi_querier import PowerBiQuerier

class TimeSeriesTestsTotal(PowerBiQuerier):
    def __init__(self) -> None:
        self.function = 'Sum'
        self.model_id = 296535
        self.powerbi_resource_key = '032423d3-f7a4-473b-b50c-bf5518918335'
        self.source = 'v'
        self.name = 'V_Tests_RollingSevenDayAverage'
        self.property = 'Date'
        super().__init__()

    def _select(self) -> List[Dict[str, Any]]:
        return [
            {
                'Column': self._column_expression(self.property),
                'Name': f'{self.name}.{self.property}'
            },
            self._aggregation('RollingSevenDayAverage')
       ]

    def _binding(self) -> Dict[str, Any]:
        return {
            'Primary': { 'Groupings': [{ 'Projections': [0, 1] }] },
            'DataReduction': {
                'DataVolume': 4,
                'Primary': { 'BinnedLineSample': {} }
            },
            'Version': 1
        }
