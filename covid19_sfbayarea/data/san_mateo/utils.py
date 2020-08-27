from functools import reduce
from typing import Any, Dict, List

def map_ethnicity_to_data_model(ethnicity: str) -> str:
    ethnicity_without_whitespace = ethnicity.strip()
    mapping = {
        'American Indian/Alaska Native': 'Native_Amer',
        'Asian': 'Asian',
        'Latino/Hispanic': 'Latinx_or_Hispanic',
        'Black': 'African_Amer',
        'Multirace': 'Multiple_Race',
        'Other': 'Other',
        'Pacific Islander': 'Pacific_Islander',
        'White': 'White',
        'Unknown': 'Unknown'
    }
    return mapping.get(ethnicity_without_whitespace, ethnicity_without_whitespace)

def dig(items: Dict[str, Any], json_path: List[Any]) -> Any:
    try:
        return reduce(lambda subitem, next_step: subitem[next_step], json_path, items)
    except (KeyError, TypeError, IndexError) as err:
        print('Error reading returned JSON, check path: ', err)
        raise(err)
