from typing import Dict, List
from .power_bi_querier import PowerBiQuerier

class CasesByGender(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c1'
        self.name = 'cases_by_sex'
        self.property = 'sex'
        super().__init__()

    def _parse_data(self, response_json: Dict[str, List]) -> List[Dict[str, int]]:
        results = super()._parse_data(response_json)
        return [ { gender.lower(): count } for gender, count in results ]
