from typing import Dict, List
from .power_bi_querier import PowerBiQuerier
from .utils import map_ethnicity_to_data_model

class CasesByEthnicity(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c'
        self.name = 'cases_by_race'
        self.property = 'race_cat'
        super().__init__()

    def _parse_data(self, response_json: Dict[str, List]) -> Dict[str, int]: # type: ignore
        results = super()._parse_data(response_json)
        return { map_ethnicity_to_data_model(ethnicity): count for ethnicity, count in results }
