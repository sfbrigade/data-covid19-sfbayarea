from cachecontrol import CacheControl  # type: ignore
import json
import logging
import requests
from typing import Dict, Any, Generator, Optional
from urllib.parse import urljoin
from .errors import BadRequest


logger = logging.getLogger(__name__)


class Ckan:
    """
    Handle access to datasets in a CKAN repository.
    """
    def __init__(self, base_url: str):
        self.session = CacheControl(requests.Session())
        self.base_url = base_url
        self.search_url = urljoin(self.base_url, '/api/3/action/datastore_search')
        self.metadata_url = urljoin(self.base_url, '/api/3/action/resource_show')

    def data(self, resource_id: str, yield_meta: bool = False, **params: Any) -> Generator[Dict, None, None]:
        """
        Yield each record from a dataset.

        Parameters
        ----------
        resource_id : str
            The ID of the resource to get data from.
        yield_meta : bool
            If true, yield metadata from the dataset (e.g. field names and
            types) as the first item.
        params
            Any other data search arguments. For a full reference, see:
            https://docs.ckan.org/en/2.7/maintaining/datastore.html#ckanext.datastore.logic.action.datastore_search
        """
        params['resource_id'] = resource_id
        if isinstance(params.get('q'), dict):
            params['filters'] = json.dumps(params['filters'])
        if isinstance(params.get('filters'), dict):
            params['filters'] = json.dumps(params['filters'])

        next_url = self.search_url
        next_params: Optional[Dict] = params

        # Keep looping as long as there is a next page of results
        count = 0
        while True:
            data = self.request(next_url, params=next_params)
            records = data['records']
            if yield_meta and count == 0:
                meta = {key: value
                        for key, value in data.items()
                        if key != 'records'}
                yield meta

            if len(records) == 0:
                return

            total = data['total']
            count += len(records)
            logger.info(f'Loaded {count} results out of {total} ...')

            for record in data['records']:
                yield record

            next_url = data.get('_links', {}).get('next')
            next_url = urljoin(self.base_url, next_url)
            next_params = None

    def metadata(self, resource_id: str, **params: Any) -> Dict:
        """
        Get metadata about a dataset.
        """
        params['id'] = resource_id
        return self.request(self.metadata_url, params=params)

    def request(self, url: str, **kwargs: Any) -> Dict:
        response = self.session.get(url, **kwargs)
        data = response.json()
        if not data['success']:
            if 'error' not in data:
                message = response.text
            elif 'message' not in data['error']:
                message = str(data['error'])
            else:
                message = str(data['error']['message'])
            raise BadRequest(f'CKAN API Error: {message}', response=response)

        return data['result']
