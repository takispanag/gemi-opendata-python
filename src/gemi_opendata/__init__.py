"""Python client for the Greek GEMI Open Data API."""

from .client import GemiClient
from .exceptions import (
    GemiAPIError,
    GemiAuthenticationError,
    GemiBadRequestError,
    GemiError,
    GemiNotFoundError,
    GemiRateLimitError,
    GemiResponseError,
    GemiServiceError,
    GemiTimeoutError,
    GemiTransportError,
)

__all__ = [
    "GemiAPIError",
    "GemiAuthenticationError",
    "GemiBadRequestError",
    "GemiClient",
    "GemiError",
    "GemiNotFoundError",
    "GemiRateLimitError",
    "GemiResponseError",
    "GemiServiceError",
    "GemiTimeoutError",
    "GemiTransportError",
]
