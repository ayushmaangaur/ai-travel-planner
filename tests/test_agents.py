import json

import google.genai
import pytest

from agents.root_agent import RootTravelAgent
from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.weather_agent import WeatherAgent

from models.trip import TravelRequest, TravelPlan
from models.flight import FlightRecommendation
from models.hotel import HotelRecommendation
from models.weather import WeatherRecommendation

from services.llm_service import LLMService


# --------------------------------------------------
# Mock responses
# --------------------------------------------------

def mock_generate(self, prompt: str) -> str:

    prompt_lower = prompt.lower()

    # Root Agent
    if "new user message" in prompt_lower:
        return json.dumps({
            "current_location": "Delhi",
            "origin": "Delhi",
            "destination": "Tokyo",
            "days": 7,
            "budget": 50000,
            "travelers": 2,
            "preference": "non-stop"
        })

    # Flight Agent
    if "flight agent" in prompt_lower:
        return json.dumps({
            "origin": "Delhi",
            "destination": "Tokyo",
            "options": [
                {
                    "airline": "Air India",
                    "flight_number": "AI 306",
                    "departure_airport": "DEL",
                    "arrival_airport": "NRT",
                    "departure_time": "21:15",
                    "arrival_time": "08:00 (+1)",
                    "duration": "8h 15m",
                    "stops": 0,
                    "price": 45000,
                    "currency": "INR"
                }
            ]
        })

    # Hotel Agent
    if "hotel agent" in prompt_lower:
        return json.dumps({
            "destination": "Tokyo",
            "options": [
                {
                    "name": "Tokyo Budget Hotel",
                    "location": "Shinjuku",
                    "rating": 4.2,
                    "price_per_night": 5000,
                    "currency": "INR",
                    "amenities": [
                        "Free Wi-Fi",
                        "Air Conditioning"
                    ]
                }
            ]
        })

    # Weather Agent
    if "weather agent" in prompt_lower:
        return json.dumps({
            "destination": "Tokyo",
            "forecast": [
                {
                    "date": "Day 1",
                    "condition": "Sunny",
                    "temperature": "25°C",
                    "precipitation": "10%"
                }
            ]
        })

    return "{}"


# --------------------------------------------------
# Gemini must never be called
# --------------------------------------------------

def fail_if_gemini_called(*args, **kwargs):
    raise AssertionError(
        "Gemini Client was called during mock-mode testing!"
    )


# --------------------------------------------------
# Fixture
# --------------------------------------------------

@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):

    # Prevent actual Gemini client creation
    monkeypatch.setattr(
        google.genai,
        "Client",
        fail_if_gemini_called
    )

    # Prevent actual Gemini API calls
    monkeypatch.setattr(
        LLMService,
        "generate",
        mock_generate
    )


# --------------------------------------------------
# Root Agent
# --------------------------------------------------

def test_root_agent():

    agent = RootTravelAgent()

    result = agent.plan_trip(
        "I am in Delhi and want to visit Tokyo for 7 days "
        "with 2 people. My budget is 50000 and I prefer non-stop flights."
    )

    assert isinstance(result, TravelPlan)

    assert result.destination == "Tokyo"

    assert isinstance(
        result.flights,
        FlightRecommendation
    )

    assert isinstance(
        result.hotels,
        HotelRecommendation
    )

    assert isinstance(
        result.weather,
        WeatherRecommendation
    )


# --------------------------------------------------
# Flight Agent
# --------------------------------------------------

def test_flight_agent():

    agent = FlightAgent()

    request = TravelRequest(
        origin="Delhi",
        destination="Tokyo",
        days=7,
        budget=50000,
        travelers=2,
        preference="non-stop"
    )

    result = agent.search_flights(request)

    assert isinstance(
        result,
        FlightRecommendation
    )

    assert result.origin == "Delhi"
    assert result.destination == "Tokyo"

    assert len(result.options) > 0

    assert result.options[0].stops == 0


# --------------------------------------------------
# Hotel Agent
# --------------------------------------------------

def test_hotel_agent():

    agent = HotelAgent()

    request = TravelRequest(
        origin="Delhi",
        destination="Tokyo",
        days=7,
        budget=50000,
        travelers=2,
        preference="cheap"
    )

    result = agent.search_hotels(request)

    assert isinstance(
        result,
        HotelRecommendation
    )

    assert result.destination == "Tokyo"

    assert len(result.options) > 0


# --------------------------------------------------
# Weather Agent
# --------------------------------------------------

def test_weather_agent():

    agent = WeatherAgent()

    request = TravelRequest(
        origin="Delhi",
        destination="Tokyo",
        days=7,
        budget=50000,
        travelers=2
    )

    result = agent.get_weather(request)

    assert isinstance(
        result,
        WeatherRecommendation
    )

    assert result.destination == "Tokyo"

    assert isinstance(
        result.forecast,
        list
    )

    assert len(result.forecast) > 0

def test_root_agent_handles_flight_failure(monkeypatch):

    agent = RootTravelAgent()

    def fail_flights(request):
        raise Exception("Flight API timeout")

    monkeypatch.setattr(
        agent.flight_agent,
        "search_flights",
        fail_flights
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
    assert "Flight service unavailable" in result.errors[0]


def test_root_agent_handles_hotel_failure(monkeypatch):

    agent = RootTravelAgent()

    def fail_hotels(request):
        raise Exception("Hotel service unavailable")

    monkeypatch.setattr(
        agent.hotel_agent,
        "search_hotels",
        fail_hotels
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
    assert "Hotel service unavailable" in result.errors[0]


def test_root_agent_handles_weather_failure(monkeypatch):

    agent = RootTravelAgent()

    def fail_weather(request):
        raise Exception("Weather API timeout")

    monkeypatch.setattr(
        agent.weather_agent,
        "get_weather",
        fail_weather
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
    assert "Weather service unavailable" in result.errors[0]

def test_root_agent_handles_all_agent_failures(monkeypatch):

    agent = RootTravelAgent()

    monkeypatch.setattr(
        agent.flight_agent,
        "search_flights",
        lambda request: (_ for _ in ()).throw(Exception("Flight failed"))
    )

    monkeypatch.setattr(
        agent.hotel_agent,
        "search_hotels",
        lambda request: (_ for _ in ()).throw(Exception("Hotel failed"))
    )

    monkeypatch.setattr(
        agent.weather_agent,
        "get_weather",
        lambda request: (_ for _ in ()).throw(Exception("Weather failed"))
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