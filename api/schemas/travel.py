from pydantic import BaseModel
from typing import Optional


class TravelRequestSchema(BaseModel):
    message: Optional[str] = None
    current_location: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    days: Optional[int] = None
    budget: Optional[float] = None
    travelers: Optional[int] = None
    preference: Optional[str] = None


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
    morning: list[ActivityResponse] = []
    afternoon: list[ActivityResponse] = []
    evening: list[ActivityResponse] = []
    meals: list[str] = []
    travel_tips: list[str] = []
    weather_note: Optional[str] = None


class TravelPlanResponse(BaseModel):
    destination: str
    itinerary: list[DayPlanResponse] = []
    flights: object | None = None
    hotels: object | None = None
    weather: object | None = None
    flight_status: str
    hotel_status: str
    weather_status: str
    errors: list[str]