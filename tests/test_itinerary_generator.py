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

    assert len(result) == 5
    assert [day.day for day in result] == [1, 2, 3, 4, 5]


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
    assert any(
        "Tokyo Budget Hotel" in tip
        for tip in result[0].travel_tips
    )
    assert result[0].morning[0].location == "Shinjuku"

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

    assert result[0].weather_note is not None
    assert "Sunny" in result[0].weather_note
    assert "25°C" in result[0].weather_note

    assert result[1].weather_note is not None
    assert "Rain" in result[1].weather_note
    assert "20°C" in result[1].weather_note


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

def test_late_arrival_is_scheduled_in_evening():

    request = TravelRequest(
        destination="Goa",
        days=3,
    )

    flight_result = FlightRecommendation(
        origin="Delhi",
        destination="Goa",
        options=[
            FlightOption(
                airline="Test Airline",
                flight_number="TA123",
                arrival_time="19:25",
                price=10000,
            )
        ],
    )

    generator = ItineraryGenerator()

    result = generator.generate(
        request,
        flight_result,
        None,
        None,
    )

    day_one = result[0]

    assert day_one.morning == []
    assert day_one.afternoon == []

    assert any(
        activity.name == "Arrival and check-in"
        for activity in day_one.evening
    )

def test_afternoon_arrival_is_scheduled_in_afternoon():

    request = TravelRequest(
        destination="Goa",
        days=3,
    )

    flight_result = FlightRecommendation(
        origin="Delhi",
        destination="Goa",
        options=[
            FlightOption(
                airline="Test Airline",
                flight_number="TA123",
                arrival_time="15:30",
                price=10000,
            )
        ],
    )

    generator = ItineraryGenerator()

    result = generator.generate(
        request,
        flight_result,
        None,
        None,
    )

    day_one = result[0]

    assert any(
        activity.name == "Arrival and check-in"
        for activity in day_one.afternoon
    )

    assert all(
        activity.name != "Arrival and check-in"
        for activity in day_one.morning
    )

def test_morning_arrival_is_scheduled_in_morning():

    request = TravelRequest(
        destination="Goa",
        days=3,
    )

    flight_result = FlightRecommendation(
        origin="Delhi",
        destination="Goa",
        options=[
            FlightOption(
                airline="Test Airline",
                flight_number="TA123",
                arrival_time="09:30",
                price=10000,
            )
        ],
    )

    generator = ItineraryGenerator()

    result = generator.generate(
        request,
        flight_result,
        None,
        None,
    )

    day_one = result[0]

    assert any(
        activity.name == "Arrival and check-in"
        for activity in day_one.morning
    )

    assert all(
        activity.name != "Arrival and check-in"
        for activity in day_one.afternoon
    )

def test_generated_activities_have_cost_estimates():

    request = TravelRequest(
        destination="Goa",
        days=3,
    )

    generator = ItineraryGenerator()

    result = generator.generate(
        request,
        None,
        None,
        None,
    )

    activities = []

    for day in result:
        activities.extend(day.morning)
        activities.extend(day.afternoon)
        activities.extend(day.evening)

    assert len(activities) > 0

    assert any(
        activity.estimated_cost > 0
        for activity in activities
    )

def test_arrival_activity_has_zero_cost():

    request = TravelRequest(
        destination="Goa",
        days=3,
    )

    generator = ItineraryGenerator()

    result = generator.generate(
        request,
        None,
        None,
        None,
    )

    arrival = result[0].morning[0]

    assert arrival.name == "Arrival and check-in"
    assert arrival.estimated_cost == 0.0