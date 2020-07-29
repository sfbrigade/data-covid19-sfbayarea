import json
from typing import Any, Dict, List
from .power_bi_querier import PowerBiQuerier
from requests import get

class Meta(PowerBiQuerier):
    def get_data(self) -> None:
        fetched_meta = self._fetch_meta()

    def _fetch_meta(self) -> Dict[Any]:
        url = ''.join(
            'https://wabi-us-gov-iowa-api.analysis.usgovcloudapi.net/public/reports/',
            self.DEFAULT_POWERBI_RESOURCE_KEY,
            '/modelsAndExploration?preferReadOnlySession=true'
        )
        response = get(url, headers = { 'X-PowerBI-ResourceKey': self.DEFAULT_POWERBI_RESOURCE_KEY })
        return response.json()

    def _extract_meta(self, response_json: Dict[Any]) -> None:
        visual_containers = self._dig(response_json, ['exploration', 'sections', 0, 'visualContainers'])
        visual_container_with_meta = _find_visual_container_with_meta(visual_containers)
        serialized_config = visual_containers[8]['config']
        config = json.loads(serialized_config)
        return config['singleVisual']['objects']['general'][0]['properties']['paragraphs'][0]['textRuns'][0]['value']

    def _find_meta_from_visual_containers(self, visual_containers: List[Dict]) -> str:
        configs = [json.loads(visual_container['config']) for visual_container in visual_containers]
        objects = [config['singleVisual']['objects'] for config in configs]
        objects_with_general_key = [object for object in objects if 'general' in object.keys()]
        properties = [object['properties'] for objects in objects_with_general_key for object in objects['general']]
        filter()

    def _dig(self, results: Dict[str, List], json_path: List[Any]) -> List[Dict[str, int]]:
        try:
            return reduce(lambda subitem, next_step: subitem[next_step], json_path, results) # type: ignore
        except (KeyError, TypeError, IndexError) as err:
            print('Error reading returned JSON, check path: ', err)
            raise(err)
