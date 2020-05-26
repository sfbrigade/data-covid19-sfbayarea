from typing import Dict, Any
import data_scrapers.alameda as alameda
import data_scrapers.san_francisco as san_francisco

scrapers: Dict[str, Any] = {
    'alameda': alameda,
    # 'contra_costa': None,
    # 'marin': None,
    # 'napa': None,
    'san_francisco': san_francisco
    # 'san_mateo': None,
    # 'santa_clara': None,
    # 'solano': None,
    # 'sonoma': None,
}
