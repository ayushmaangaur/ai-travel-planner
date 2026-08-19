from agents.hotel_agent import HotelAgent
from models.trip import TravelRequest
from models.hotel import HotelOption


def make_hotel(price):
    return HotelOption(
        name="Test Hotel",
        location="Tokyo",
        rating=4.5,
        price_per_night=price,
        currency="INR",
        amenities=["Wi-Fi"],
    )


def test_over_budget_hotels_are_removed():

    agent = HotelAgent()

    request = TravelRequest(
        destination="Tokyo",
        days=7,
        budget=50000,
        travelers=2,
    )

    options = [
        make_hotel(5000),   # 35,000 total
        make_hotel(7000),   # 49,000 total
        make_hotel(8000),   # 56,000 total
    ]

    result = agent.select_hotels(options, request)

    prices = [hotel.price_per_night for hotel in result]

    assert 5000 in prices
    assert 7000 in prices
    assert 8000 not in prices


def test_within_budget_hotels_are_kept():

    agent = HotelAgent()

    request = TravelRequest(
        destination="Tokyo",
        days=7,
        budget=50000,
        travelers=2,
    )

    options = [
        make_hotel(4000),   # 28,000
        make_hotel(5000),   # 35,000
        make_hotel(6000),   # 42,000
    ]

    result = agent.select_hotels(options, request)

    assert len(result) == 3
    assert all(
        hotel.price_per_night * request.days <= request.budget
        for hotel in result
    )