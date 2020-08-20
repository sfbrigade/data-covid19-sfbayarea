from datetime import datetime
from typing import Any, Dict, List

from .power_bi_querier import PowerBiQuerier

class TimeSeriesDaily(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c'
        self.name = 'cases_by_day'
        self.property = 'date_result'
        super().__init__()

    def _parse_data(self, response_json: Dict) -> List[Dict[str, Any]]:
        data_pairs = super()._parse_data(response_json)
        return { timestamp: cases for timestamp, cases in data_pairs }
