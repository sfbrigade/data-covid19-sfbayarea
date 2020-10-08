from typing import Any, Dict, List
from .power_bi_querier import PowerBiQuerier
from .utils import dig

class CasesByEthnicity(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'v'
        self.name = 'V_RaceEth_Rates'
        self.property = 'RaceEth'
        super().__init__()

    def _parse_data(self, response_json: Dict[str, List]) -> Dict[str, int]:
        results = super()._parse_data(response_json)
        ethnicity_labels = dig(response_json, [*self.JSON_PATH[0:-3], 'ValueDicts', 'D0'])
        return { ethnicity_labels[ethnicity_label_index].strip(): count for ethnicity_label_index, count in results }

    def _select(self) -> List[Dict[str, Any]]:
        return [
            {
                'Column': self._column_expression(self.property),
                'Name': f'{self.name}.{self.property}'
            },
            self._aggregation('Cases')
       ]
