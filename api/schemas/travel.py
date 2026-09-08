from typing import Optional
from pydantic import BaseModel, Field


# ============================================================
# REQUEST
# ============================================================

class TravelRequestSchema(BaseModel):
    message: Optional[str] = None
    current_location: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    days: Optional[int] = None
    budget: Optional[float] = None
    travelers: Optional[int] = None
    preference: Optional[str] = None


# ============================================================
# ITINERARY
# ============================================================

class ActivityResponse(BaseModel):
    name: str
    description: str
    location: Optional[str] = None
    duration: Optional[str] = None
    estimated_cost: Optional[float] = None
    currency: str = "INR"


class DayPlanResponse(BaseModel):
    day: int
    title: str
    summary: str
    morning: list[ActivityResponse] = Field(default_factory=list)
    afternoon: list[ActivityResponse] = Field(default_factory=list)
    evening: list[ActivityResponse] = Field(default_factory=list)
    meals: list[str] = Field(default_factory=list)
    travel_tips: list[str] = Field(default_factory=list)
    weather_note: Optional[str] = None


# ============================================================
# BUDGET
# ============================================================

class OptimizationActionResponse(BaseModel):
    type: str
    action: str
    description: str
    previous_cost: float = 0.0
    new_cost: float = 0.0
    savings: float = 0.0


class BudgetBreakdownResponse(BaseModel):
    budget: float
    flights: float
    hotels: float
    activities: float
    food: float
    transport: float
    total: float
    remaining: float
    within_budget: bool
    budget_used_percentage: float
    optimization_actions: list[OptimizationActionResponse] = []


# ============================================================
# TRAVEL PLAN RESPONSE
# ============================================================

class TravelPlanResponse(BaseModel):
    destination: str

    itinerary: list[DayPlanResponse]

    flights: object | None = None
    hotels: object | None = None
    weather: object | None = None

    budget_breakdown: BudgetBreakdownResponse | None = None

    optimization_actions: list[OptimizationActionResponse] = Field(
        default_factory=list
    )

    flight_status: str
    hotel_status: str
    weather_status: str

    errors: list[str]