from datetime import date, timedelta
import json
import logging
from types import TracebackType
from typing import Any, Dict, List, Union, Optional, Type
from websocket import create_connection  # type: ignore


logger = logging.getLogger(__name__)


class JsonRpcError(Exception):
    def __init__(self, code: int, message: str, **data: Dict):
        self.code = code
        self.message = message
        self.data = data
        reason = f'{message} (code {code})'
        if data:
            reason += f' -- {data}'

        super().__init__(reason)


class QlikClient:
    """
    Qlik (https://qlik.com/) exposes its main dashboard/client API over
    WebSockets with a JSON-RPC-based protocol (it's not *quite* standard, and
    includes `handle` and `delta` properties that are critically important but
    not part of JSON-RPC).

    This is a pretty thin wrapper around the basics of the API. We might want
    to extend it as we learn more about the detailed patterns in various Qlik
    objects or in the Counties' typical setups.

    Qlik Engine Docs: https://help.qlik.com/en-US/sense-developer/November2020/Subsystems/EngineAPI/Content/Sense_EngineAPI/introducing-engine-API.htm
                 And: https://help.qlik.com/en-US/sense-developer/November2020/APIs/EngineAPI/index.html
    JSON-RPC docs: https://www.jsonrpc.org/specification

    There are some existing Python Clients, but they all either don't seem well
    maintained or don't appear to cover the API aspects we focus on.

    Parameters
    ----------
    url : str
        The URL of the Qlik server, e.g.
        ``'wss://dashboard.cchealth.org/app/'``.
    document_id : str
        The ID of the document you want to read data from, e.g.
        ``'b7d7f869-fb91-4950-9262-0b89473ceed6'``.

    Examples
    --------
    Connect and get an object:
    >>> dashboard = QlikClient('wss://dashboard.cchealth.org/app/',
    >>>                        'b7d7f869-fb91-4950-9262-0b89473ceed6')
    >>> dashboard.open()
    >>> tests_chart = dashboard.get_data('bZFxmu')
    """
    def __init__(self, url: str, document_id: str, cookie: str = None):
        self.url = url + ('' if url.endswith('/') else '/')
        self.document_id = document_id
        self._message_id = 1
        self._document_handle = -1
        self._cookie = cookie

    def _connect(self) -> None:
        "Connect to the websocket server."
        socket_url = self.url + self.document_id
        self._socket = create_connection(socket_url, cookie=self._cookie)

    def _send(self, handle: Any, method: str, parameters: Union[List, Dict],
              delta: bool = False) -> Dict:
        "Send a JSON-RPC message and await the response."
        id_ = self._message_id
        self._message_id += 1

        message = {
            'jsonrpc': '2.0',
            'id': id_,
            # `handle` is non-standard, but required in Qlik's API.
            'handle': handle,
            'method': method,
            'params': parameters
        }
        # `delta` is also non-standard, and an optional part of the API.
        if delta:
            message['delta'] = True

        logger.debug('Sending: %s', message)
        self._socket.send(json.dumps(message))

        while True:
            # Keep reading the socket until we see our response.
            response = self._socket.recv()
            logger.debug('Received: %s', response)
            response_data = json.loads(response)
            if response_data.get('id') == id_:
                break

        if 'error' in response_data:
            raise JsonRpcError(**response_data['error'])
        elif 'result' in response_data:
            return response_data['result']
        elif 'method' in response_data:
            return {
                'method': response_data['method'],
                'params': response_data.get('params')
            }
        else:
            raise ValueError(f'Unexpected response: {response_data}')

    def open(self) -> None:
        "Open a connection to the Qlik server and get basic document info."
        self._connect()
        document = self._send(-1,
                              'OpenDoc',
                              [self.document_id, "", "", "", False])
        self._document_handle = document['qReturn']['qHandle']

    def close(self) -> None:
        self._socket.close()

    def get_app_layout(self) -> Dict:
        """
        Get layout information for application/document as a whole.
        """
        return self._send(self._document_handle, 'GetAppLayout', [])

    def get_object(self, object_id: str) -> Dict:
        """
        Get a handle for the object with a given ID. In most cases, you want to
        call ``get_data`` instead (it gets full details instead of a handle).

        Parameters
        ----------
        object_id : str
            The ID of the object to get a handle to, e.g. ``'bZFxmu'``.
        """
        return self._send(self._document_handle, 'GetObject', [object_id])

    def get_layout(self, handle: Any) -> Dict:
        """
        Get layout information for the object with a given handle. In most
        cases, you want to call ``get_data`` instead (it takes the object ID
        instead of a handle).

        Parameters
        ----------
        handle
            The API handle of the object to get.
        """
        return self._send(handle, 'GetLayout', [])

    def get_data(self, object_id: str) -> Dict:
        """
        Get detailed information for an object in the Qlik document. This
        usually includes layout/styling info, formatting info, and data (in the
        case of tables, charts, etc.).

        Parameters
        ----------
        object_id : str
            The ID of the object to get data for, e.g. ``'bZFxmu'``.
        """
        handle = self.get_object(object_id)['qReturn']['qHandle']
        return self.get_layout(handle)

    def get_field(self, field: str) -> Dict:
        return self._send(self._document_handle, 'GetField', [field])

    def select_field_value(self, field: str, value: str) -> Dict:
        handle = self.get_field(field)['qReturn']['qHandle']
        return self._send(handle, 'Select', [value])

    def __enter__(self) -> 'QlikClient':
        self.open()
        return self

    def __exit__(self,
                 _type: Optional[Type[BaseException]],
                 _value: Optional[BaseException],
                 _traceback: Optional[TracebackType]) -> None:
        self.close()

    @staticmethod
    def parse_date(value: int) -> date:
        """
        Parse a date from Qlik. Qlik uses MS Excel's date format
        (days since 1900-01-01 + 2).

        Parameters
        ----------
        value : int
            The Qlik/Excel-formatted date value to parse.
        """
        return date(1900, 1, 1) + timedelta(days=(value - 2))
