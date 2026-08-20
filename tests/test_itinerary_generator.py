from utils.itinerary_generator import ItineraryGenerator

from models.trip import TravelRequest
from models.flight import FlightRecommendation, FlightOption
from models.hotel import HotelRecommendation, HotelOption
from models.weather import WeatherRecommendation, WeatherDay


def test_itinerary_has_exact_number_of_days():

    request = TravelRequest(
        origin="Delhi",
        destination="Tokyo",
        days=7,
        budget=50000,
        travelers=2
    )

    generator = ItineraryGenerator()

    result = generator.generate(
        request,
        None,
        None,
        None
    )

    assert len(result) == 7


def test_itinerary_contains_day_numbers():

    request = TravelRequest(
        origin="Delhi",
        destination="Tokyo",
        days=5,
        travelers=2
    )

    generator = ItineraryGenerator()

    result = generator.generate(
        request,
        None,
        None,
        None
    )

    assert result[0].startswith("Day 1:")
    assert result[1].startswith("Day 2:")
    assert result[2].startswith("Day 3:")
    assert result[3].startswith("Day 4:")
    assert result[4].startswith("Day 5:")


def test_itinerary_uses_hotel_information():

    request = TravelRequest(
        destination="Tokyo",
        days=3
    )

    hotel_result = HotelRecommendation(
        destination="Tokyo",
        options=[
            HotelOption(
                name="Tokyo Budget Hotel",
                location="Shinjuku",
                rating=4.1,
                price_per_night=5000,
                currency="INR",
                amenities=[]
            )
        ]
    )

    generator = ItineraryGenerator()

    result = generator.generate(
        request,
        None,
        hotel_result,
        None
    )

    assert len(result) == 3
    assert "Tokyo Budget Hotel" in result[0]
    assert "Shinjuku" in result[0]


def test_itinerary_uses_weather():

    request = TravelRequest(
        destination="Tokyo",
        days=2
    )

    weather_result = WeatherRecommendation(
        destination="Tokyo",
        forecast=[
            WeatherDay(
                date="Day 1",
                condition="Sunny",
                temperature="25°C",
                precipitation="10%"
            ),
            WeatherDay(
                date="Day 2",
                condition="Rain",
                temperature="20°C",
                precipitation="70%"
            )
        ]
    )

    generator = ItineraryGenerator()

    result = generator.generate(
        request,
        None,
        None,
        weather_result
    )

    assert "Sunny" in result[0]
    assert "25°C" in result[0]
    assert "Rain" in result[1]


def test_itinerary_handles_missing_recommendations():

    request = TravelRequest(
        destination="Tokyo",
        days=4
    )

    generator = ItineraryGenerator()

    result = generator.generate(
        request,
        None,
        None,
        None
    )

    assert len(result) == 4