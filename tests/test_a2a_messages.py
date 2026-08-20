import pytest

from a2a.messages import A2ARequest, A2AResponse


def test_valid_flight_request():

    request = A2ARequest(
        sender="root-agent",
        recipient="flight-agent",
        task="search_flights",
        payload={"destination": "Tokyo"},
    )

    assert request.sender == "root-agent"
    assert request.recipient == "flight-agent"
    assert request.task == "search_flights"
    assert request.payload["destination"] == "Tokyo"


def test_valid_hotel_request():

    request = A2ARequest(
        sender="root-agent",
        recipient="hotel-agent",
        task="search_hotels",
        payload={"destination": "Tokyo"},
    )

    assert request.task == "search_hotels"


def test_valid_weather_request():

    request = A2ARequest(
        sender="root-agent",
        recipient="weather-agent",
        task="get_weather",
        payload={"destination": "Tokyo"},
    )

    assert request.task == "get_weather"


def test_invalid_task_is_rejected():

    with pytest.raises(ValueError):
        A2ARequest(
            sender="root-agent",
            recipient="flight-agent",
            task="hack_database",
            payload={},
        )


def test_sender_and_recipient_cannot_be_same():

    with pytest.raises(ValueError):
        A2ARequest(
            sender="flight-agent",
            recipient="flight-agent",
            task="search_flights",
            payload={},
        )


def test_empty_payload_is_rejected():

    with pytest.raises(ValueError):
        A2ARequest(
            sender="root-agent",
            recipient="flight-agent",
            task="search_flights",
            payload=None,
        )


def test_successful_response_requires_result():

    with pytest.raises(ValueError):
        A2AResponse(
            sender="flight-agent",
            recipient="root-agent",
            success=True,
            result=None,
        )


def test_failed_response_requires_error():

    with pytest.raises(ValueError):
        A2AResponse(
            sender="flight-agent",
            recipient="root-agent",
            success=False,
            error=None,
        )


def test_valid_success_response():

    response = A2AResponse(
        sender="flight-agent",
        recipient="root-agent",
        success=True,
        result={"flights": []},
    )

    assert response.success is True
    assert response.result == {"flights": []}


def test_valid_failure_response():

    response = A2AResponse(
        sender="flight-agent",
        recipient="root-agent",
        success=False,
        error="Flight service unavailable",
    )

    assert response.success is False
    assert response.error == "Flight service unavailable"