import json
from functools import reduce
from typing import Any, Dict, List
from .power_bi_querier import PowerBiQuerier
from requests import get

class Meta():
    def get_data(self) -> str:
        url = ''.join([
            'https://wabi-us-gov-iowa-api.analysis.usgovcloudapi.net/public/reports/',
            PowerBiQuerier.DEFAULT_POWERBI_RESOURCE_KEY,
            '/modelsAndExploration?preferReadOnlySession=true'
        ])
        response = get(url, headers = { 'X-PowerBI-ResourceKey': PowerBiQuerier.DEFAULT_POWERBI_RESOURCE_KEY })
        return self._extract_meta(response.json())

    def _extract_meta(self, response_json: Dict[str, Any]) -> str:
        visual_containers = self._dig(response_json, ['exploration', 'sections', 0, 'visualContainers'])
        text_boxes = self._extract_text_runs(visual_containers)
        return max(text_boxes, key=len)

    def _extract_text_runs(self, containers: List[Any]) -> List[str]:
        configs_with_text = [json.loads(container['config']) for container in containers if 'textRuns' in container['config']]
        paragraphs = self._extract_paragraphs(configs_with_text)
        return [text_run['value'] for paragraph in paragraphs for text_run in paragraph['textRuns']]

    def _extract_paragraphs(self, configs: List[List[Dict]]):
        json_path = ['singleVisual', 'objects', 'general', 0, 'properties', 'paragraphs']
        return [paragraph for config in configs for paragraph in self._dig(config, json_path)]

    def _dig(self, results: Dict[str, List], json_path: List[Any]) -> List[Dict[str, int]]:
        try:
            return reduce(lambda subitem, next_step: subitem[next_step], json_path, results) # type: ignore
        except (KeyError, TypeError, IndexError) as err:
            print('Error reading returned JSON, check path: ', err)
            raise(err)
