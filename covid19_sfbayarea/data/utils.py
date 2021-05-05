import json
from pathlib import Path
from typing import Dict


def get_data_model() -> Dict:
    """ Return a dictionary representation of the data model """
    root = Path(__file__).parent.parent.parent
    template_path = root / 'data_models/data_model.json'
    with template_path.open() as template:
        out = json.load(template)
    return out
