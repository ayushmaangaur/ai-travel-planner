from agents.flight_agent import FlightAgent
from models.trip import TravelRequest
from models.flight import FlightOption


def make_flight(price, stops=0):
    return FlightOption(
        airline="Test Airline",
        flight_number="TEST123",
        departure_airport="DEL",
        arrival_airport="NRT",
        departure_time="10:00",
        arrival_time="20:00",
        duration="8h",
        stops=stops,
        price=price,
        currency="INR",
    )


def test_over_budget_flights_are_removed():

    agent = FlightAgent()

    request = TravelRequest(
        origin="Delhi",
        destination="Tokyo",
        budget=50000,
        travelers=2,
    )

    options = [
        make_flight(45000),
        make_flight(50000),
        make_flight(55000),
    ]

    result = agent.select_flights(options, request)

    prices = [flight.price for flight in result]

    assert 45000 in prices
    assert 50000 in prices
    assert 55000 not in prices


def test_within_budget_flights_are_kept():

    agent = FlightAgent()

    request = TravelRequest(
        origin="Delhi",
        destination="Tokyo",
        budget=50000,
        travelers=2,
    )

    options = [
        make_flight(25000),
        make_flight(35000),
        make_flight(45000),
    ]

    result = agent.select_flights(options, request)

    assert len(result) == 3
    assert all(flight.price <= 50000 for flight in result)