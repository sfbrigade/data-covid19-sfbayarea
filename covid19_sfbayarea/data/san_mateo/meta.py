import json
from typing import Any, Dict, List
from .power_bi_querier import PowerBiQuerier
from covid19_sfbayarea.utils import dig
from requests import get

class Meta():
    def get_data(self) -> str:
        try:
            url = ''.join([
                'https://wabi-us-gov-iowa-api.analysis.usgovcloudapi.net/public/reports/',
                PowerBiQuerier.powerbi_resource_key,
                '/modelsAndExploration?preferReadOnlySession=true'
            ])
            response = get(url, headers = { 'X-PowerBI-ResourceKey': PowerBiQuerier.powerbi_resource_key })
            return self._extract_meta(response.json())
        except:
            return """
            Because of limited testing capacity, the number of cases detected
            through testing represents only a small portion of the total number
            of likely cases in the County. COVID-19 data are reported as timely,
            accurately, and completely as we have available. Data are updated as
            we receive information that is more complete and will change over
            time as we learn more. Cases are lab-confirmed COVID-19 cases
            reported to San Mateo County Public Health by providers, commercial
            laboratories, and academic laboratories, including reporting results
            through the California Reportable Disease Information Exchange. A
            lab-confirmed case is defined as detection of SARS-CoV-2 RNA in a
            clinical specimen using a molecular amplification detection test.
            Cases are counted by date the lab result was reported.  Deaths
            reported in this dashboard include only San Mateo County residents.
            """

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
