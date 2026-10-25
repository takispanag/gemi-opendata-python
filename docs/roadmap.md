# Roadmap

The synchronous transport, endpoint methods, and error contract provide the current
baseline. The following are real product features that remain unimplemented.
They carry no estimate or guarantee about evaluation time or acceptance.

## Async client and bounded batch lookups

Add asynchronous access for applications that need multiple independent company
lookups without blocking their event loop. Keep the existing synchronous client
usable throughout the change.

Acceptance considerations:

- Async context management closes the connection pool after success or failure.
- All endpoint paths, authentication, query encoding, and error semantics match
  the synchronous API, with shared validation where practical.
- Batch lookups enforce a caller-selected concurrency bound and preserve a clear
  association between each input and its result or error.
- Cancellation stops outstanding work and releases resources; no blocking sleeps
  or synchronous network requests run in the event loop.
- Synthetic tests cover concurrency, mixed success/failure, cancellation, and
  parity between clients. Existing synchronous tests continue to pass.
- Examples demonstrate library use with an existing event loop and without one.

This is a substantial next feature across transport, lifecycle management, error
handling, tests, and documentation. Decide the batch failure/cancellation policy
before implementation.

## Schema-backed response and search models

Once the live Swagger specification is accessible, introduce typed company,
document, metadata, and search objects with a documented compatibility policy.
Handle missing/nullable fields, unknown fields, dates, activity-code versions, and
numeric identifiers without losing information. Decide whether raw JSON remains
the default or becomes an explicit escape hatch. Use synthetic complete fixtures
and add cases for schema drift and malformed responses.

## Metadata caching

The official technical docs recommend caching slowly changing reference data.
Define cache lifetime, manual refresh/invalidation, mutation isolation, and behavior
after refresh failures. Async users will also need concurrent refresh deduplication.
Test expiration and failures using a controlled clock and synthetic HTTP responses.

## Integration verification

When the service and a legitimate personal API key are available, verify the
client against the current official schema in a private environment. Keep keys,
actual registry responses, and identifiers out of source control and test fixtures.
Document any observed contract differences before implementing compatibility work.
