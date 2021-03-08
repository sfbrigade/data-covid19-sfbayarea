from typing import Dict, Any
from . import alameda
from . import contra_costa
from . import marin
from . import napa
from . import san_francisco
from . import san_mateo
from . import santa_clara
from . import solano
from . import sonoma

scrapers: Dict[str, Any] = {
    'alameda': alameda,
    'contra_costa': contra_costa,
    'marin': marin,
    'napa': napa,
    'san_francisco': san_francisco,
    'san_mateo': san_mateo,
    'santa_clara': santa_clara,
    'sonoma': sonoma,
    'solano': solano,
}
