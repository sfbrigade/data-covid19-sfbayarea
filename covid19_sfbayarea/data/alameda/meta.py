import json
from typing import Any, Dict, List
from .power_bi_querier import PowerBiQuerier
from covid19_sfbayarea.utils import dig
from requests import get

class Meta():
    def get_data(self) -> str:
        url = ''.join([
            'https://wabi-us-gov-iowa-api.analysis.usgovcloudapi.net/public/reports/',
            PowerBiQuerier.powerbi_resource_key,
            '/modelsAndExploration?preferReadOnlySession=true'
        ])
        response = get(url, headers = { 'X-PowerBI-ResourceKey': PowerBiQuerier.powerbi_resource_key })
        return self._extract_meta(response.json())[2:] # First two characters are ': '

    def _extract_meta(self, response_json: Dict[str, Any]) -> str:
        visual_containers = dig(response_json, ['exploration', 'sections', 0, 'visualContainers'])
        text_boxes = self._extract_text_runs(visual_containers)
        return max(text_boxes, key=len)

    def _extract_text_runs(self, containers: List[Any]) -> List[str]:
        configs_with_text = [json.loads(container['config']) for container in containers if 'textRuns' in container['config']]
        paragraphs = self._extract_paragraphs(configs_with_text)
        return [text_run['value'] for paragraph in paragraphs for text_run in paragraph['textRuns']]

    def _extract_paragraphs(self, configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        json_path = ['singleVisual', 'objects', 'general', 0, 'properties', 'paragraphs']
        return [paragraph for config in configs for paragraph in dig(config, json_path)]
