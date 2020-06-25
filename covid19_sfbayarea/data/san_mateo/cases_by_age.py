from typing import Dict, List
from .power_bi_querier import PowerBiQuerier

class CasesByAge(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c1'
        self.name = 'cases_by_age'
        self.property = 'age_cat'
        super().__init__()

    def _parse_data(self, response_json: Dict[str, List]) -> List[Dict[str, int]]:
        results = super()._parse_data(response_json)
        return [ { 'group': group, 'count': count } for group, count in results ]
