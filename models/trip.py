from dataclasses import dataclass, field
from typing import Optional

from models.flight import FlightRecommendation
from models.hotel import HotelRecommendation
from models.weather import WeatherRecommendation


@dataclass
class TravelRequest:
    current_location: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    days: Optional[int] = None
    budget: Optional[float] = None
    travelers: Optional[int] = None
    preference: Optional[str] = None


@dataclass
class TravelPlan:
    destination: str
    flights: FlightRecommendation | None = None
    hotels: HotelRecommendation | None = None
    weather: WeatherRecommendation | None = None
    errors: list[str] = field(default_factory=list)