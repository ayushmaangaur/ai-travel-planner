from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_check():

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok"
    }


def test_plan_trip(monkeypatch):

    from models.trip import TravelPlan

    expected_plan = TravelPlan(
        destination="Tokyo",
        itinerary=[],
        flights=None,
        hotels=None,
        weather=None,
        flight_status="available",
        hotel_status="available",
        weather_status="available",
        errors=[],
    )

    def fake_plan_trip(message):

        assert "Tokyo" in message
        assert "50000" in message
        assert "2" in message

        return expected_plan

    monkeypatch.setattr(
        "api.routes.travel.travel_service.plan_trip",
        fake_plan_trip,
    )

    response = client.post(
        "/travel/plan",
        json={
            "current_location": "Delhi",
            "origin": "Delhi",
            "destination": "Tokyo",
            "days": 7,
            "budget": 50000,
            "travelers": 2,
            "preference": "cheap flights",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["destination"] == "Tokyo"
    assert data["flight_status"] == "available"
    assert data["hotel_status"] == "available"
    assert data["weather_status"] == "available"
    assert data["errors"] == []

def test_plan_trip_returns_nested_recommendations(monkeypatch):

    from models.trip import TravelPlan
    from models.flight import FlightRecommendation, FlightOption
    from models.hotel import HotelRecommendation, HotelOption
    from models.weather import WeatherRecommendation, WeatherDay

    expected_plan = TravelPlan(
        destination="Tokyo",
        itinerary=["Visit Shibuya", "Visit Tokyo Tower"],

        flights=FlightRecommendation(
            origin="Delhi",
            destination="Tokyo",
            options=[
                FlightOption(
                    airline="Test Airline",
                    flight_number="TA123",
                    departure_airport="DEL",
                    arrival_airport="NRT",
                    departure_time="10:00",
                    arrival_time="20:00",
                    duration="10h",
                    stops=0,
                    price=20000,
                    currency="INR",
                )
            ],
        ),

        hotels=HotelRecommendation(
            destination="Tokyo",
            options=[
                HotelOption(
                    name="Test Hotel",
                    location="Shinjuku",
                    rating=4.0,
                    price_per_night=4000,
                    currency="INR",
                    amenities=["Wi-Fi", "Breakfast"],
                )
            ],
        ),

        weather=WeatherRecommendation(
            destination="Tokyo",
            forecast=[
                WeatherDay(
                    date="Day 1",
                    condition="Sunny",
                    temperature="20°C",
                    precipitation="10%",
                )
            ],
        ),

        flight_status="available",
        hotel_status="available",
        weather_status="available",
        errors=[],
    )

    def fake_plan_trip(message):
        return expected_plan

    monkeypatch.setattr(
        "api.routes.travel.travel_service.plan_trip",
        fake_plan_trip,
    )

    response = client.post(
        "/travel/plan",
        json={
            "current_location": "Delhi",
            "origin": "Delhi",
            "destination": "Tokyo",
            "days": 7,
            "budget": 50000,
            "travelers": 2,
            "preference": "cheap flights",
        },
    )

    assert response.status_code == 200

    data = response.json()

    # --------------------------------------------------------
    # Top-level response
    # --------------------------------------------------------

    assert data["destination"] == "Tokyo"
    assert data["itinerary"] == [
        "Visit Shibuya",
        "Visit Tokyo Tower",
    ]

    # --------------------------------------------------------
    # Flight response
    # --------------------------------------------------------

    assert data["flights"]["origin"] == "Delhi"
    assert data["flights"]["destination"] == "Tokyo"

    assert len(data["flights"]["options"]) == 1

    flight = data["flights"]["options"][0]

    assert flight["airline"] == "Test Airline"
    assert flight["flight_number"] == "TA123"
    assert flight["departure_airport"] == "DEL"
    assert flight["arrival_airport"] == "NRT"
    assert flight["stops"] == 0
    assert flight["price"] == 20000
    assert flight["currency"] == "INR"

    # --------------------------------------------------------
    # Hotel response
    # --------------------------------------------------------

    assert data["hotels"]["destination"] == "Tokyo"

    assert len(data["hotels"]["options"]) == 1

    hotel = data["hotels"]["options"][0]

    assert hotel["name"] == "Test Hotel"
    assert hotel["location"] == "Shinjuku"
    assert hotel["rating"] == 4.0
    assert hotel["price_per_night"] == 4000
    assert hotel["amenities"] == [
        "Wi-Fi",
        "Breakfast",
    ]

    # --------------------------------------------------------
    # Weather response
    # --------------------------------------------------------

    assert data["weather"]["destination"] == "Tokyo"

    assert len(data["weather"]["forecast"]) == 1

    weather = data["weather"]["forecast"][0]

    assert weather["date"] == "Day 1"
    assert weather["condition"] == "Sunny"
    assert weather["temperature"] == "20°C"
    assert weather["precipitation"] == "10%"

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    assert data["flight_status"] == "available"
    assert data["hotel_status"] == "available"
    assert data["weather_status"] == "available"
    assert data["errors"] == []

def test_plan_trip_returns_partial_plan_when_agent_fails(monkeypatch):

    from models.trip import TravelPlan

    partial_plan = TravelPlan(
        destination="Tokyo",
        itinerary=[],
        flights=None,
        hotels=None,
        weather=None,
        flight_status="unavailable",
        hotel_status="available",
        weather_status="available",
        errors=["FlightAgent: Flight API failed"],
    )

    def fake_plan_trip(message):
        return partial_plan

    monkeypatch.setattr(
        "api.routes.travel.travel_service.plan_trip",
        fake_plan_trip,
    )

    response = client.post(
        "/travel/plan",
        json={
            "current_location": "Delhi",
            "origin": "Delhi",
            "destination": "Tokyo",
            "days": 7,
            "budget": 50000,
            "travelers": 2,
            "preference": "cheap flights",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["destination"] == "Tokyo"

    # Flight failed
    assert data["flights"] is None
    assert data["flight_status"] == "unavailable"

    # Other services remain available
    assert data["hotel_status"] == "available"
    assert data["weather_status"] == "available"

    # Error is exposed to the client
    assert len(data["errors"]) == 1
    assert "FlightAgent" in data["errors"][0]
    assert "Flight API failed" in data["errors"][0]

def test_plan_trip_handles_unexpected_application_error(monkeypatch):

    def fake_plan_trip(message):
        raise RuntimeError("Unexpected planning failure")

    monkeypatch.setattr(
        "api.routes.travel.travel_service.plan_trip",
        fake_plan_trip,
    )

    response = client.post(
        "/travel/plan",
        json={
            "current_location": "Delhi",
            "origin": "Delhi",
            "destination": "Tokyo",
            "days": 7,
            "budget": 50000,
            "travelers": 2,
        },
    )

    assert response.status_code == 500

    data = response.json()

    assert data["detail"] == "Travel planning failed."