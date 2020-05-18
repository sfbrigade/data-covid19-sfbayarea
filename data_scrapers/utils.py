from pathlib import Path
import json
from typing import Dict
import requests
from urllib.parse import urljoin

def get_data_model() -> Dict:
    """ Return a dictionary representation of the data model """
    template_path = Path(__file__).parent.parent / 'data_models/data_model.json'
    with template_path.open() as template:
        out = json.load(template)
    return out

class SocrataApi:
    """ Class for starting a Session with Socrata endpoints and sending requests"""
    def __init__(self, base_url):
        self.session = requests.Session()
        self.base_url = base_url
        self.resource_url = urljoin(self.base_url, '/resource/')
        self.metadata_url = urljoin(self.base_url, '/api/views/metadata/v1/')

    def request(self, url, **kwargs):
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response.json()
