# GEMI Open Data Python client

A small Python client for the official Open Data API of Greece's General
Commercial Registry (Γενικό Εμπορικό Μητρώο, GEMI).

The client covers company search, public company records, documents, and reference
data, with input validation and SDK exceptions for API and transport failures.
JSON responses are returned unchanged. This is alpha software; automated tests
use synthetic HTTP responses, and authenticated live integration is unverified.

## Install from source

```shell
git clone https://github.com/takispanag/gemi-opendata-python.git
cd gemi-opendata-python
python -m pip install -e .
```

This project has not been published to PyPI yet.
Python 3.10 or newer is required. A virtual environment is recommended.

## Usage

Request an API key from the [official GEMI Open Data portal](https://opendata.businessportal.gr/).
The Swagger page's `api-docs-key` is for limited documentation testing; it does
not replace requesting your own key.

```python
import os

from gemi_opendata import GemiClient

with GemiClient() as client:  # Reads GEMI_OPENDATA_API_KEY from your environment.
    matches = client.search_companies(afm=os.environ["GEMI_AFM"], resultsSize=10)
    company = client.get_company(os.environ["GEMI_NUMBER"])
    documents = client.get_company_documents(os.environ["GEMI_NUMBER"])
```

Set `GEMI_OPENDATA_API_KEY`, `GEMI_AFM`, and `GEMI_NUMBER` privately for this manual
example. No key or real company identifier is included here. Never put their values
in a commit, uploaded fixture, screenshot, or shared terminal log.

At least one search criterion is required. Multiple criteria are combined with
AND by the API. Sequence values (for example, multiple KAD codes) are sent as
comma-separated values, as required by the API reference.

`resultsSize` must be between 1 and 200. The SDK forwards raw query names to GEMI;
consult the upstream reference for exact filter names. See the
[API reference](docs/api.md) for argument validation and endpoint behavior.

## API coverage

- Search companies and retrieve a company by GEMI number
- Retrieve a company's public documents and download document files
- Retrieve GEMI reference data: activities, prefectures, municipalities,
  company statuses, legal types, GEMI offices, and assembly subjects
- Check API health

## Errors and resource cleanup

Use a context manager to close connections automatically. Invalid local arguments
raise `ValueError`. Runtime failures inherit from `GemiError`:

```python
from gemi_opendata import GemiClient, GemiError, GemiRateLimitError

try:
    with GemiClient() as client:
        print(client.health())  # True after a successful HTTP status.
except GemiRateLimitError as error:
    print("Rate limited; Retry-After hint:", error.retry_after)
except GemiError as error:
    print("GEMI request failed:", error)
```

The SDK distinguishes bad requests, authentication failures, missing records,
rate limits, service errors, transport errors, timeouts, and invalid JSON. It
preserves structured API error details and redacts the configured API key from
them. Requests are not automatically retried and redirects are not followed.
The error hierarchy is documented in [docs/api.md](docs/api.md).

## Development

From the repository root, use an activated virtual environment:

```shell
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m build
```

Tests use HTTPX MockTransport and clearly synthetic values. They do not make
network requests or require a GEMI key. CI runs the suite on Python 3.10–3.13 on
Linux and Python 3.13 on Windows. A configured CI matrix is separate from a
claim that a particular run has passed; check the repository's Actions results.

See the [roadmap](docs/roadmap.md) for async access, typed response/search models,
and metadata caching. These features are not implemented yet.

## Documentation and data terms

- [Official technical documentation](https://opendata.businessportal.gr/techdocs/)
- [Official Swagger / OpenAPI 2.0 specification](https://opendata-api.businessportal.gr/api-docs)
- The API's published data license is ODC-BY-1.0. Data consumers must follow
  its attribution terms. This client is independently licensed under MIT.

The project is not affiliated with or endorsed by GEMI, KEEE, or the Greek
Ministry of Development. Do not commit API keys; use an environment variable or
a secret manager.

During the 2026-10-25 audit, the official API documentation endpoint returned
HTTP 502. Authenticated live behavior still needs verification when the service
is available; see [verification limits](docs/api.md#verification-boundary).

