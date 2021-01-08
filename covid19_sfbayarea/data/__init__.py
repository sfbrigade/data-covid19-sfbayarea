from typing import Dict, Any
from . import alameda
from . import san_francisco
from . import marin
from . import sonoma
from . import solano
from . import san_mateo
from . import santa_clara

scrapers: Dict[str, Any] = {
    'alameda': alameda,
    # 'contra_costa': None,
    'marin': marin,
    # 'napa': None,
    'san_francisco': san_francisco,
    'san_mateo': san_mateo,
    'santa_clara': santa_clara,
    'sonoma': sonoma,
    'solano': solano,
}
