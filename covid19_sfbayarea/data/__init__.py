from typing import Dict, Any
from . import alameda
from . import san_francisco
from . import marin
from . import sonoma
from . import solano

scrapers: Dict[str, Any] = {
    'alameda': alameda,
    # 'contra_costa': None,
    'marin': marin,
    # 'napa': None,
    'san_francisco': san_francisco,
    # 'san_mateo': None,
    # 'santa_clara': None,
    'sonoma': sonoma,
    'solano': solano,
}
