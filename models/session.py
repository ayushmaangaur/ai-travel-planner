from dataclasses import dataclass, field, fields

from models.trip import TravelRequest


@dataclass
class ConversationSession:
    request: TravelRequest = field(default_factory=TravelRequest)

    def update_request(self, new_request: TravelRequest):

        for field_info in fields(TravelRequest):

            new_value = getattr(new_request, field_info.name)

            if new_value is not None:

                setattr(
                    self.request,
                    field_info.name,
                    new_value
                )