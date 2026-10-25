# Changelog

## Unreleased

- Add SDK exception types for HTTP, transport, timeout, and JSON decoding failures.
- Preserve structured API errors and Retry-After hints; redact the configured API
  key from structured error details and avoid echoing arbitrary server bodies.
- Validate client configuration, company/document identifiers, nonempty search
  criteria, query value types, and resultsSize bounds before sending requests.
- Return True from health() after a successful status, including empty/text bodies.
  This replaces the earlier behavior of attempting JSON decoding for this endpoint.
- Add offline tests, development dependencies, and CI for the supported Python range.

## 0.1.0 (unreleased initial version)

- Introduce the synchronous client for the GEMI Open Data endpoint families.
- Provide source installation, package metadata, and an MIT license.

No version has been published to PyPI.
