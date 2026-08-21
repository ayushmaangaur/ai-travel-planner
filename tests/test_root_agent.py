from unittest.mock import MagicMock

from agents.root_agent import RootTravelAgent

from models.trip import TravelPlan

from models.flight import FlightRecommendation
from models.hotel import HotelRecommendation
from models.weather import WeatherRecommendation

from a2a.messages import A2AResponse


def make_agent():
    agent = RootTravelAgent()

    # Mock LLM so tests never call Gemini
    agent.llm = MagicMock()

    # Complete TravelRequest
    agent.session.request.origin = "Delhi"
    agent.session.request.destination = "Tokyo"
    agent.session.request.days = 7
    agent.session.request.budget = 50000
    agent.session.request.travelers = 2

    agent.llm.parse_travel_request.return_value = (
        agent.session.request
    )

    # Mock A2A trancsport
    agent.a2a_transport = MagicMock()

    return agent


def success_response(result):
    return A2AResponse(
        sender="SpecializedAgent",
        recipient="RootTravelAgent",
        success=True,
        result=result,
        error=None,
    )


def failure_response(error):
    return A2AResponse(
        sender="SpecializedAgent",
        recipient="RootTravelAgent",
        success=False,
        result=None,
        error=error,
    )


def test_flight_agent_failure():

    agent = make_agent()

    agent.a2a_transport.send.side_effect = [
        failure_response("Flight API failed"),
        success_response(
            HotelRecommendation(
                destination="Tokyo",
                options=[]
            )
        ),
        success_response(
            WeatherRecommendation(
                destination="Tokyo",
                forecast=[]
            )
        ),
    ]

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

    agent.a2a_transport.send.side_effect =[
        success_response(
            FlightRecommendation(
                origin="Delhi",
                destination="Tokyo",
                options=[]
            )
        ),
        failure_response("Hotel API failed"),
        success_response(
            WeatherRecommendation(
                destination="Tokyo",
                forecast=[]
            )
        ),
    ]

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

    agent.a2a_transport.send.side_effect =[
        success_response(
            FlightRecommendation(
                origin="Delhi",
                destination="Tokyo",
                options=[]
            )
        ),
        success_response(
            HotelRecommendation(
                destination="Tokyo",
                options=[]
            )
        ),
        failure_response("Weather API failed"),
    ]

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

def test_root_agent_uses_local_a2a_transport(monkeypatch):

    agent = RootTravelAgent()

    calls = []

    original_send = agent.a2a_transport.send

    def tracked_send(message):

        calls.append(message.task)

        return original_send(message)

    monkeypatch.setattr(
        agent.a2a_transport,
        "send",
        tracked_send
    )

    result = agent.plan_trip(
        "I am in Delhi and want to visit Tokyo for 7 days "
        "with 2 people. My budget is 50000."
    )

    assert result.destination == "Tokyo"

    assert calls == [
        "search_flights",
        "search_hotels",
        "get_weather",
    ]