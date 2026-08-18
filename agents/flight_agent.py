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

        return FlightRecommendation(
            origin=data.get("origin"),
            destination=data.get("destination"),
            options=options,
        )