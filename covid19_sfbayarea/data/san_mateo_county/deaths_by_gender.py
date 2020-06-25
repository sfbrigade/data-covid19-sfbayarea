from power_bi_querier import PowerBiQuerier

class DeathsByGender(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'd1'
        self.name = 'death by sex'
        self.property = 'sex'
        super().__init__()

    def _parse_data(self, response_json) -> None:
        results = super()._parse_data(response_json)
        return [ { gender.lower(): count } for gender, count in results ]
