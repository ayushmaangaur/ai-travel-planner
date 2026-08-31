from unittest.mock import MagicMock

from agents.root_agent import RootTravelAgent

from a2a.messages import A2AResponse

from models.trip import TravelPlan
from models.flight import FlightRecommendation
from models.hotel import HotelRecommendation
from models.weather import WeatherRecommendation


# ============================================================
# HELPERS
# ============================================================

def success_response(result):

    return A2AResponse(
        success=True,
        result=result,
        error=None,
    )


def failure_response(error):

    return A2AResponse(
        success=False,
        result=None,
        error=error,
    )


def make_agent():

    agent = RootTravelAgent()

    # Replace the transport itself with a mock.
    agent.a2a_transport = MagicMock()

    return agent


# ============================================================
# FLIGHT FAILURE
# ============================================================

def test_flight_agent_failure():

    agent = make_agent()

    agent.a2a_transport.send.side_effect = [
        failure_response("Flight API failed"),

        success_response(
            HotelRecommendation(
                destination="Tokyo",
                options=[],
            )
        ),

        success_response(
            WeatherRecommendation(
                destination="Tokyo",
                forecast=[],
            )
        ),
    ]

    result = agent.plan_trip(
        "I am in Delhi and want to visit Tokyo "
        "for 7 days with 2 people. "
        "My budget is 50000."
    )

    assert isinstance(result, TravelPlan)

    assert result.flights is None
    assert result.hotels is not None
    assert result.weather is not None

    assert result.flight_status == "unavailable"
    assert result.hotel_status == "available"
    assert result.weather_status == "available"

    assert len(result.errors) == 1
    assert "FlightAgent" in result.errors[0]


# ============================================================
# HOTEL FAILURE
# ============================================================

def test_hotel_agent_failure():

    agent = make_agent()

    agent.a2a_transport.send.side_effect = [
        success_response(
            FlightRecommendation(
                origin="Delhi",
                destination="Tokyo",
                options=[],
            )
        ),

        failure_response("Hotel API failed"),

        success_response(
            WeatherRecommendation(
                destination="Tokyo",
                forecast=[],
            )
        ),
    ]

    result = agent.plan_trip(
        "I am in Delhi and want to visit Tokyo "
        "for 7 days with 2 people. "
        "My budget is 50000."
    )

    assert isinstance(result, TravelPlan)

    assert result.flights is not None
    assert result.hotels is None
    assert result.weather is not None

    assert result.flight_status == "available"
    assert result.hotel_status == "unavailable"
    assert result.weather_status == "available"

    assert len(result.errors) == 1
    assert "HotelAgent" in result.errors[0]


# ============================================================
# WEATHER FAILURE
# ============================================================

def test_weather_agent_failure():

    agent = make_agent()

    agent.a2a_transport.send.side_effect = [
        success_response(
            FlightRecommendation(
                origin="Delhi",
                destination="Tokyo",
                options=[],
            )
        ),

        success_response(
            HotelRecommendation(
                destination="Tokyo",
                options=[],
            )
        ),

        failure_response("Weather API failed"),
    ]

    result = agent.plan_trip(
        "I am in Delhi and want to visit Tokyo "
        "for 7 days with 2 people. "
        "My budget is 50000."
    )

    assert isinstance(result, TravelPlan)

    assert result.flights is not None
    assert result.hotels is not None
    assert result.weather is None

    assert result.flight_status == "available"
    assert result.hotel_status == "available"
    assert result.weather_status == "unavailable"

    assert len(result.errors) == 1
    assert "WeatherAgent" in result.errors[0]


# ============================================================
# LOCAL A2A TRANSPORT
# ============================================================

def test_root_agent_uses_local_a2a_transport():

    agent = RootTravelAgent()

    from a2a.local_transport import LocalA2ATransport

    assert isinstance(
        agent.a2a_transport,
        LocalA2ATransport,
    )