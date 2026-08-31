import json

import pytest

from agents.root_agent import RootTravelAgent
from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.weather_agent import WeatherAgent

from models.trip import TravelRequest, TravelPlan
from models.flight import FlightRecommendation
from models.hotel import HotelRecommendation
from models.weather import WeatherRecommendation


# ============================================================
# GEMINI MOCK
# ============================================================

@pytest.fixture(autouse=True)
def mock_gemini(monkeypatch):
    """
    Prevent real Gemini API calls during agent tests.

    Individual tests can override this mock when they need
    to test specific LLM behavior.
    """

    def fake_generate(self, prompt):

        # Flight Agent
        if "Flight Agent" in prompt:
            return json.dumps({
                "origin": "Delhi",
                "destination": "Tokyo",
                "options": [
                    {
                        "airline": "Test Airline",
                        "flight_number": "TA123",
                        "departure_airport": "DEL",
                        "arrival_airport": "NRT",
                        "departure_time": "10:00",
                        "arrival_time": "20:00",
                        "duration": "10h",
                        "stops": 0,
                        "price": 20000,
                        "currency": "INR",
                    }
                ],
            })

        # Hotel Agent
        if "Hotel Agent" in prompt:
            return json.dumps({
                "destination": "Tokyo",
                "options": [
                    {
                        "name": "Test Hotel",
                        "location": "Shinjuku",
                        "rating": 4.0,
                        "price_per_night": 4000,
                        "currency": "INR",
                        "amenities": ["Wi-Fi"],
                    }
                ],
            })

        # Weather Agent
        if "Weather Agent" in prompt:
            return json.dumps({
                "destination": "Tokyo",
                "forecast": [
                    {
                        "date": "Day 1",
                        "condition": "Sunny",
                        "temperature": "20°C",
                        "precipitation": "10%",
                    },
                    {
                        "date": "Day 2",
                        "condition": "Cloudy",
                        "temperature": "19°C",
                        "precipitation": "20%",
                    },
                    {
                        "date": "Day 3",
                        "condition": "Sunny",
                        "temperature": "21°C",
                        "precipitation": "10%",
                    },
                ],
            })

        # Root Agent travel-request parsing
        return json.dumps({
            "current_location": "Delhi",
            "origin": "Delhi",
            "destination": "Tokyo",
            "days": 3,
            "budget": 60000,
            "travelers": 2,
            "preference": "cheap flights",
        })

    monkeypatch.setattr(
        "services.llm_service.LLMService.generate",
        fake_generate,
    )


# ============================================================
# ROOT AGENT
# ============================================================

def test_root_agent():

    agent = RootTravelAgent()

    result = agent.plan_trip(
        "I am in Delhi and want to travel to Tokyo "
        "for 3 days with 2 people. "
        "My budget is 60000 rupees and I prefer cheap flights."
    )

    assert isinstance(result, TravelPlan)
    assert result.destination == "Tokyo"


# ============================================================
# FLIGHT AGENT
# ============================================================

def test_flight_agent():

    agent = FlightAgent()

    request = TravelRequest(
        origin="Delhi",
        destination="Tokyo",
        days=3,
        budget=60000,
        travelers=2,
    )

    result = agent.search_flights(request)

    assert isinstance(result, FlightRecommendation)
    assert result.origin == "Delhi"
    assert result.destination == "Tokyo"
    assert len(result.options) > 0


# ============================================================
# HOTEL AGENT
# ============================================================

def test_hotel_agent():

    agent = HotelAgent()

    request = TravelRequest(
        destination="Tokyo",
        days=3,
        budget=60000,
        travelers=2,
    )

    result = agent.search_hotels(request)

    assert isinstance(result, HotelRecommendation)
    assert result.destination == "Tokyo"
    assert len(result.options) > 0


# ============================================================
# WEATHER AGENT
# ============================================================

def test_weather_agent():

    agent = WeatherAgent()

    request = TravelRequest(
        destination="Tokyo",
        days=3,
        travelers=2,
    )

    result = agent.get_weather(request)

    assert isinstance(result, WeatherRecommendation)
    assert result.destination == "Tokyo"
    assert len(result.forecast) > 0


# ============================================================
# ROOT AGENT FAILURE HANDLING
# ============================================================

def test_root_agent_handles_flight_failure(monkeypatch):

    agent = RootTravelAgent()

    def fail_flights(request):
        raise Exception("Flight API timeout")

    monkeypatch.setattr(
        agent.flight_agent,
        "search_flights",
        fail_flights,
    )

    result = agent.plan_trip(
        "I am in Delhi and want to visit Tokyo for 7 days "
        "with 2 people. My budget is 50000."
    )

    assert isinstance(result, TravelPlan)

    assert result.flights is None
    assert result.hotels is not None
    assert result.weather is not None

    assert len(result.errors) == 1
    assert "FlightAgent" in result.errors[0]


def test_root_agent_handles_hotel_failure(monkeypatch):

    agent = RootTravelAgent()

    def fail_hotels(request):
        raise Exception("Hotel service unavailable")

    monkeypatch.setattr(
        agent.hotel_agent,
        "search_hotels",
        fail_hotels,
    )

    result = agent.plan_trip(
        "I am in Delhi and want to visit Tokyo for 7 days "
        "with 2 people. My budget is 50000."
    )

    assert isinstance(result, TravelPlan)

    assert result.flights is not None
    assert result.hotels is None
    assert result.weather is not None

    assert len(result.errors) == 1
    assert "HotelAgent" in result.errors[0]


def test_root_agent_handles_weather_failure(monkeypatch):

    agent = RootTravelAgent()

    def fail_weather(request):
        raise Exception("Weather API timeout")

    monkeypatch.setattr(
        agent.weather_agent,
        "get_weather",
        fail_weather,
    )

    result = agent.plan_trip(
        "I am in Delhi and want to visit Tokyo for 7 days "
        "with 2 people. My budget is 50000."
    )

    assert isinstance(result, TravelPlan)

    assert result.flights is not None
    assert result.hotels is not None
    assert result.weather is None

    assert len(result.errors) == 1
    assert "WeatherAgent" in result.errors[0]


def test_root_agent_handles_all_agent_failures(monkeypatch):

    agent = RootTravelAgent()

    monkeypatch.setattr(
        agent.flight_agent,
        "search_flights",
        lambda request: (
            (_ for _ in ()).throw(Exception("Flight failed"))
        ),
    )

    monkeypatch.setattr(
        agent.hotel_agent,
        "search_hotels",
        lambda request: (
            (_ for _ in ()).throw(Exception("Hotel failed"))
        ),
    )

    monkeypatch.setattr(
        agent.weather_agent,
        "get_weather",
        lambda request: (
            (_ for _ in ()).throw(Exception("Weather failed"))
        ),
    )

    result = agent.plan_trip(
        "I am in Delhi and want to visit Tokyo for 7 days "
        "with 2 people. My budget is 50000."
    )

    assert isinstance(result, TravelPlan)

    assert result.destination == "Tokyo"
    assert result.flights is None
    assert result.hotels is None
    assert result.weather is None

    assert len(result.errors) == 3