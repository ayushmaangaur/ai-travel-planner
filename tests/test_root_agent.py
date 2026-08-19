from unittest.mock import MagicMock

from agents.root_agent import RootTravelAgent

from models.trip import TravelPlan
from models.flight import FlightRecommendation
from models.hotel import HotelRecommendation
from models.weather import WeatherRecommendation


def make_agent():

    agent = RootTravelAgent()

    # Mock LLM so tests never call Gemini
    agent.llm = MagicMock()

    # Create a complete TravelRequest
    agent.session.request.origin = "Delhi"
    agent.session.request.destination = "Tokyo"
    agent.session.request.days = 7
    agent.session.request.budget = 50000
    agent.session.request.travelers = 2

    agent.llm.parse_travel_request.return_value = (
        agent.session.request
    )

    # Mock all specialized agents
    agent.flight_agent = MagicMock()
    agent.hotel_agent = MagicMock()
    agent.weather_agent = MagicMock()

    return agent


def test_flight_agent_failure():

    agent = make_agent()

    agent.flight_agent.search_flights.side_effect = Exception(
        "Flight API failed"
    )

    agent.hotel_agent.search_hotels.return_value = (
        HotelRecommendation(
            destination="Tokyo",
            options=[]
        )
    )

    agent.weather_agent.get_weather.return_value = (
        WeatherRecommendation(
            destination="Tokyo",
            forecast=[]
        )
    )

    result = agent.plan_trip("Plan my trip")

    assert isinstance(result, TravelPlan)

    assert result.flights is None
    assert result.flight_status == "unavailable"

    assert result.hotels is not None
    assert result.hotel_status == "available"

    assert result.weather is not None
    assert result.weather_status == "available"

    assert len(result.errors) == 1
    assert "FlightAgent" in result.errors[0]


def test_hotel_agent_failure():

    agent = make_agent()

    agent.flight_agent.search_flights.return_value = (
        FlightRecommendation(
            origin="Delhi",
            destination="Tokyo",
            options=[]
        )
    )

    agent.hotel_agent.search_hotels.side_effect = Exception(
        "Hotel API failed"
    )

    agent.weather_agent.get_weather.return_value = (
        WeatherRecommendation(
            destination="Tokyo",
            forecast=[]
        )
    )

    result = agent.plan_trip("Plan my trip")

    assert isinstance(result, TravelPlan)

    assert result.flights is not None
    assert result.flight_status == "available"

    assert result.hotels is None
    assert result.hotel_status == "unavailable"

    assert result.weather is not None
    assert result.weather_status == "available"

    assert len(result.errors) == 1
    assert "HotelAgent" in result.errors[0]


def test_weather_agent_failure():

    agent = make_agent()

    agent.flight_agent.search_flights.return_value = (
        FlightRecommendation(
            origin="Delhi",
            destination="Tokyo",
            options=[]
        )
    )

    agent.hotel_agent.search_hotels.return_value = (
        HotelRecommendation(
            destination="Tokyo",
            options=[]
        )
    )

    agent.weather_agent.get_weather.side_effect = Exception(
        "Weather API failed"
    )

    result = agent.plan_trip("Plan my trip")

    assert isinstance(result, TravelPlan)

    assert result.flights is not None
    assert result.flight_status == "available"

    assert result.hotels is not None
    assert result.hotel_status == "available"

    assert result.weather is None
    assert result.weather_status == "unavailable"

    assert len(result.errors) == 1
    assert "WeatherAgent" in result.errors[0]