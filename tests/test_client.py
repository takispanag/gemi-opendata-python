"""Offline contract tests. Every key, identifier, and payload here is synthetic."""

from functools import partial

import httpx
import pytest

import gemi_opendata
from gemi_opendata import GemiAPIError, GemiClient

EXAMPLE_KEY = "YOUR_API_KEY_HERE"


@pytest.fixture
def client_factory(monkeypatch):
    """Replace only the network transport; exercise the real HTTPX client."""
    real_client = httpx.Client
    clients = []

    def create(handler=None, **options):
        handler = handler or (lambda request: httpx.Response(200, json={}))
        monkeypatch.setattr(
            "gemi_opendata.client.httpx.Client",
            partial(real_client, transport=httpx.MockTransport(handler)),
        )
        options.setdefault("api_key", EXAMPLE_KEY)
        client = GemiClient(**options)
        clients.append(client)
        return client

    yield create
    for client in clients:
        client.close()


@pytest.mark.parametrize(
    ("method", "arguments", "path"),
    [
        ("get_company", (1,), "/companies/1"),
        ("get_company_documents", (1,), "/companies/1/documents"),
        ("list_activities", (), "/metadata/activities"),
        ("list_prefectures", (), "/metadata/prefectures"),
        ("list_municipalities", (), "/metadata/municipalities"),
        ("list_company_statuses", (), "/metadata/companyStatuses"),
        ("list_legal_types", (), "/metadata/legalTypes"),
        ("list_gemi_offices", (), "/metadata/gemiOffices"),
        ("list_assembly_subjects", (), "/metadata/assemblySubjects"),
    ],
)
def test_endpoint_preserves_base_path_auth_and_json(
    client_factory, method, arguments, path
):
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/api/opendata/v1" + path
        assert request.headers["api_key"] == EXAMPLE_KEY
        return httpx.Response(200, json={"synthetic": True})

    client = client_factory(handler)
    assert getattr(client, method)(*arguments) == {"synthetic": True}


@pytest.mark.parametrize("body", [b"", b"OK", b'{"status":"ok"}'])
def test_health_uses_success_status_without_requiring_json(client_factory, body):
    def handler(request):
        assert request.url.path == "/api/opendata/v1/health"
        assert request.headers["api_key"] == EXAMPLE_KEY
        return httpx.Response(200, content=body)

    client = client_factory(handler)
    assert client.health() is True


def test_invalid_json_raises_sdk_response_error(client_factory):
    client = client_factory(
        lambda request: httpx.Response(200, content=b"<html>oops</html>")
    )
    with pytest.raises(gemi_opendata.GemiResponseError):
        client.get_company(1)


@pytest.mark.parametrize(
    ("status", "error_name"),
    [
        (400, "GemiBadRequestError"),
        (401, "GemiAuthenticationError"),
        (403, "GemiAuthenticationError"),
        (404, "GemiNotFoundError"),
        (429, "GemiRateLimitError"),
        (500, "GemiServiceError"),
        (503, "GemiServiceError"),
        (418, "GemiAPIError"),
    ],
)
def test_http_errors_have_catchable_semantic_types(client_factory, status, error_name):
    client = client_factory(lambda request: httpx.Response(status))
    error_type = getattr(gemi_opendata, error_name)
    with pytest.raises(error_type) as error:
        client.get_company(1)
    assert type(error.value) is error_type
    assert error.value.status_code == status
    assert isinstance(error.value, gemi_opendata.GemiError)


def test_api_error_exposes_structured_details_and_retry_hint(client_factory):
    client = client_factory(
        lambda request: httpx.Response(
            429,
            json=[{"code": "EXAMPLE_LIMIT", "message": "Synthetic rate limit"}],
            headers={"Retry-After": "30"},
        )
    )
    with pytest.raises(GemiAPIError) as error:
        client.get_company(1)
    assert error.value.errors == (
        {"code": "EXAMPLE_LIMIT", "message": "Synthetic rate limit"},
    )
    assert error.value.retry_after == "30"


