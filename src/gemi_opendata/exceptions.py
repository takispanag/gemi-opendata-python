"""Exceptions raised by the GEMI API client."""


class GemiAPIError(Exception):
    """An HTTP error response returned by the GEMI API."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"GEMI API returned HTTP {status_code}: {message}")

