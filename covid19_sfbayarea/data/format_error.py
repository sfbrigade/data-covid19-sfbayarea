class FormatError(Exception):
    """
    A custom error to raise whenever a scraper runs into something in an
    unexpected format. This usually means that the website the scraper is
    accessing has changed
    """
    pass