def test_api_key_is_redacted_from_structured_error(client_factory):
    client = client_factory(
        lambda request: httpx.Response(
            400, json=[{"code": EXAMPLE_KEY, "message": "Rejected " + EXAMPLE_KEY}]
        )
    )
    with pytest.raises(GemiAPIError) as error:
        client.get_company(1)
    assert EXAMPLE_KEY not in str(error.value)
    assert EXAMPLE_KEY not in repr(error.value.errors)


def test_non_json_http_error_does_not_echo_arbitrary_body(client_factory):
    client = client_factory(
        lambda request: httpx.Response(503, text="<html>" + EXAMPLE_KEY + "</html>")
    )
    with pytest.raises(GemiAPIError) as error:
        client.get_company(1)
    assert EXAMPLE_KEY not in str(error.value)
    assert error.value.errors == ()


@pytest.mark.parametrize(
    ("transport_error", "error_name"),
    [
        (httpx.ReadTimeout, "GemiTimeoutError"),
        (httpx.ConnectError, "GemiTransportError"),
    ],
)
def test_transport_failures_are_wrapped(client_factory, transport_error, error_name):
    def handler(request):
        raise transport_error("Synthetic connection failure", request=request)

    client = client_factory(handler)
    with pytest.raises(getattr(gemi_opendata, error_name)) as error:
        client.get_company(1)
    assert isinstance(error.value.__cause__, transport_error)
    assert isinstance(error.value, gemi_opendata.GemiTransportError)
    assert isinstance(error.value, gemi_opendata.GemiError)


@pytest.mark.parametrize(
    "criteria",
    [
        {},
        {"afm": ""},
        {"afm": "  "},
        {"afm": None},
        {"resultsSize": 10},
        {"synthetic_filter": []},
    ],
)
def test_search_requires_nonempty_filter_not_just_size(client_factory, criteria):
    requests = []
    client = client_factory(
        lambda request: requests.append(request) or httpx.Response(200, json=[])
    )
    with pytest.raises(ValueError):
        client.search_companies(**criteria)
    assert requests == []


@pytest.mark.parametrize("size", [0, -1, 201, True, "10", 1.5])
def test_search_size_must_be_integer_between_one_and_200(client_factory, size):
    client = client_factory()
    with pytest.raises(ValueError):
        client.search_companies(afm="000000000", resultsSize=size)


def test_search_encodes_csv_filters_and_discards_empty_values(client_factory):
    def handler(request):
        assert request.url.path.endswith("/companies")
        assert dict(request.url.params) == {
            "afm": "000000000",
            "synthetic_filter": "1,2",
            "resultsSize": "200",
        }
        return httpx.Response(200, json=[])

    client = client_factory(handler)
    # Synthetic field checks generic CSV encoding, not an upstream filter name.
    assert (
        client.search_companies(
            afm=" 000000000 ",
            synthetic_filter=[1, 2],
            unused=None,
            blank=" ",
            resultsSize=200,
        )
        == []
    )


@pytest.mark.parametrize(
    "value",
    [
        True,
        {},
        {1},
        b"example",
        bytearray(b"example"),
        memoryview(b"example"),
        ["a,b"],
        [None],
    ],
)
def test_search_rejects_ambiguous_query_values(client_factory, value):
    client = client_factory()
    with pytest.raises(ValueError):
        client.search_companies(synthetic_filter=value)


@pytest.mark.parametrize("method", ["get_company", "get_company_documents"])
@pytest.mark.parametrize(
    "identifier", [0, -1, True, "", "../health", "EXAMPLE_ID", "１"]
)
def test_company_identifiers_reject_invalid_path_values(
    client_factory, method, identifier
):
    client = client_factory()
    with pytest.raises(ValueError):
        getattr(client, method)(identifier)


def test_decimal_string_identifier_preserves_leading_zeroes(client_factory):
    def handler(request):
        assert request.url.path.endswith("/companies/000000000001")
        return httpx.Response(200, json={})

    assert client_factory(handler).get_company("000000000001") == {}


def test_document_download_preserves_binary_bytes_and_query_names(client_factory):
    def handler(request):
        assert request.url.path.endswith("/downloadFile")
        assert dict(request.url.params) == {"key": "assemblyDecision", "elementId": "1"}
        return httpx.Response(200, content=b"%PDF-EXAMPLE\x00\xff")

    assert (
        client_factory(handler).download_file(key="assemblyDecision", element_id=1)
        == b"%PDF-EXAMPLE\x00\xff"
    )


