import requests

class BadRequest(requests.exceptions.HTTPError):
    """
    Represents a detailed error message from a web server.
    """

    def __str__(self):
        message = super().__str__()
        return f'{message} (status: {self.response.status_code})'
