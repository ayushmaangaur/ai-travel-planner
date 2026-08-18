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
    hotel: str | None = None
    weather: str | None = None
    flights: list[str] = field(default_factory=list)
    estimated_cost: int | None = None