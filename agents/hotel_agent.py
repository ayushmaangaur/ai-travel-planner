import json

from services.llm_service import LLMService
from models.trip import TravelRequest
from models.hotel import HotelRecommendation, HotelOption


class HotelAgent:

    def __init__(self):
        self.llm = LLMService()

    def build_prompt(self, request: TravelRequest) -> str:

        return f"""
You are a Hotel Agent in an AI Travel Planner.

Your job is to recommend suitable hotels based on the travel request.

Travel Request:

Destination: {request.destination}
Days: {request.days}
Travelers: {request.travelers}
Budget: {request.budget}
Preference: {request.preference}

Generate realistic hotel recommendations.

Consider:
- Hotel name
- Location
- Rating
- Price per night
- Currency
- Amenities

IMPORTANT:
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include explanations.
- Prices must be numeric.
- Rating must be numeric.

Return exactly this structure:

{{
    "destination": "{request.destination}",
    "options": [
        {{
            "name": "...",
            "location": "...",
            "rating": 4.0,
            "price_per_night": 0,
            "currency": "INR",
            "amenities": [
                "..."
            ]
        }}
    ]
}}
"""

    def search_hotels(
        self,
        request: TravelRequest
    ) -> HotelRecommendation:

        prompt = self.build_prompt(request)

        # Gemini is the source of hotel recommendations.
        # There is intentionally no hardcoded fallback here.
        response = self.llm.generate(prompt)

        try:
            data = json.loads(response)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(
                f"HotelAgent received invalid JSON: {e}"
            ) from e

        if not isinstance(data, dict):
            raise ValueError(
                "HotelAgent response must be a JSON object"
            )

        raw_options = data.get("options", [])

        if not isinstance(raw_options, list):
            raise ValueError(
                "HotelAgent options must be a list"
            )

        options = []

        for hotel in raw_options:

            if not isinstance(hotel, dict):
                continue

            # -----------------------------
            # Parse price
            # -----------------------------

            price = hotel.get(
                "price_per_night"
            )

            try:
                if price is not None:
                    price = float(price)
            except (TypeError, ValueError):
                price = None

            # -----------------------------
            # Parse rating
            # -----------------------------

            rating = hotel.get("rating")

            try:
                if rating is not None:
                    rating = float(rating)
            except (TypeError, ValueError):
                rating = None

            # -----------------------------
            # Parse amenities
            # -----------------------------

            amenities = hotel.get(
                "amenities",
                []
            )

            if not isinstance(
                amenities,
                list
            ):
                amenities = []

            options.append(
                HotelOption(
                    name=hotel.get("name"),
                    location=hotel.get("location"),
                    rating=rating,
                    price_per_night=price,
                    currency=hotel.get(
                        "currency",
                        "INR"
                    ),
                    amenities=[
                        str(item)
                        for item in amenities
                        if item is not None
                    ],
                )
            )

        # Deterministic application-side
        # budget filtering and ranking.
        selected_options = self.select_hotels(
            options,
            request
        )

        return HotelRecommendation(
            destination=data.get(
                "destination",
                request.destination
            ),
            options=selected_options,
        )

    def select_hotels(
        self,
        options: list[HotelOption],
        request: TravelRequest
    ) -> list[HotelOption]:

        if not options:
            return []

        # If either value is unavailable,
        # don't perform budget filtering.
        if (
            request.budget is None
            or request.days is None
        ):
            return options

        valid_options = []

        for hotel in options:

            # Ignore malformed hotel prices.
            if hotel.price_per_night is None:
                continue

            # Total hotel cost for the trip.
            total_cost = (
                hotel.price_per_night
                * request.days
            )

            # Keep only hotels within budget.
            if total_cost <= request.budget:
                valid_options.append(hotel)

        # Cheapest hotels first.
        valid_options.sort(
            key=lambda hotel:
            hotel.price_per_night
        )

        return valid_options