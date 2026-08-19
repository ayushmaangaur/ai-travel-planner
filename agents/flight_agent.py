import json
from services.llm_service import LLMService
from models.trip import TravelRequest
from models.flight import FlightRecommendation, FlightOption


class FlightAgent:

    def __init__(self):
        self.llm = LLMService()

    def build_prompt(self, request: TravelRequest) -> str:

        return f"""
You are a Flight Agent.

Your job is to recommend suitable flights based on the travel request.

Travel Request:

Origin: {request.origin}
Destination: {request.destination}
Travelers: {request.travelers}
Budget: {request.budget}
Preference: {request.preference}

Provide realistic flight recommendations.

Consider:
- Airline
- Flight number
- Departure airport
- Arrival airport
- Departure time
- Arrival time
- Duration
- Number of stops
- Price
- Currency

Return ONLY valid JSON in this format:

{{
    "origin": "{request.origin}",
    "destination": "{request.destination}",
    "options": [
        {{
            "airline": "...",
            "flight_number": "...",
            "departure_airport": "...",
            "arrival_airport": "...",
            "departure_time": "...",
            "arrival_time": "...",
            "duration": "...",
            "stops": 0,
            "price": 0,
            "currency": "INR"
        }}
    ]
}}
"""

    def search_flights(self, request: TravelRequest) -> FlightRecommendation:

        prompt = self.build_prompt(request)

        response = self.llm.generate(prompt)

        data = json.loads(response)

        options = []

        for flight in data.get("options", []):
            options.append(
                FlightOption(
                    airline=flight.get("airline"),
                    flight_number=flight.get("flight_number"),
                    departure_airport=flight.get("departure_airport"),
                    arrival_airport=flight.get("arrival_airport"),
                    departure_time=flight.get("departure_time"),
                    arrival_time=flight.get("arrival_time"),
                    duration=flight.get("duration"),
                    stops=flight.get("stops", 0),
                    price=flight.get("price"),
                    currency=flight.get("currency", "INR"),
                )
            )

        selected_options = self.select_flights(options, request)

        return FlightRecommendation(
            origin=data.get("origin"),
            destination=data.get("destination"),
            options=selected_options,
        )

    def select_flights(
        self,
        options: list[FlightOption],
        request: TravelRequest
    ) -> list[FlightOption]:

        # Filter flights that exceed the budget
        if request.budget is not None:
            options = [
                flight
                for flight in options
                if flight.price is not None
                and flight.price <= request.budget
            ]

        # Apply preference
        preference = (request.preference or "").lower()

        if "non-stop" in preference or "nonstop" in preference:
            options.sort(key=lambda flight: (
                flight.stops,
                flight.price if flight.price is not None else float("inf")
            ))

        elif "cheapest" in preference or "cheap" in preference:
            options.sort(
                key=lambda flight:
                flight.price if flight.price is not None else float("inf")
            )

        else:
            # Default: fewer stops first, then cheaper price
            options.sort(key=lambda flight: (
                flight.stops,
                flight.price if flight.price is not None else float("inf")
            ))

        return options