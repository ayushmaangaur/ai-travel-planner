from dataclasses import dataclass, field


@dataclass
class FlightOption:
    airline: str
    flight_number: str | None = None
    departure_airport: str | None = None
    arrival_airport: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    duration: str | None = None
    stops: int = 0
    price: float | None = None
    currency: str = "INR"


@dataclass
class FlightRecommendation:
    origin: str
    destination: str
    options: list[FlightOption] = field(default_factory=list)