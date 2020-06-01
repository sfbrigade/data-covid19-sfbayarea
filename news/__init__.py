from typing import Dict, Type
from .alameda import AlamedaNews
from .base import NewsScraper
from .san_francisco import SanFranciscoNews
from .santa_clara import SantaClaraNews


scrapers: Dict[str, Type[NewsScraper]] = {
    'alameda': AlamedaNews,
    # 'contra_costa': None,
    # 'marin': None,
    # 'napa': None,
    'san_francisco': SanFranciscoNews,
    # 'san_mateo': None,
    'santa_clara': SantaClaraNews,
    # 'solano': None,
    # 'sonoma': None,
}
