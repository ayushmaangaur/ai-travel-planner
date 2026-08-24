import pytest
from fastapi.testclient import TestClient

from a2a.http_server import create_app
from a2a.messages import A2AResponse


# ============================================================
# Fake Router
# ============================================================

class FakeRouter:

    def __init__(
        self,
        response=None,
        exception=None,
    ):
        self.response = response
        self.exception = exception
        self.received_message = None

    def send(self, message):

        self.received_message = message

        if self.exception is not None:
            raise self.exception

        return self.response


# ============================================================
# Helpers
# ============================================================

def success_response():

    return A2AResponse(
        sender="flight-agent",
        recipient="root-agent",
        success=True,
        result={
            "origin": "Delhi",
            "destination": "Tokyo",
        },
        error=None,
    )


def failure_response():

    return A2AResponse(
        sender="flight-agent",
        recipient="root-agent",
        success=False,
        result=None,
        error="Flight service unavailable",
    )


def make_client(router):

    app = create_app(router)

    return TestClient(app)


# ============================================================
# Application creation
# ============================================================

def test_create_app_requires_router():

    with pytest.raises(ValueError):

        create_app(None)


# ============================================================
# Successful A2A request
# ============================================================

def test_a2a_endpoint_success():

    router = FakeRouter(
        response=success_response()
    )

    client = make_client(router)

    response = client.post(
        "/a2a",
        json={
            "sender": "root-agent",
            "recipient": "flight-agent",
            "task": "search_flights",
            "payload": {
                "origin": "Delhi",
                "destination": "Tokyo",
                "days": 7,
                "budget": 50000,
                "travelers": 2,
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sender"] == "flight-agent"
    assert data["recipient"] == "root-agent"
    assert data["success"] is True

    assert data["result"] == {
        "origin": "Delhi",
        "destination": "Tokyo",
    }

    assert data["error"] is None


# ============================================================
# Verify router receives A2ARequest
# ============================================================

def test_a2a_endpoint_passes_request_to_router():

    router = FakeRouter(
        response=success_response()
    )

    client = make_client(router)

    client.post(
        "/a2a",
        json={
            "sender": "root-agent",
            "recipient": "hotel-agent",
            "task": "search_hotels",
            "payload": {
                "destination": "Tokyo",
                "days": 7,
            },
        },
    )

    message = router.received_message

    assert message is not None

    assert message.sender == "root-agent"
    assert message.recipient == "hotel-agent"
    assert message.task == "search_hotels"

    assert message.payload == {
        "destination": "Tokyo",
        "days": 7,
    }


# ============================================================
# Failed A2A response
# ============================================================

def test_a2a_endpoint_failure_response():

    router = FakeRouter(
        response=failure_response()
    )

    client = make_client(router)

    response = client.post(
        "/a2a",
        json={
            "sender": "root-agent",
            "recipient": "flight-agent",
            "task": "search_flights",
            "payload": {
                "origin": "Delhi",
                "destination": "Tokyo",
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is False
    assert data["result"] is None

    assert data["error"] == (
        "Flight service unavailable"
    )


# ============================================================
# Invalid task
# ============================================================

def test_a2a_endpoint_rejects_invalid_task():

    router = FakeRouter(
        response=success_response()
    )

    client = make_client(router)

    response = client.post(
        "/a2a",
        json={
            "sender": "root-agent",
            "recipient": "flight-agent",
            "task": "invalid_task",
            "payload": {
                "origin": "Delhi",
                "destination": "Tokyo",
            },
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert "Unsupported A2A task" in data["detail"]


# ============================================================
# Missing payload
# ============================================================

def test_a2a_endpoint_rejects_missing_payload():

    router = FakeRouter(
        response=success_response()
    )

    client = make_client(router)

    response = client.post(
        "/a2a",
        json={
            "sender": "root-agent",
            "recipient": "flight-agent",
            "task": "search_flights",
        },
    )

    assert response.status_code == 422


# ============================================================
# Empty sender
# ============================================================

def test_a2a_endpoint_rejects_empty_sender():

    router = FakeRouter(
        response=success_response()
    )

    client = make_client(router)

    response = client.post(
        "/a2a",
        json={
            "sender": "",
            "recipient": "flight-agent",
            "task": "search_flights",
            "payload": {
                "origin": "Delhi",
                "destination": "Tokyo",
            },
        },
    )

    assert response.status_code == 400

    assert "sender" in response.json()["detail"]


# ============================================================
# Same sender and recipient
# ============================================================

def test_a2a_endpoint_rejects_same_sender_recipient():

    router = FakeRouter(
        response=success_response()
    )

    client = make_client(router)

    response = client.post(
        "/a2a",
        json={
            "sender": "root-agent",
            "recipient": "root-agent",
            "task": "search_flights",
            "payload": {
                "origin": "Delhi",
                "destination": "Tokyo",
            },
        },
    )

    assert response.status_code == 400

    assert "different" in response.json()["detail"]


# ============================================================
# Router exception
# ============================================================

def test_a2a_endpoint_handles_router_exception():

    router = FakeRouter(
        exception=Exception(
            "Router crashed"
        )
    )

    client = make_client(router)

    response = client.post(
        "/a2a",
        json={
            "sender": "root-agent",
            "recipient": "flight-agent",
            "task": "search_flights",
            "payload": {
                "origin": "Delhi",
                "destination": "Tokyo",
            },
        },
    )

    assert response.status_code == 500

    data = response.json()

    assert "A2A router failed" in data["detail"]

    assert "Router crashed" in data["detail"]


# ============================================================
# All supported tasks
# ============================================================

@pytest.mark.parametrize(
    "task,recipient",
    [
        ("search_flights", "flight-agent"),
        ("search_hotels", "hotel-agent"),
        ("get_weather", "weather-agent"),
    ],
)
def test_a2a_endpoint_supports_all_tasks(
    task,
    recipient,
):

    router = FakeRouter(
        response=success_response()
    )

    client = make_client(router)

    response = client.post(
        "/a2a",
        json={
            "sender": "root-agent",
            "recipient": recipient,
            "task": task,
            "payload": {
                "destination": "Tokyo",
            },
        },
    )

    assert response.status_code == 200

    assert response.json()["success"] is True