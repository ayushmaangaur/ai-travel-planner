from dataclasses import dataclass


@dataclass
class HotelOption:
    name: str
    location: str
    rating: float
    price_per_night: float
    currency: str
    amenities: list[str]


@dataclass
class HotelRecommendation:
    destination: str
    options: list[HotelOption]