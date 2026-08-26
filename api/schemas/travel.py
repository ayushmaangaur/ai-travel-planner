from pydantic import BaseModel

from typing import Optional


class TravelRequestSchema(BaseModel):

    current_location: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    days: Optional[int] = None
    budget: Optional[float] = None
    travelers: Optional[int] = None
    preference: Optional[str] = None


# ============================================================
# Flight API Schemas
# ============================================================

class FlightOptionSchema(BaseModel):

    airline: str
    flight_number: Optional[str] = None
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    duration: Optional[str] = None
    stops: int = 0
    price: Optional[float] = None
    currency: str = "INR"


class FlightRecommendationSchema(BaseModel):

    origin: str
    destination: str
    options: list[FlightOptionSchema]


# ============================================================
# Hotel API Schemas
# ============================================================

class HotelOptionSchema(BaseModel):

    name: str
    location: str
    rating: float
    price_per_night: float
    currency: str
    amenities: list[str]


class HotelRecommendationSchema(BaseModel):

    destination: str
    options: list[HotelOptionSchema]


# ============================================================
# Weather API Schemas
# ============================================================

class WeatherDaySchema(BaseModel):

    date: str
    condition: str
    temperature: str
    precipitation: str


class WeatherRecommendationSchema(BaseModel):

    destination: str
    forecast: list[WeatherDaySchema]


# ============================================================
# Travel Plan API Response
# ============================================================

class TravelPlanResponse(BaseModel):

    destination: str
    itinerary: list[str]

    flights: Optional[FlightRecommendationSchema] = None
    hotels: Optional[HotelRecommendationSchema] = None
    weather: Optional[WeatherRecommendationSchema] = None

    flight_status: str
    hotel_status: str
    weather_status: str

    errors: list[str]