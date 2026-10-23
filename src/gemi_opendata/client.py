"""Synchronous client for the documented GEMI Open Data API."""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Any

import httpx

from .exceptions import GemiAPIError


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
        key = api_key or os.getenv("GEMI_OPENDATA_API_KEY")
        if not key:
            raise ValueError(
                "Pass api_key or set the GEMI_OPENDATA_API_KEY environment variable."
            )
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
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

    def _get(
        self, path: str, *, params: dict[str, Any] | None = None, binary: bool = False
    ) -> Any:
        try:
            response = self._client.get(path, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GemiAPIError(
                exc.response.status_code, exc.response.text[:500]
            ) from exc
        return response.content if binary else response.json()

    @staticmethod
    def _query_params(criteria: dict[str, Any]) -> dict[str, Any]:
        """Encode sequence-valued search filters in the API's CSV format."""
        return {
            key: ",".join(map(str, value))
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes))
            else value
            for key, value in criteria.items()
            if value is not None
        }

    def search_companies(self, **criteria: Any) -> Any:
        """Search companies; provide one or more API search criteria."""
        params = self._query_params(criteria)
        if not params:
            raise ValueError("At least one GEMI search criterion is required.")
        return self._get("/companies", params=params)

    def get_company(self, ar_gemi: int) -> Any:
        """Get the public registry record for a GEMI number."""
        return self._get(f"/companies/{ar_gemi}")

    def get_company_documents(self, ar_gemi: int) -> Any:
        """Get public documents associated with a GEMI number."""
        return self._get(f"/companies/{ar_gemi}/documents")

    def download_file(self, *, key: str, element_id: int) -> bytes:
        """Download an API attachment using its key and element ID."""
        return self._get(
            "/downloadFile",
            params={"key": key, "elementId": element_id},
            binary=True,
        )

    def health(self) -> Any:
        """Check whether the API gateway is responding."""
        return self._get("/health")

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

