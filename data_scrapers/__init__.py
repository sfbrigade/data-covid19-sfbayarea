<<<<<<< HEAD
from typing import Dict 
import data_scrapers.alameda_county as alameda_county

scrapers: Dict = {
    'alameda': alameda_county
=======
from typing import Dict, Type
import data_scrapers.alameda_county
import data_scrapers.san_francisco_county

scrapers: Dict = {
    'alameda': alameda_county,
>>>>>>> Add CLI to run data scrapers
    # 'contra_costa': None,
    # 'marin': None,
    # 'napa': None,
    # 'san_francisco': san_francisco_county,
    # 'san_mateo': None,
    # 'santa_clara': None,
    # 'solano': None,
    # 'sonoma': None,
}
