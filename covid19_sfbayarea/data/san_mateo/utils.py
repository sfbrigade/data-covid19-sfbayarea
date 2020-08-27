from functools import reduce
from typing import Any, Dict, List

def dig(items: Dict[str, Any], json_path: List[Any]) -> Any:
    try:
        return reduce(lambda subitem, next_step: subitem[next_step], json_path, items)
    except (KeyError, TypeError, IndexError) as err:
        print('Error reading returned JSON, check path: ', err)
        raise(err)
