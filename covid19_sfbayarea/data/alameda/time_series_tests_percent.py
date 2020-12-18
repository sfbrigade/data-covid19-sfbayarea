from typing import Any, Dict, List
from .power_bi_querier import PowerBiQuerier

class TimeSeriesTestsPercent(PowerBiQuerier):
    def __init__(self) -> None:
        self.function = 'Sum'
        self.model_id = 296535
        self.powerbi_resource_key = '032423d3-f7a4-473b-b50c-bf5518918335'
        self.source = 'v'
        self.name = 'V_Tests_RollingSevenDayPercentagePositive'
        self.property = 'Date'
        super().__init__()

    def _select(self) -> List[Dict[str, Any]]:
        return [
            {
                'Column': self._column_expression(self.property),
                'Name': f'{self.name}.{self.property}'
            },
            self._aggregation('RollingSevenDayPercentagePositiveTests')
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

    def get_data(self) -> List:
        # The values in this dataset can sometimes be strings. It looks like
        # PowerBI probably sends strings for values that cannot be represented
        # by a float64 (since JSON only supports 64-bit floats for numbers).
        # For example, '7.2322939999999996' gets sent as a string; the closest
        # float64 representation is '7.232294'.
        #
        # For our purposes, the loss of precision here is OK, and we want to do
        # math with the numbers here, so just convert to a float.
        data = super().get_data()
        return [[item[0], float(item[1])] if len(item) > 1 else item
                for item in data]
