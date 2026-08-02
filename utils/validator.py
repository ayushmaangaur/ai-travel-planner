from models.trip import TravelRequest


class TravelRequestValidator:

    REQUIRED_FIELDS = [
        "destination",
        "days",
        "budget",
        "travelers",
    ]

    @staticmethod
    def validate(request: TravelRequest):

        missing_fields = []

        for field in TravelRequestValidator.REQUIRED_FIELDS:

            if getattr(request, field) is None:
                missing_fields.append(field)

        return missing_fields