from typing import Dict, Any
from . import alameda
from . import san_francisco

scrapers: Dict[str, Any] = {
    'alameda': alameda,
    # 'contra_costa': None,
    'marin': marin_scraper,
    # 'napa': None,
    'san_francisco': san_francisco
    # 'san_mateo': None,
    # 'santa_clara': None,
    # 'solano': None,
    # 'sonoma': None,
}
