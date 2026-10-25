"""Synchronous client for the documented GEMI Open Data API."""

from __future__ import annotations

import math
import os
from collections.abc import Sequence
from typing import Any

import httpx

from .exceptions import (
    GemiAPIError,
    GemiAuthenticationError,
    GemiBadRequestError,
    GemiNotFoundError,
    GemiRateLimitError,
    GemiResponseError,
    GemiServiceError,
    GemiTimeoutError,
    GemiTransportError,
)

_BASE_URL = "https://opendata-api.businessportal.gr/api/opendata/v1"
_METADATA_PATHS = {
    "activities": "activities",
    "prefectures": "prefectures",
    "municipalities": "municipalities",
    "company_statuses": "companyStatuses",
    "legal_types": "legalTypes",
    "gemi_offices": "gemiOffices",
    "assembly_subjects": "assemblySubjects",
}


class GemiClient:
    """Call GEMI's search, company, document, and metadata endpoints."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = _BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        key = os.getenv("GEMI_OPENDATA_API_KEY") if api_key is None else api_key
        if not isinstance(key, str) or not key.strip():
            raise ValueError(
                "Pass api_key or set the GEMI_OPENDATA_API_KEY environment variable."
            )
        key = key.strip()
        if any(ord(char) < 32 or ord(char) == 127 for char in key):
            raise ValueError("The API key must not contain control characters.")
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            raise ValueError("timeout must be a finite positive number of seconds.")
        try:
            url = httpx.URL(base_url)
        except (httpx.InvalidURL, TypeError) as exc:
            raise ValueError("base_url must be an absolute HTTP(S) URL.") from exc
        if (
            url.scheme not in {"http", "https"}
            or not url.host
            or url.username
            or url.password
            or url.query
            or url.fragment
        ):
            raise ValueError(
                "base_url must be an HTTP(S) URL without credentials, query, or fragment."
            )
        self._api_key = key
        self._client = httpx.Client(
            base_url=str(url).rstrip("/"),
            headers={"api_key": key, "Accept": "application/json"},
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> GemiClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _request(
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        try:
            response = self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise GemiTimeoutError("The GEMI request timed out.") from exc
        except httpx.RequestError as exc:
            raise GemiTransportError(
                "The GEMI request could not be completed."
            ) from exc
        if not response.is_success:
            error_type = {
                400: GemiBadRequestError,
                401: GemiAuthenticationError,
                403: GemiAuthenticationError,
                404: GemiNotFoundError,
                429: GemiRateLimitError,
            }.get(response.status_code, GemiAPIError)
            if response.status_code >= 500:
                error_type = GemiServiceError
            errors = self._error_details(response)
            message = "; ".join(
                item["message"] for item in errors if item.get("message")
            )
            raise error_type(
                response.status_code,
                message
                or httpx.codes.get_reason_phrase(response.status_code)
                or "Unsuccessful response",
                errors=errors,
                retry_after=response.headers.get("Retry-After"),
            )
        return response

    def _error_details(self, response: httpx.Response) -> tuple[dict[str, str], ...]:
        try:
            payload = response.json()
        except (ValueError, UnicodeDecodeError):
            return ()
        if not isinstance(payload, list):
            return ()
        return tuple(
            {
                field: item[field].replace(self._api_key, "[REDACTED]")
                for field in ("code", "message")
                if isinstance(item.get(field), str)
            }
            for item in payload
            if isinstance(item, dict)
        )

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        response = self._request(path, params=params)
        try:
            return response.json()
        except (ValueError, UnicodeDecodeError) as exc:
            raise GemiResponseError("The GEMI endpoint returned invalid JSON.") from exc

    @staticmethod
    def _query_params(criteria: dict[str, Any]) -> dict[str, Any]:
        """Encode sequence-valued search filters in the API's CSV format."""
        params = {}
        for key, value in criteria.items():
            if not key.strip():
                raise ValueError("Search parameter names must not be empty.")
            if value is None:
                continue
            if isinstance(value, str):
                if value.strip():
                    params[key] = value.strip()
            elif type(value) is int:
                params[key] = value
            elif isinstance(value, Sequence) and not isinstance(
                value, (bytes, bytearray, memoryview)
            ):
                items = []
                for item in value:
                    if type(item) is int:
                        items.append(str(item))
                    elif isinstance(item, str) and item.strip() and "," not in item:
                        items.append(item.strip())
                    else:
                        raise ValueError(
                            f"{key} must contain nonempty strings or integers."
                        )
                if items:
                    params[key] = ",".join(items)
            else:
                raise ValueError(
                    f"{key} must be a string, integer, or sequence of them."
                )
        return params

    def search_companies(self, **criteria: Any) -> Any:
        """Search companies; provide one or more API search criteria."""
        size = criteria.get("resultsSize")
        if size is not None and (type(size) is not int or not 1 <= size <= 200):
            raise ValueError("resultsSize must be an integer between 1 and 200.")
        params = self._query_params(criteria)
        if not params.keys() - {"resultsSize"}:
            raise ValueError("At least one GEMI search criterion is required.")
        return self._get("/companies", params=params)

    @staticmethod
    def _identifier(value: int | str, name: str) -> str:
        text = str(value)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, str))
            or not text.isascii()
            or not text.isdecimal()
            or int(text) <= 0
        ):
            raise ValueError(
                f"{name} must be a positive integer or decimal digit string."
            )
        return text

    def get_company(self, ar_gemi: int | str) -> Any:
        """Get the public registry record for a GEMI number."""
        identifier = self._identifier(ar_gemi, "ar_gemi")
        return self._get(f"/companies/{identifier}")

    def get_company_documents(self, ar_gemi: int | str) -> Any:
        """Get public documents associated with a GEMI number."""
        identifier = self._identifier(ar_gemi, "ar_gemi")
        return self._get(f"/companies/{identifier}/documents")

    def download_file(self, *, key: str, element_id: int | str) -> bytes:
        """Download an API attachment using its key and element ID."""
        if not isinstance(key, str) or not key.strip():
            raise ValueError("key must be a nonempty document key.")
        identifier = self._identifier(element_id, "element_id")
        return self._request(
            "/downloadFile",
            params={"key": key.strip(), "elementId": identifier},
        ).content

    def health(self) -> bool:
        """Return True for a successful HTTP status; raise on failure."""
        self._request("/health")
        return True

    def _metadata(self, resource: str) -> Any:
        return self._get(f"/metadata/{_METADATA_PATHS[resource]}")

    def list_activities(self) -> Any:
        """List GEMI activity codes (ΚΑΔ)."""
        return self._metadata("activities")

    def list_prefectures(self) -> Any:
        """List prefectures."""
        return self._metadata("prefectures")

    def list_municipalities(self) -> Any:
        """List municipalities."""
        return self._metadata("municipalities")

    def list_company_statuses(self) -> Any:
        """List GEMI company statuses."""
        return self._metadata("company_statuses")

    def list_legal_types(self) -> Any:
        """List legal entity types."""
        return self._metadata("legal_types")

    def list_gemi_offices(self) -> Any:
        """List local GEMI offices."""
        return self._metadata("gemi_offices")

    def list_assembly_subjects(self) -> Any:
        """List company assembly decision subjects."""
        return self._metadata("assembly_subjects")
