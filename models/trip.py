from dataclasses import dataclass, field


@dataclass
class TravelRequest:
    destination: str | None = None
    days: int | None = None
    budget: int | None = None
    travelers: int | None = None
    preference: str | None = None


@dataclass
class TravelPlan:
    destination: str
    itinerary: list[str] = field(default_factory=list)
    hotel: str | None = None
    weather: str | None = None
    flights: list[str] = field(default_factory=list)
    estimated_cost: int | None = None