import json

from services.llm_service import LLMService
from models.trip import TravelRequest
from models.hotel import HotelRecommendation, HotelOption


class HotelAgent:

    def __init__(self):
        self.llm = LLMService()

    def build_prompt(self, request: TravelRequest) -> str:

        return f"""
You are a Hotel Agent.

Your job is to recommend suitable hotels based on the travel request.

Travel Request:

Destination: {request.destination}
Days: {request.days}
Travelers: {request.travelers}
Budget: {request.budget}
Preference: {request.preference}

Provide realistic hotel recommendations.

Consider:
- Hotel name
- Location
- Rating
- Price per night
- Currency
- Amenities

Return ONLY valid JSON in this format:

{{
    "destination": "{request.destination}",
    "options": [
        {{
            "name": "...",
            "location": "...",
            "rating": 4.5,
            "price_per_night": 5000,
            "currency": "INR",
            "amenities": ["WiFi", "Breakfast"]
        }}
    ]
}}
"""

    def search_hotels(self, request: TravelRequest) -> HotelRecommendation:

        prompt = self.build_prompt(request)

        response = self.llm.generate(prompt)

        data = json.loads(response)

        options = []

        for hotel in data.get("options", []):

            options.append(
                HotelOption(
                    name=hotel.get("name"),
                    location=hotel.get("location"),
                    rating=hotel.get("rating"),
                    price_per_night=hotel.get("price_per_night"),
                    currency=hotel.get("currency", "INR"),
                    amenities=hotel.get("amenities", []),
                )
            )

        selected_options = self.select_hotels(options, request)

        return HotelRecommendation(
            destination=request.destination,
            options=selected_options,
        )


    def select_hotels(
        self,
        options: list[HotelOption],
        request: TravelRequest
    ) -> list[HotelOption]:

        if request.budget is not None:
            options = [
                hotel
                for hotel in options
                if hotel.price_per_night is not None
                and hotel.price_per_night <= request.budget
            ]

        preference = (request.preference or "").lower()

        if "cheap" in preference or "budget" in preference:
            options.sort(
                key=lambda hotel:
                hotel.price_per_night
                if hotel.price_per_night is not None
                else float("inf")
            )

        elif "luxury" in preference:
            options.sort(
                key=lambda hotel:
                hotel.rating
                if hotel.rating is not None
                else 0,
                reverse=True
            )

        else:
            # Default: higher-rated hotels first
            options.sort(
                key=lambda hotel:
                hotel.rating
                if hotel.rating is not None
                else 0,
                reverse=True
            )

        return options