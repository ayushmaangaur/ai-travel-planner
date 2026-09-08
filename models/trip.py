from dataclasses import dataclass, field
from typing import Optional
from models.budget import OptimizationAction

@dataclass
class TravelRequest:
    current_location: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[str] = None
    days: Optional[int] = None
    budget: Optional[float] = None
    travelers: Optional[int] = None
    preference: Optional[str] = None


@dataclass
class Activity:
    name: str
    description: str
    location: Optional[str] = None
    duration: Optional[str] = None
    estimated_cost: Optional[float] = None
    currency: str = "INR"


@dataclass
class DayPlan:
    day: int
    title: str
    summary: str

    morning: list[Activity] = field(default_factory=list)
    afternoon: list[Activity] = field(default_factory=list)
    evening: list[Activity] = field(default_factory=list)

    meals: list[str] = field(default_factory=list)

    travel_tips: list[str] = field(default_factory=list)

    weather_note: Optional[str] = None


@dataclass
class TravelPlan:
    destination: str

    itinerary: list[DayPlan] = field(default_factory=list)

    flights: object | None = None
    hotels: object | None = None
    weather: object | None = None

    budget_breakdown: object | None = None
    optimization_actions: list[OptimizationAction] = field(
        default_factory=list
    )

    flight_status: str = "available"
    hotel_status: str = "available"
    weather_status: str = "available"

    errors: list[str] = field(default_factory=list)