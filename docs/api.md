# API reference

The default base URL is
`https://opendata-api.businessportal.gr/api/opendata/v1`.
Requests use the `api_key` header. The client is synchronous and owns its HTTPX
connection pool; use it as a context manager or call `close()`.

## Construction

`GemiClient(api_key=None, *, base_url=..., timeout=30.0)`

- An omitted key is read from `GEMI_OPENDATA_API_KEY`. An explicitly empty key
  raises `ValueError` instead of falling back to the environment.
- `timeout` is a positive, finite number of seconds, applied using HTTPX's
  per-operation timeout behavior; it is not a deadline for an entire workflow.
- A custom base URL must use HTTP(S), include a host, and omit user credentials,
  query parameters, and fragments. Its path prefix is retained for requests.
- Redirects are not followed automatically. No requests are automatically retried.

## Methods

Paths below are relative to the base URL. JSON methods return the upstream JSON
unchanged; the SDK does not yet provide company response models or schema checking.

| Method | GET path | Result |
| --- | --- | --- |
| `search_companies(**criteria)` | `/companies` | JSON |
| `get_company(ar_gemi)` | `/companies/{arGemi}` | JSON |
| `get_company_documents(ar_gemi)` | `/companies/{arGemi}/documents` | JSON |
| `download_file(key=..., element_id=...)` | `/downloadFile` | `bytes` |
| `health()` | `/health` | `True` on HTTP success; raises on failure |
| `list_activities()` | `/metadata/activities` | JSON |
| `list_prefectures()` | `/metadata/prefectures` | JSON |
| `list_municipalities()` | `/metadata/municipalities` | JSON |
| `list_company_statuses()` | `/metadata/companyStatuses` | JSON |
| `list_legal_types()` | `/metadata/legalTypes` | JSON |
| `list_gemi_offices()` | `/metadata/gemiOffices` | JSON |
| `list_assembly_subjects()` | `/metadata/assemblySubjects` | JSON |

Identifiers accept positive integers or ASCII decimal strings. Strings preserve
leading zeroes. Document downloads use the query names `key` and `elementId` and
return bytes without writing any file or trusting a server-provided filename.

### Search criteria

Use the exact upstream query parameter names from the
[official Swagger reference](https://opendata-api.businessportal.gr/opendata/docs/).
Multiple filters are combined with AND by the API.

- At least one nonempty filter is required. `resultsSize` alone is not a filter.
- `resultsSize`, when supplied, must be an integer in the range 1–200.
- `None`, blank strings, and empty sequences are omitted. Strings are trimmed.
- String/integer sequences are encoded as comma-separated values. Empty elements,
  comma-containing elements, booleans, mappings, and binary values are rejected.
- Query names are forwarded as supplied. They are not checked against a local
  allowlist; misspelled or future parameter names remain the server's responsibility.

The client offers neither automatic pagination nor a promise of exhaustive search
results. Do not interpret a limited result set as a complete registry export.

## Errors

Client-side argument/configuration failures raise `ValueError`. SDK runtime errors
inherit from `GemiError`, which can be imported from `gemi_opendata`.

| Exception | Trigger |
| --- | --- |
| `GemiBadRequestError` | HTTP 400 |
| `GemiAuthenticationError` | HTTP 401 or 403 |
| `GemiNotFoundError` | HTTP 404 |
| `GemiRateLimitError` | HTTP 429 |
| `GemiServiceError` | HTTP 5xx |
| `GemiAPIError` | Other unsuccessful HTTP statuses, including redirects |
| `GemiTimeoutError` | HTTPX timeout; also inherits from `GemiTransportError` |
| `GemiTransportError` | Other HTTPX request failures |
| `GemiResponseError` | A successful JSON endpoint returned undecodable JSON |

All HTTP errors inherit from `GemiAPIError`. Its existing `status_code` and
`message` attributes remain available. `errors` is a tuple of dictionaries holding
the string `code`/`message` entries from a structured API error array. Unexpected
payloads fall back to a status description. Raw HTML/text error bodies are omitted.
`retry_after` contains the Retry-After header if supplied; it is a hint, not a
parsed duration or an automatic retry policy. The HTTP mappings also cover standard
statuses not explicitly listed by the upstream Swagger reference.

Timeout and transport errors retain the original HTTPX exception as `__cause__`.
Do not publish full request objects, tracebacks, or production responses without
checking them for sensitive data.

## Verification boundary

The automated suite uses synthetic responses through HTTPX's MockTransport. It
verifies request paths, authentication headers, query encoding, error behavior,
binary downloads, and resource cleanup without a live key or network access.

On 2026-10-25 the official `/api-docs` URL returned HTTP 502 during this audit.
The endpoint map follows the official reference previously reviewed for this
project. Authenticated integration and schema compatibility with the current live
service have not been verified. Recheck the published spec when it is available:

- [Swagger JSON](https://opendata-api.businessportal.gr/api-docs)
- [Technical documentation](https://opendata.businessportal.gr/techdocs/)

