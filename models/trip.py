from dataclasses import dataclass
from typing import Optional


@dataclass
class TravelRequest:
    destination: Optional[str] = None
    days: Optional[int] = None
    budget: Optional[int] = None
    travelers: Optional[int] = None
    preference: Optional[str] = None