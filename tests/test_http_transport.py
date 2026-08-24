import pytest

from a2a.http_transport import HTTPA2ATransport
from a2a.messages import A2ARequest, A2AResponse


# ============================================================
# Helpers
# ============================================================

def make_request():
    return A2ARequest(
        sender="root-agent",
        recipient="flight-agent",
        task="search_flights",
        payload={
            "origin": "Delhi",
            "destination": "Tokyo",
            "days": 7,
            "budget": 50000,
            "travelers": 2,
        },
    )


class FakeResponse:

    def __init__(
        self,
        status_code=200,
        json_data=None,
    ):
        self.status_code = status_code
        self.json_data = json_data

    def json(self):
        if isinstance(self.json_data, Exception):
            raise self.json_data

        return self.json_data


# ============================================================
# Initialization
# ============================================================

def test_http_transport_requires_base_url():

    with pytest.raises(ValueError):

        HTTPA2ATransport("")


def test_http_transport_requires_positive_timeout():

    with pytest.raises(ValueError):

        HTTPA2ATransport(
            "http://localhost:8000",
            timeout=0,
        )


def test_http_transport_strips_trailing_slash():

    transport = HTTPA2ATransport(
        "http://localhost:8000/"
    )

    assert transport.base_url == "http://localhost:8000"


# ============================================================
# Request validation
# ============================================================

def test_send_requires_a2a_request():

    transport = HTTPA2ATransport(
        "http://localhost:8000"
    )

    with pytest.raises(TypeError):

        transport.send(
            "not an A2A request"
        )


# ============================================================
# Successful HTTP request
# ============================================================

def test_send_success(monkeypatch):

    transport = HTTPA2ATransport(
        "http://localhost:8000"
    )

    request = make_request()

    captured = {}

    def fake_post(
        url,
        json,
        timeout,
    ):

        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout

        return FakeResponse(
            status_code=200,
            json_data={
                "sender": "flight-agent",
                "recipient": "root-agent",
                "success": True,
                "result": {
                    "origin": "Delhi",
                    "destination": "Tokyo",
                },
                "error": None,
            },
        )

    monkeypatch.setattr(
        "a2a.http_transport.requests.post",
        fake_post,
    )

    result = transport.send(request)

    assert isinstance(
        result,
        A2AResponse
    )

    assert result.sender == "flight-agent"
    assert result.recipient == "root-agent"
    assert result.success is True

    assert result.result == {
        "origin": "Delhi",
        "destination": "Tokyo",
    }

    assert result.error is None

    assert captured["url"] == (
        "http://localhost:8000/a2a"
    )

    assert captured["timeout"] == 10.0

    assert captured["json"]["sender"] == "root-agent"
    assert captured["json"]["recipient"] == "flight-agent"
    assert captured["json"]["task"] == "search_flights"


# ============================================================
# Failed A2A response
# ============================================================

def test_send_failed_a2a_response(monkeypatch):

    transport = HTTPA2ATransport(
        "http://localhost:8000"
    )

    request = make_request()

    def fake_post(
        url,
        json,
        timeout,
    ):

        return FakeResponse(
            status_code=200,
            json_data={
                "sender": "flight-agent",
                "recipient": "root-agent",
                "success": False,
                "result": None,
                "error": "Flight API unavailable",
            },
        )

    monkeypatch.setattr(
        "a2a.http_transport.requests.post",
        fake_post,
    )

    result = transport.send(request)

    assert isinstance(
        result,
        A2AResponse
    )

    assert result.success is False
    assert result.result is None
    assert result.error == (
        "Flight API unavailable"
    )


# ============================================================
# HTTP error status
# ============================================================

def test_send_http_error(monkeypatch):

    transport = HTTPA2ATransport(
        "http://localhost:8000"
    )

    request = make_request()

    def fake_post(
        url,
        json,
        timeout,
    ):

        return FakeResponse(
            status_code=500,
            json_data={
                "error": "Internal server error"
            },
        )

    monkeypatch.setattr(
        "a2a.http_transport.requests.post",
        fake_post,
    )

    with pytest.raises(RuntimeError) as exc:

        transport.send(request)

    assert "status 500" in str(exc.value)


# ============================================================
# Invalid JSON
# ============================================================

def test_send_invalid_json(monkeypatch):

    transport = HTTPA2ATransport(
        "http://localhost:8000"
    )

    request = make_request()

    def fake_post(
        url,
        json,
        timeout,
    ):

        return FakeResponse(
            status_code=200,
            json_data=ValueError(
                "Invalid JSON"
            ),
        )

    monkeypatch.setattr(
        "a2a.http_transport.requests.post",
        fake_post,
    )

    with pytest.raises(RuntimeError) as exc:

        transport.send(request)

    assert "invalid JSON" in str(
        exc.value
    )


# ============================================================
# Invalid response structure
# ============================================================

def test_send_invalid_response_structure(monkeypatch):

    transport = HTTPA2ATransport(
        "http://localhost:8000"
    )

    request = make_request()

    def fake_post(
        url,
        json,
        timeout,
    ):

        return FakeResponse(
            status_code=200,
            json_data={
                "sender": "flight-agent",
                # recipient missing
                "success": True,
                "result": {},
            },
        )

    monkeypatch.setattr(
        "a2a.http_transport.requests.post",
        fake_post,
    )

    with pytest.raises(RuntimeError) as exc:

        transport.send(request)

    assert "Invalid A2A HTTP response" in str(
        exc.value
    )


# ============================================================
# Network failure
# ============================================================

def test_send_network_failure(monkeypatch):

    import requests

    transport = HTTPA2ATransport(
        "http://localhost:8000"
    )

    request = make_request()

    def fake_post(
        url,
        json,
        timeout,
    ):

        raise requests.ConnectionError(
            "Connection refused"
        )

    monkeypatch.setattr(
        "a2a.http_transport.requests.post",
        fake_post,
    )

    with pytest.raises(RuntimeError) as exc:

        transport.send(request)

    assert "A2A HTTP request failed" in str(
        exc.value
    )