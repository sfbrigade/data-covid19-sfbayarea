from power_bi_querier import PowerBiQuerier

class CasesByAge(PowerBiQuerier):
    def __init__(self) -> None:
        self.source = 'c1'
        self.name = 'cases_by_age'
        self.property = 'age_cat'
        super()

    def _parse_data(self, response_json) -> None:
        results = self._dig_results(response_json)
        return [ { 'group': group, 'count': count } for group, count in results ]


pbq = CasesByAge()
import pdb
pdb.set_trace()
print(pbq.get_data())
