from .alameda import AlamedaNews
from .san_francisco import SanFranciscoNews


scrapers = {
    'alameda': AlamedaNews,
    # 'contra_costa': None,
    # 'marin': None,
    # 'napa': None,
    'san_francisco': SanFranciscoNews,
    # 'san_mateo': None,
    # 'santa_clara': None,
    # 'solano': None,
    # 'sonoma': None,
}
