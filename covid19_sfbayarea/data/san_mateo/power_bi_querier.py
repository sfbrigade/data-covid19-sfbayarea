import json
from functools import reduce
from requests import post
from typing import Any, Dict, List

class PowerBiQuerier:
    BASE_URI = 'https://wabi-us-gov-iowa-api.analysis.usgovcloudapi.net/public/reports/querydata?synchronous=true'
    JSON_PATH = ['results', 0, 'result', 'data', 'dsr', 'DS', 0, 'PH', 0, 'DM0']
    DEFAULT_MODEL_ID = 275725
    DEFAULT_POWERBI_RESOURCE_KEY = '86dc380f-4914-4cff-b2a5-03af9f292bbd'

    def __init__(self) -> None:
        self._set_defaults()
        self._assert_init_variables_are_set()

    def get_data(self) -> List:
        response_json = self._fetch_data()
        return self._parse_data(response_json)

    def _set_defaults(self) -> None:
        self.model_id = getattr(self, 'model_id', self.DEFAULT_MODEL_ID)
        self.name = getattr(self, 'name')
        self.powerbi_resource_key = getattr(self, 'powerbi_resource_key', self.DEFAULT_POWERBI_RESOURCE_KEY)
        self.property = getattr(self, 'property')
        self.source = getattr(self, 'source')

    def _fetch_data(self) -> Dict:
        response = post( self.BASE_URI, headers = { 'X-PowerBI-ResourceKey': self.powerbi_resource_key }, json = self._query_params())
        response.raise_for_status()
        return response.json()

    def _parse_data(self, response_json: Dict[str, List]) -> List:
        results = self._dig_results(response_json)
        return self._extract_lists(results)

    def _query_params(self) -> Dict[str, Any]:
        return {
            'version': '1.0.0',
            'queries': [self._query()],
            'cancelQueries': [],
            'modelId': self.model_id
        }

    def _query(self) -> Dict[str, Any]:
        return {
            'Query': { 'Commands': [self._command()] },
            'CacheKey': json.dumps({ 'Commands': [self._command()] }),
            'QueryId': '',
            'ApplicationContext': {
                'DatasetId':'aa4631ab-2f78-40f6-b4c4-d2f5f8a89bcc',
                'Sources': [{ 'ReportId': 'baf74baa-bdc9-4c71-995a-b996f1d0b7e9' }]
            }
        }

    def _command(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return {
             'SemanticQueryDataShapeCommand': {
                 'Query': {
                     'Version': 2,
                     'From': [{ 'Name': self.source, 'Entity': self.name }],
                     'Select': self._select(),
                     'OrderBy': self._order_by()
                 },
                 'Binding': self._binding()
             }
         }

    def _select(self) -> List[Dict[str, Any]]:
        return [
            {
                'Column': self._column_expression(self.property),
                'Name': f'{self.name}.{self.property}'
            },
            {
                'Aggregation': {
                    'Expression': { 'Column': self._column_expression('n') },
                    'Function': 0
                },
                'Name': f'CountNonNull({self.name}.n)'
            }
       ]

    def _order_by(self) -> List[Dict[str, Any]]:
        return [
            {
                'Direction': 1,
                'Expression': { 'Column': self._column_expression(self.property) }
            }
        ]

    def _column_expression(self, property: str) -> Dict[str, Any]:
        return {
            'Expression': { 'SourceRef': { 'Source': self.source } },
            'Property': property
        }

    def _binding(self) -> Dict[str, Any]:
        return {
            'Primary': { 'Groupings': [{ 'Projections': [0, 1] }] },
            'DataReduction': {
                'DataVolume': 4,
                'Primary': { 'Window': { 'Count': 1000 } }
            },
            'Version': 1
        }

    def _assert_init_variables_are_set(self) -> None:
        if not (getattr(self, 'source') and getattr(self, 'name') and getattr(self, 'property')):
            raise(UnboundLocalError('Please set source, name, and property.'))

    def _dig_results(self, results: Dict[str, List]) -> List[Dict[str, int]]:
        try:
            return reduce(lambda subitem, next_step: subitem[next_step], self.JSON_PATH, results) # type: ignore
        except (KeyError, TypeError, IndexError) as err:
            print('Error reading returned JSON, check path: ', err)
            raise(err)

    def _extract_lists(self, results: List[Dict]) -> List[List]:
        pairs: List[List] = []
        for result in results:
            if 'R' in result:
                for repeated_index, is_repeated in enumerate(self._determine_repeated_values(result['R'])):
                    if is_repeated:
                        previous_result = pairs[-1]
                        result['C'].insert(repeated_index, previous_result[repeated_index])

            pairs.append(result['C'])
        return pairs

    # PowerBI uses the key 'R' to represent repeated values.
    # The values to repeat are indexed by bits, starting with 1. These bits are sent as decimal.
    # So element 0 has a value of 1, element 1 has a value of 2, element 2 has a value of 4 and they keep doubling.
    # These values are then added together.
    # For example, 14 would mean that the repeated indexes 1, 2, and 3 (2nd, 3rd, and 4th elements) repeat.
    def _determine_repeated_values(self, r: int) -> List[int]:
        r_in_binary = reversed('{:b}'.format(r))
        return [ bool(int(one_or_zero)) for one_or_zero in r_in_binary ]

