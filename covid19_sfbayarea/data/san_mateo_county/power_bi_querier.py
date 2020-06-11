import json
from functools import reduce
from requests import post

class PowerBiQuerier:
    BASE_URI = 'https://wabi-us-gov-iowa-api.analysis.usgovcloudapi.net/public/reports/querydata?synchronous=true'
    MODEL_ID = 275725
    POWERBI_RESOURCE_KEY = '86dc380f-4914-4cff-b2a5-03af9f292bbd'
    def __init__(self) -> None:
        self.source = 'c1'
        self.name = 'cases_by_age'
        self.property = 'age_cat'

    def get_data(self) -> None:
        response_json = self._fetch_data()
        return self._parse_data(response_json)

    def _fetch_data(self) -> None:
        response = post(
            self.BASE_URI,
            headers = { 'X-PowerBI-ResourceKey': self.POWERBI_RESOURCE_KEY },
            json = self._query_params()
        )
        response.raise_for_status()
        return response.json()

    def _parse_data(self, response_json) -> None:
        results = self._dig(self.path, response_json)
        data_pairs = [ result['C'] for result in results[1:-1]]
        return { 'group': group, 'count': count for group, count in data_pairs }


    def _dig(self, path, item) -> None:
        try:
            return reduce(lambda subitem, next_step: subitem[next_step], path, item)
        except (KeyError, TypeError, IndexError) as err:
            print('Error reading returned JSON, check path: ', err)
            raise(err)

    def _query_params(self) -> None:
        return {
            'version': '1.0.0',
            'queries': [self._query()],
            'cancelQueries': [],
            'modelId': self.MODEL_ID
        }

    def _query(self) -> None:
        return {
            'Query': { 'Commands': [self._command()] },
            'CacheKey': json.dumps({ 'Commands': [self._command()] }),
            'QueryId': '',
            'ApplicationContext': {
                'DatasetId':'aa4631ab-2f78-40f6-b4c4-d2f5f8a89bcc',
                'Sources': [{ 'ReportId': 'baf74baa-bdc9-4c71-995a-b996f1d0b7e9' }]
            }
        }

    def _command(self) -> None:
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

    def _select(self) -> None:
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

    def _order_by(self) -> None:
        return [
            {
                'Direction': 1,
                'Expression': { 'Column': self._column_expression(self.property) }
            }
        ]

    def _column_expression(self, property) -> None:
        return {
            'Expression': { 'SourceRef': { 'Source': self.source } },
            'Property': property
        }

    def _binding(self) -> None:
        return {
            'Primary': { 'Groupings': [{ 'Projections': [0, 1] }] },
            'DataReduction': {
                'DataVolume': 4,
                'Primary': { 'Window': { 'Count': 1000 } }
            },
            'Version': 1
        }

pbq = PowerBiQuerier()
import pdb
pdb.set_trace()
print(pbq.fetch_data())
