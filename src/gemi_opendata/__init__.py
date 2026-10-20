"""Python client for the Greek GEMI Open Data API."""

from .client import GemiClient
from .exceptions import GemiAPIError

__all__ = ["GemiAPIError", "GemiClient"]

