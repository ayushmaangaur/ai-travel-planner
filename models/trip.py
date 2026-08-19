from dataclasses import dataclass, field
from typing import Optional


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

    itinerary: list[str] = field(default_factory=list)

    flights: object | None = None
    hotels: object | None = None
    weather: object | None = None

    flight_status: str = "available"
    hotel_status: str = "available"
    weather_status: str = "available"

    errors: list[str] = field(default_factory=list)