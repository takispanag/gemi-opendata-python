"""Exceptions raised by the GEMI API client."""


class GemiError(Exception):
    """Base class for SDK runtime failures (local validation uses ValueError)."""


class GemiAPIError(GemiError):
    """An unsuccessful HTTP response, with safe structured API error details."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        errors: tuple[dict[str, str], ...] = (),
        retry_after: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.errors = errors
        self.retry_after = retry_after
        super().__init__(f"GEMI API returned HTTP {status_code}: {message}")


class GemiBadRequestError(GemiAPIError):
    """The service rejected a request (HTTP 400)."""


class GemiAuthenticationError(GemiAPIError):
    """The service rejected authentication or authorization (HTTP 401/403)."""


class GemiNotFoundError(GemiAPIError):
    """The service found no matching resource (HTTP 404)."""


class GemiRateLimitError(GemiAPIError):
    """The service rate-limited the request (HTTP 429)."""


class GemiServiceError(GemiAPIError):
    """The service returned a server error (HTTP 5xx)."""


class GemiTransportError(GemiError):
    """An HTTP request failed before a usable response was received."""


class GemiTimeoutError(GemiTransportError):
    """The configured HTTP timeout was exceeded."""


class GemiResponseError(GemiError):
    """A successful JSON endpoint returned undecodable JSON."""
