def friendly_county(county_id: str) -> str:
    '''
    Transform a county ID (e.g. "san_francisco") into a more human-friendly
    name (e.g. "San Francisco").
    '''
    return county_id.replace('_', ' ').title()
