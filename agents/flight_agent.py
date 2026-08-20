import json

from services.llm_service import LLMService
from models.trip import TravelRequest
from models.flight import FlightRecommendation, FlightOption


class FlightAgent:

    def __init__(self):
        self.llm = LLMService()

    def build_prompt(self, request: TravelRequest) -> str:

        return f"""
You are a Flight Agent in an AI Travel Planner.

Your job is to recommend suitable flights based on the travel request.

Travel Request:

Origin: {request.origin}
Destination: {request.destination}
Travelers: {request.travelers}
Budget: {request.budget}
Preference: {request.preference}

Generate realistic flight recommendations.

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

IMPORTANT:
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include explanations.
- Return multiple options when possible.
- Prices must be numeric.
- Stops must be numeric.

Return exactly this structure:

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

    def search_flights(
        self,
        request: TravelRequest
    ) -> FlightRecommendation:

        prompt = self.build_prompt(request)

        # Gemini is the source of flight recommendations.
        # There is intentionally no hardcoded fallback here.
        response = self.llm.generate(prompt)

        try:
            data = json.loads(response)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(
                f"FlightAgent received invalid JSON: {e}"
            ) from e

        if not isinstance(data, dict):
            raise ValueError(
                "FlightAgent response must be a JSON object"
            )

        raw_options = data.get("options", [])

        if not isinstance(raw_options, list):
            raise ValueError(
                "FlightAgent options must be a list"
            )

        options = []

        for flight in raw_options:

            if not isinstance(flight, dict):
                continue

            # -----------------------------
            # Parse price
            # -----------------------------

            price = flight.get("price")

            try:
                if price is not None:
                    price = float(price)
            except (TypeError, ValueError):
                price = None

            # -----------------------------
            # Parse stops
            # -----------------------------

            stops = flight.get("stops", 0)

            try:
                stops = int(stops)
            except (TypeError, ValueError):
                stops = 0

            # -----------------------------
            # Build FlightOption
            # -----------------------------

            options.append(
                FlightOption(
                    airline=flight.get("airline"),
                    flight_number=flight.get("flight_number"),
                    departure_airport=flight.get(
                        "departure_airport"
                    ),
                    arrival_airport=flight.get(
                        "arrival_airport"
                    ),
                    departure_time=flight.get(
                        "departure_time"
                    ),
                    arrival_time=flight.get(
                        "arrival_time"
                    ),
                    duration=flight.get("duration"),
                    stops=stops,
                    price=price,
                    currency=flight.get(
                        "currency",
                        "INR"
                    ),
                )
            )

        # Deterministic application-side filtering/ranking.
        selected_options = self.select_flights(
            options,
            request
        )

        return FlightRecommendation(
            origin=data.get(
                "origin",
                request.origin
            ),
            destination=data.get(
                "destination",
                request.destination
            ),
            options=selected_options,
        )

    def select_flights(
        self,
        options: list[FlightOption],
        request: TravelRequest
    ) -> list[FlightOption]:

        # -----------------------------
        # Budget filtering
        # -----------------------------

        if request.budget is not None:

            options = [
                flight
                for flight in options
                if (
                    flight.price is not None
                    and flight.price <= request.budget
                )
            ]

        preference = (
            request.preference or ""
        ).lower()

        # -----------------------------
        # Non-stop preference
        # -----------------------------

        if (
            "non-stop" in preference
            or "nonstop" in preference
        ):

            options.sort(
                key=lambda flight: (
                    flight.stops,
                    flight.price
                    if flight.price is not None
                    else float("inf")
                )
            )

        # -----------------------------
        # Cheapest preference
        # -----------------------------

        elif (
            "cheapest" in preference
            or "cheap" in preference
        ):

            options.sort(
                key=lambda flight:
                flight.price
                if flight.price is not None
                else float("inf")
            )

        # -----------------------------
        # Default ranking
        # -----------------------------

        else:

            options.sort(
                key=lambda flight: (
                    flight.stops,
                    flight.price
                    if flight.price is not None
                    else float("inf")
                )
            )

        return options