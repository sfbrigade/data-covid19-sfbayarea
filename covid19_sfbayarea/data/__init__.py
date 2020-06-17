from typing import Dict, Any
from . import alameda
from . import san_francisco
import data_scrapers.sonoma_county as sonoma_county

scrapers: Dict[str, Any] = {
    'alameda': alameda,
    # 'contra_costa': None,
    # 'marin': None,
    # 'napa': None,
    'san_francisco': san_francisco
    # 'san_mateo': None,
    # 'santa_clara': None,
    # 'solano': None,
    'sonoma': sonoma_county,
}
