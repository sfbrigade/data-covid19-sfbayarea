from typing import Dict, Type
from .alameda import AlamedaNews
from .base import NewsScraper
# from .contra_costa import ContraCostaNews
# from .marin import MarinNews
# from .napa import NapaNews
from .san_francisco import SanFranciscoNews
from .san_mateo import SanMateoNews
from .santa_clara import SantaClaraNews
# from .solano import SolanoNews
# from .sonoma import SonomaNews


scrapers: Dict[str, Type[NewsScraper]] = {
    'alameda': AlamedaNews,
    # 'contra_costa': ContraCostaNews,
    # 'marin': MarinNews,
    # 'napa': NapaNews,
    'san_francisco': SanFranciscoNews,
    'san_mateo': SanMateoNews,
    'santa_clara': SantaClaraNews,
    # 'solano': SolanoNews,
    # 'sonoma': SonomaNews,
}
