import json
from typing import Any, Dict, List
from .power_bi_querier import PowerBiQuerier
from .utils import dig
from requests import get

class Meta():
    def get_data(self) -> str:
        try:
            url = ''.join([
                'https://wabi-us-gov-iowa-api.analysis.usgovcloudapi.net/public/reports/',
                PowerBiQuerier.DEFAULT_POWERBI_RESOURCE_KEY,
                '/modelsAndExploration?preferReadOnlySession=true'
            ])
            response = get(url, headers = { 'X-PowerBI-ResourceKey': PowerBiQuerier.DEFAULT_POWERBI_RESOURCE_KEY })
            return self._extract_meta(response.json())[2:] # First two characters are ': '
        except:
            return """
            The City of Berkeley and Alameda County (minus Berkeley) are separate local health jurisdictions (LHJs).
            We are showing data for each separately and together. The numbers for the Alameda County LHJ and the
            Berkeley LHJ come from the state’s communicable disease tracking database, CalREDIE. These data are updated
            daily, with cases sometimes reassigned to other LHJs and sometimes changed from a suspected to a confirmed
            case, so counts for a particular date in the past may change as information is updated in CalREDIE. Case
            dates reflect the date created in CalREDIE. The time lag between the date of death and the date of entry
            into CalREDIE has sometimes been one week; the date of death is what is reflected here, and so death counts
            for a particular date in the past may change as information is updated in CalREDIE. Furthermore, we review
            our data routinely and adjust to ensure its integrity and that it most accurately represents the full
            picture of COVID-19 cases in our county. Berkeley LHJ cases do not include two cases that were passengers of
            the Diamond Princess cruise.
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
