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


class TravelPlanResponse(BaseModel):

    destination: str
    itinerary: list[str]

    flights: object | None = None
    hotels: object | None = None
    weather: object | None = None

    flight_status: str
    hotel_status: str
    weather_status: str

    errors: list[str]