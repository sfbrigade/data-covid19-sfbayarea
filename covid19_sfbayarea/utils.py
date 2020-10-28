from functools import reduce
from typing import Any, Dict, List, Union

def friendly_county(county_id: str) -> str:
    '''
    Transform a county ID (e.g. "san_francisco") into a more human-friendly
    name (e.g. "San Francisco").
    '''
    return county_id.replace('_', ' ').title()

def dig(items: Union[Dict[Any, Any], List[Any]], json_path: List[Any]) -> Any:
    try:
        return reduce(lambda subitem, next_step: subitem[next_step], json_path, items)
    except (KeyError, TypeError, IndexError) as err:
        print('Error reading returned JSON, check path: ', err)
        raise(err)
