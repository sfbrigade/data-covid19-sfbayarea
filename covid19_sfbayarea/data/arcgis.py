import requests
from typing import Any, Dict, Generator
from urllib.parse import urljoin
from ..errors import BadRequest


class ArcGisFeatureServer:
    """
    A thin wrapper around ArcGIS's FeatureServer API. The capabilities are
    pretty limited, but it gives us a useful wrapper for the data-focused parts
    of the API that we need.

    Parameters
    ----------
    base_url : str
        The base URL of the server, including the "Unique Service ID". Example:
        ``'https://services1.arcgis.com/Ko5rxt00spOfjMqj'``
    """
    def __init__(self, base_url: str):
        if not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url
        self.service_base_url = urljoin(base_url, 'ArcGIS/rest/services/')

    def _build_query_url(self, service: str, table_id: int) -> str:
        query_path = f'{service}/FeatureServer/{table_id}/query'
        return urljoin(self.service_base_url, query_path)

    def query(
        self,
        service: str,
        table_id: int = 0,
        *,  # Parameters below must be specified as keywords. -----------------
        where: str = '1=1',
        outFields: str = None,
        groupByFieldsForStatistics: str = None,
        orderByFields: str = None,
        **params: Any
     ) -> Generator[Dict, None, None]:
        """
        Query a table/layer from an ArcGIS Feature Service. This will yield
        the ``attributes`` field of each result record.

        ArcGIS queries normally require a ``where`` clause, but this method
        provides a default ``where`` that selects all rows to simplify some
        queries.

        The parameters of this method don't follow typical python convention
        because they correspond directly to ArcGIS ``query`` API parameters.
        Only a subset of commonly used parameters are explicitly listed here
        for code completion support. For a full reference, see:
            https://developers.arcgis.com/rest/services-reference/query-feature-service-layer-.htm

        Parameters
        ----------
        service : str
            The name of the service to query, e.g. ``'CaseDataDemographics'``.
        table_id : int
            The table/layer ID to query from the service. These IDs are usually
            sequential and start from 0.
        where : str
        outFields : str
        groupByFieldsForStatistics : str
        orderByFields : str
        **params
            Additional query parameters accepted by the ArcGIS API. Reference:
            - https://developers.arcgis.com/rest/services-reference/query-feature-service-layer-.htm
            - https://developers.arcgis.com/documentation/mapping-apis-and-location-services/data-hosting/services/feature-service/

        Yields
        ------
        dict
            This yields the ``attributes`` field of each resulting feature.
            (Features are GeoJSON, but since we don't care about the geometry,
            we skip over it and just yield the data.)
        """
        url = self._build_query_url(service, table_id)
        next_params = params.copy()
        next_params.update({
            'f': 'json',
            'returnGeometry': False,
            'where': where,
            'outFields': outFields,
            'groupByFieldsForStatistics': groupByFieldsForStatistics,
            'orderByFields': orderByFields
        })

        while True:
            response = requests.get(url, params=next_params)
            data = response.json()
            if 'error' in data:
                message = data['error']['message']
                if 'details' in data['error']:
                    details = ' '.join(data['error']['details'])
                    message = f'{message} ({details})'
                raise BadRequest(message, response=response)

            for feature in data['features']:
                yield feature['attributes']

            if not data.get('exceededTransferLimit', False):
                return

            offset = next_params.get('resultOffset', 0) + len(data['features'])
            next_params['resultOffset'] = offset
