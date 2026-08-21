import pytest

from a2a.local_transport import LocalA2ATransport
from a2a.router import A2ARouter
from a2a.messages import A2ARequest


class FakeFlightAgent:

    def search_flights(self, request):
        return "flight-result"


class FakeHotelAgent:

    def search_hotels(self, request):
        return "hotel-result"


class FakeWeatherAgent:

    def get_weather(self, request):
        return "weather-result"


def make_router():

    return A2ARouter(
        flight_agent=FakeFlightAgent(),
        hotel_agent=FakeHotelAgent(),
        weather_agent=FakeWeatherAgent(),
    )


def test_local_transport_routes_flight():

    transport = LocalA2ATransport(
        make_router()
    )

    request = A2ARequest(
        sender="root-agent",
        recipient="flight-agent",
        task="search_flights",
        payload={
            "destination": "Tokyo"
        },
    )

    response = transport.send(request)

    assert response.success is True
    assert response.result == "flight-result"


def test_local_transport_routes_hotel():

    transport = LocalA2ATransport(
        make_router()
    )

    request = A2ARequest(
        sender="root-agent",
        recipient="hotel-agent",
        task="search_hotels",
        payload={
            "destination": "Tokyo"
        },
    )

    response = transport.send(request)

    assert response.success is True
    assert response.result == "hotel-result"


def test_local_transport_routes_weather():

    transport = LocalA2ATransport(
        make_router()
    )

    request = A2ARequest(
        sender="root-agent",
        recipient="weather-agent",
        task="get_weather",
        payload={
            "destination": "Tokyo"
        },
    )

    response = transport.send(request)

    assert response.success is True
    assert response.result == "weather-result"


def test_local_transport_rejects_invalid_message():

    transport = LocalA2ATransport(
        make_router()
    )

    with pytest.raises(TypeError):

        transport.send(
            "not an A2A request"
        )