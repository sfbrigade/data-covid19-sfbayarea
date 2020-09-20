def friendly_county(county_id: str) -> str:
    '''
    Transform a county ID (e.g. "san_francisco") into a more human-friendly
    name (e.g. "San Francisco").
    '''
    return county_id.replace('_', ' ').title()


def cli_friendly_county(county_name: str) -> str:
    '''
    Transform a human-friendly county name into a command-line friendly string;
    the reverse of `friendly_county()` (e.g. 'San Francisco' -> 'san_francisco')
    '''
    return county_name.replace(" ", "_").lower()
