from power_bi_querier import PowerBiQuerier

class CasesByAge(PowerBiQuerier):
    def _parse_data(self, response_json) -> None:
        results = self._dig(self.path, response_json)
        data_pairs = [ result['C'] for result in results[1:-1] ]
        return [ { 'group': group, 'count': count } for group, count in data_pairs ]
