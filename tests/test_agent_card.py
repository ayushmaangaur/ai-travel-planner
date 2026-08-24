import pytest

from a2a.agent_card import AgentCard


def test_flight_agent_card():

    card = AgentCard(
        name="flight-agent",
        description="Finds suitable flights.",
        capabilities=["search_flights"],
        endpoint="http://localhost:8001",
    )

    assert card.name == "flight-agent"
    assert card.supports("search_flights")
    assert not card.supports("search_hotels")


def test_hotel_agent_card():

    card = AgentCard(
        name="hotel-agent",
        description="Finds suitable hotels.",
        capabilities=["search_hotels"],
        endpoint="http://localhost:8002",
    )

    assert card.supports("search_hotels")


def test_weather_agent_card():

    card = AgentCard(
        name="weather-agent",
        description="Provides weather information.",
        capabilities=["get_weather"],
        endpoint="http://localhost:8003",
    )

    assert card.supports("get_weather")


def test_invalid_agent_name():

    with pytest.raises(ValueError):

        AgentCard(
            name="unknown-agent",
            description="Unknown agent",
            capabilities=["something"],
            endpoint="http://localhost:8000",
        )


def test_empty_capabilities():

    with pytest.raises(ValueError):

        AgentCard(
            name="flight-agent",
            description="Flight agent",
            capabilities=[],
            endpoint="http://localhost:8001",
        )