@pytest.mark.parametrize(
    "options",
    [
        {"key": "", "element_id": 1},
        {"key": " ", "element_id": 1},
        {"key": "assemblyDecision", "element_id": 0},
    ],
)
def test_document_download_rejects_missing_key_or_invalid_id(client_factory, options):
    with pytest.raises(ValueError):
        client_factory().download_file(**options)


@pytest.mark.parametrize(
    "key", ["", " ", "example\nkey", "example\rkey", "EXAMPLE_Δ_KEY"]
)
def test_explicit_invalid_key_never_falls_back_to_environment(monkeypatch, key):
    monkeypatch.setenv("GEMI_OPENDATA_API_KEY", EXAMPLE_KEY)
    with pytest.raises(ValueError):
        GemiClient(key)


def test_missing_key_is_rejected(monkeypatch):
    monkeypatch.delenv("GEMI_OPENDATA_API_KEY", raising=False)
    with pytest.raises(ValueError):
        GemiClient()


def test_key_can_be_loaded_from_environment(client_factory, monkeypatch):
    monkeypatch.setenv("GEMI_OPENDATA_API_KEY", "ENV_EXAMPLE_API_KEY")

    def handler(request):
        assert request.headers["api_key"] == "ENV_EXAMPLE_API_KEY"
        return httpx.Response(200, json={})

    assert client_factory(handler, api_key=None).list_legal_types() == {}


@pytest.mark.parametrize(
    "base_url",
    [
        "ftp://example.invalid",
        "https://",
        "https://EXAMPLE_USER:EXAMPLE_PASSWORD@example.invalid",
        "https://example.invalid/?key=EXAMPLE",
        "https://example.invalid/#fragment",
    ],
)
def test_base_url_rejects_unsafe_or_ambiguous_configuration(base_url):
    with pytest.raises(ValueError):
        GemiClient(EXAMPLE_KEY, base_url=base_url)


@pytest.mark.parametrize("timeout", [0, -1, True, float("nan"), float("inf")])
def test_timeout_must_be_finite_and_positive(timeout):
    with pytest.raises(ValueError):
        GemiClient(EXAMPLE_KEY, timeout=timeout)


def test_context_manager_closes_connection_pool(client_factory):
    client = client_factory()
    with client:
        assert client.get_company(1) == {}
    with pytest.raises(RuntimeError, match="closed"):
        client.get_company(1)


def test_redirect_is_not_followed_with_credentials(client_factory):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(
            302, headers={"Location": "https://example.invalid/elsewhere"}
        )

    with pytest.raises(GemiAPIError) as error:
        client_factory(handler).get_company(1)
    assert error.value.status_code == 302
    assert len(requests) == 1


@pytest.mark.parametrize(
    "payload", [None, "SYNTHETIC_MESSAGE", {"message": "SYNTHETIC_MESSAGE"}, [None, 7]]
)
def test_unexpected_error_payload_falls_back_to_status(client_factory, payload):
    client = client_factory(lambda request: httpx.Response(503, json=payload))
    with pytest.raises(GemiAPIError) as error:
        client.get_company(1)
    assert error.value.status_code == 503
    assert error.value.errors == ()


def test_service_errors_are_not_automatically_retried(client_factory):
    requests = []
    client = client_factory(
        lambda request: requests.append(request) or httpx.Response(503)
    )
    with pytest.raises(GemiAPIError):
        client.get_company(1)
    assert len(requests) == 1


@pytest.mark.parametrize("name", ["", " "])
def test_search_rejects_empty_parameter_names(client_factory, name):
    with pytest.raises(ValueError):
        client_factory().search_companies(**{name: "EXAMPLE_VALUE"})


def test_api_key_is_redacted_from_custom_http_reason(client_factory):
    client = client_factory(
        lambda request: httpx.Response(
            503, extensions={"reason_phrase": EXAMPLE_KEY.encode("ascii")}
        )
    )
    with pytest.raises(GemiAPIError) as error:
        client.get_company(1)
    assert EXAMPLE_KEY not in str(error.value)
