from dataclasses import dataclass, field
from models.trip import TravelRequest


@dataclass
class ConversationSession:
    request: TravelRequest = field(default_factory=TravelRequest)