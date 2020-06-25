from power_bi_querier import PowerBiQuerier

class DeathsByEthnicity(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'd'
        self.name = 'deaths by race'
        self.property = 'race'
        super().__init__()

    def _parse_data(self, response_json) -> None:
        results = super()._parse_data(response_json)
        return [ { ethnicity.strip(): count } for ethnicity, count in results ]
