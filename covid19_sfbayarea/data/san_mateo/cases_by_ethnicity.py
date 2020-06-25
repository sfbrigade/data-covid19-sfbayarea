from typing import Dict, List
from .power_bi_querier import PowerBiQuerier

class CasesByEthnicity(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c'
        self.name = 'cases_by_race'
        self.property = 'race_cat'
        super().__init__()

    def _parse_data(self, response_json: Dict[str, List]) -> List[Dict[str, int]]:
        results = super()._parse_data(response_json)
        return [ { ethnicity.strip(): count } for ethnicity, count in results ]
