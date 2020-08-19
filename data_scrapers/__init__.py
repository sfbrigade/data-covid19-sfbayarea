from typing import Dict, Any
import data_scrapers.alameda_county as alameda_county
import data_scrapers.sonoma_county as sonoma_county

scrapers: Dict[str, Any] = {
    'alameda': alameda_county,
    # 'contra_costa': None,
    # 'marin': None,
    # 'napa': None,
    # 'san_francisco': san_francisco_county,
    # 'san_mateo': None,
    # 'santa_clara': None,
    # 'solano': None,
    'sonoma': sonoma_county,
}
