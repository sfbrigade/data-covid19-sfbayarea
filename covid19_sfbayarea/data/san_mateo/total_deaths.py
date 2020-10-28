from typing import Any, Dict, List, cast
from .power_bi_querier import PowerBiQuerier
from covid19_sfbayarea.utils import dig

class TotalDeaths(PowerBiQuerier):
    JSON_PATH = ['results', 0, 'result', 'data', 'dsr', 'DS', 0, 'PH', 0, 'DM0', 0, 'M0']
    def __init__(self) -> None:
        self.function = 'Sum'
        self.name = 'deaths by race'
        self.property = 'n'
        self.source = 'd1'
        super().__init__()

    def _parse_data(self, response_json: Dict[str, List]) -> int: # type: ignore
        return cast(int, dig(response_json, self.JSON_PATH))

    def _select(self) -> List[Dict[str, Any]]:
        return [self._aggregation('n')]

    def _binding(self) -> Dict[str, Any]:
        return {
            'Primary': { 'Groupings': [{ 'Projections': [0] }] },
            'DataReduction': {
                'DataVolume': 3,
                'Primary': { 'Top': {} }
            },
            'Version': 1
        }
