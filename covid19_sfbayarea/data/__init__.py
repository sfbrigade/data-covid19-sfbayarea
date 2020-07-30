from typing import Dict, Any
from . import alameda
from . import san_francisco
<<<<<<< HEAD
from . import sonoma
=======
from . import solano
>>>>>>> 5ba6dbb55c75455b154e42832651e6a3837fc805

scrapers: Dict[str, Any] = {
    'alameda': alameda,
    # 'contra_costa': None,
    # 'marin': None,
    # 'napa': None,
    'san_francisco': san_francisco,
    # 'san_mateo': None,
    # 'santa_clara': None,
<<<<<<< HEAD
    # 'solano': None,
    'sonoma': sonoma,
=======
    'solano': solano,
    # 'sonoma': None,
>>>>>>> 5ba6dbb55c75455b154e42832651e6a3837fc805
}
