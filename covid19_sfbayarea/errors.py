import requests


class FormatError(Exception):
    """
    A custom error to raise whenever a scraper runs into something in an
    unexpected format. This usually means that the website the scraper is
    accessing has changed.
    """
    pass


class PowerBiQueryError(ValueError):
    """
    Represents an error returned by PowerBI in response to a query.
    """
    ...


class BadRequest(requests.exceptions.HTTPError):
    """
    Represents a detailed error message from a web server.
    """
    def __str__(self) -> str:
        message = super().__str__()
        return f'{message} (status: {self.response.status_code})'
