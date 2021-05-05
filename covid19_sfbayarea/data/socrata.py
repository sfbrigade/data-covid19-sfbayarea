from functools import lru_cache
from typing import Any, Dict, List
import requests
from urllib.parse import urljoin
from cachecontrol import CacheControl  # type: ignore
from ..errors import BadRequest


class SocrataApi:
    """
    Class for starting a session for requests via Socrata APIs.
    Initialize with a base_url
    """
    # SODA API has a default limit of 1000 records per call,
    # so we'll use that as well.
    # See: https://dev.socrata.com/docs/paging.html
    DEFAULT_LIMIT = 1000

    def __init__(self, base_url: str):
        self.session = CacheControl(requests.Session())
        self.base_url = base_url
        self.resource_url = urljoin(self.base_url, '/resource/')
        self.metadata_url = urljoin(self.base_url, '/api/views/metadata/v1/')

    @lru_cache(maxsize=32)
    def _request(self, url: str, **kwargs: Any) -> Dict:
        try:
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as http_err:

            try:
                # see if the API returned message data
                server_message = response.json()['message']

            except Exception:
                # if no JSON data, re-rasie the original error
                raise http_err

            raise BadRequest(server_message, response=response)

    def request(self, url: str, params: Dict = None, **kwargs: Any) -> Dict:
        # Arguments to _request() must be hashable (so they can be cached).
        # If a params dict is sent, convert it to a tuple.
        if params:
            kwargs['params'] = tuple(params.items())

        return self._request(url, **kwargs)

    def resource(
            self, resource_id: str, params: Dict = None, **kwargs: Any
    ) -> List[Dict]:
        """Fetch and return data from a given Socrata data resource"""
        data: List[Dict] = []

        params = params or {}
        params.setdefault("$offset", 0)
        limit = params.setdefault("$limit", self.DEFAULT_LIMIT)

        while True:
            results = self.request(
                f'{self.resource_url}{resource_id}', params=params, **kwargs
            )
            result_count = len(results)

            if result_count == limit:
                data.extend(results)
                offset = params["$offset"] + limit
                params.update({"$offset": offset})
                continue

            elif result_count > 0 and result_count < limit:
                data.extend(results)
                break

            else:
                break

        return data

    def metadata(self, resource_id: str, **kwargs: Any) -> Dict:
        return self.request(f'{self.metadata_url}{resource_id}.json', **kwargs)
