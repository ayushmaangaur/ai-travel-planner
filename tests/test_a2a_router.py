import pytest

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


def make_request(task):

    recipients = {
        "search_flights": "FlightAgent",
        "search_hotels": "HotelAgent",
        "get_weather": "WeatherAgent",
    }

    return A2ARequest(
        sender="RootTravelAgent",
        recipient=recipients[task],
        task=task,
        payload={
            "destination": "Tokyo"
        },
    )


def test_router_routes_flight():

    router = A2ARouter(
        flight_agent=FakeFlightAgent(),
        hotel_agent=FakeHotelAgent(),
        weather_agent=FakeWeatherAgent(),
    )

    response = router.send(
        make_request("search_flights")
    )

    assert response.success is True
    assert response.result == "flight-result"
    assert response.sender == "FlightAgent"
    assert response.recipient == "RootTravelAgent"


def test_router_routes_hotel():

    router = A2ARouter(
        flight_agent=FakeFlightAgent(),
        hotel_agent=FakeHotelAgent(),
        weather_agent=FakeWeatherAgent(),
    )

    response = router.send(
        make_request("search_hotels")
    )

    assert response.success is True
    assert response.result == "hotel-result"
    assert response.sender == "HotelAgent"
    assert response.recipient == "RootTravelAgent"


def test_router_routes_weather():

    router = A2ARouter(
        flight_agent=FakeFlightAgent(),
        hotel_agent=FakeHotelAgent(),
        weather_agent=FakeWeatherAgent(),
    )

    response = router.send(
        make_request("get_weather")
    )

    assert response.success is True
    assert response.result == "weather-result"
    assert response.sender == "WeatherAgent"
    assert response.recipient == "RootTravelAgent"


def test_invalid_task_is_rejected_before_router():

    with pytest.raises(ValueError, match="Unsupported A2A task"):

        A2ARequest(
            sender="RootTravelAgent",
            recipient="UnknownAgent",
            task="unknown_task",
            payload={
                "destination": "Tokyo"
            },
        )


def test_router_returns_agent_failure():

    class FailingFlightAgent:

        def search_flights(self, request):
            raise RuntimeError("Flight service failed")

    router = A2ARouter(
        flight_agent=FailingFlightAgent(),
        hotel_agent=FakeHotelAgent(),
        weather_agent=FakeWeatherAgent(),
    )

    response = router.send(
        make_request("search_flights")
    )

    assert response.success is False
    assert response.result is None
    assert "Flight service failed" in response.error