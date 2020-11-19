from typing import Any, Dict, List
from .power_bi_querier import PowerBiQuerier
from covid19_sfbayarea.utils import dig

class DeathsByEthnicity(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'v'
        self.name = 'V_RaceEth_Rates'
        self.property = 'RaceEth'
        super().__init__()

    def _parse_data(self, response_json: Dict[str, List]) -> Dict[str, int]:
        results = super()._parse_data(response_json)
        ethnicity_labels = dig(response_json, [*self.json_path[0:-3], 'ValueDicts', 'D0'])
        totals = {'Overall', 'Overall Known Race/Ethnicity'}
        return {
            ethnicity_label: count
            for ethnicity_label_index, count in results
            if (ethnicity_label := ethnicity_labels[ethnicity_label_index].strip()) not in totals
        }


    def _select(self) -> List[Dict[str, Any]]:
        return [
            {
                'Column': self._column_expression(self.property),
                'Name': f'{self.name}.{self.property}'
            },
            self._aggregation('Deaths')
       ]
