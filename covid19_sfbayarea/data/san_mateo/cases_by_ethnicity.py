from typing import Dict, List
from .power_bi_querier import PowerBiQuerier

class CasesByEthnicity(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c'
        self.name = 'cases_by_race'
        self.property = 'race_cat'
        super().__init__()

    def _parse_data(self, response_json: Dict[str, List]) -> Dict[str, int]:
        results = super()._parse_data(response_json)
        return { self._map_ethnicity_to_data_model(ethnicity.strip()): count for ethnicity, count in results }

    def _map_ethnicity_to_data_model(self, ethnicity: str) -> str:
        mapping = {
            'American Indian/Alaska Native': 'Native_Amer',
            'Asian': 'Asian',
            'Latino/Hispanic': 'Latinx_or_Hispanic',
            'Black': 'African_Amer',
            'Multirace': 'Multiple_Race',
            'Other': 'Other',
            'Pacific Islander': 'Pacific_Islander',
            'White': 'White',
            'Unknown': 'Unknown'
        }
        return mapping.get(ethnicity, ethnicity)
