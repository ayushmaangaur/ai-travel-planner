from dataclasses import dataclass


@dataclass
class TravelRequest:
    destination: str
    days: int
    budget: int
    travelers: int