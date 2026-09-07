import json

from services.llm_service import LLMService

from models.trip import (
    TravelRequest,
    DayPlan,
    Activity,
)

from models.flight import FlightRecommendation
from models.hotel import HotelRecommendation
from models.weather import WeatherRecommendation


class ItineraryAgent:

    def __init__(self):
        self.llm = LLMService()

    # =========================================================
    # PROMPT
    # =========================================================

    def build_prompt(
        self,
        request: TravelRequest,
        flights: FlightRecommendation | None,
        hotels: HotelRecommendation | None,
        weather: WeatherRecommendation | None,
    ) -> str:

        return f"""
You are an expert travel itinerary planner.

Create a practical, detailed and realistic day-by-day itinerary.

TRIP DETAILS

Origin:
{request.origin}

Destination:
{request.destination}

Number of days:
{request.days}

Number of travelers:
{request.travelers}

Budget:
{request.budget} INR

Travel preference:
{request.preference}


FLIGHT INFORMATION

{flights}


HOTEL INFORMATION

{hotels}


WEATHER INFORMATION

{weather}


REQUIREMENTS

1. Create exactly {request.days} DayPlan objects.

2. Every day must contain:
   - a meaningful title
   - a useful summary
   - morning activities
   - afternoon activities
   - evening activities

3. Activities must be specific to {request.destination}.

4. Do NOT use generic descriptions such as:
   "Explore major attractions and local experiences."

5. Recommend actual attractions, neighborhoods, landmarks,
   markets, viewpoints, cultural experiences or activities.

6. Group geographically nearby activities together to reduce
   unnecessary travel.

7. Consider the weather information when deciding outdoor
   activities.

8. Consider the traveler's budget.

9. Consider the traveler's preference.

10. Include realistic transportation/travel tips.

11. Include meal suggestions appropriate for the destination.

12. Do not invent flight or hotel information.
    Only use the provided flight and hotel information.

13. If weather information is unavailable, simply omit
    weather-specific recommendations.

14. Return ONLY valid JSON.

JSON FORMAT:

[
  {{
    "day": 1,
    "title": "Arrival and South Mumbai",
    "summary": "A relaxed first day...",
    "morning": [
      {{
        "name": "Gateway of India",
        "description": "Visit...",
        "location": "Apollo Bunder",
        "duration": "1 hour",
        "estimated_cost": 0,
        "currency": "INR"
      }}
    ],
    "afternoon": [],
    "evening": [],
    "meals": [
      "Try local seafood for lunch"
    ],
    "travel_tips": [
      "Use local trains or metro where practical"
    ],
    "weather_note": "Hot and humid; carry water."
  }}
]
"""

    # =========================================================
    # PARSE RESPONSE
    # =========================================================

    def parse_response(self, response: str) -> list[DayPlan]:

        data = json.loads(response)

        if not isinstance(data, list):
            raise ValueError(
                "ItineraryAgent response must be a JSON list"
            )

        itinerary = []

        for day_data in data:

            def parse_activities(items):

                return [
                    Activity(
                        name=item["name"],
                        description=item["description"],
                        location=item.get("location"),
                        duration=item.get("duration"),
                        estimated_cost=item.get(
                            "estimated_cost"
                        ),
                        currency=item.get(
                            "currency",
                            "INR"
                        ),
                    )
                    for item in items
                ]

            itinerary.append(
                DayPlan(
                    day=day_data["day"],
                    title=day_data["title"],
                    summary=day_data["summary"],

                    morning=parse_activities(
                        day_data.get("morning", [])
                    ),

                    afternoon=parse_activities(
                        day_data.get("afternoon", [])
                    ),

                    evening=parse_activities(
                        day_data.get("evening", [])
                    ),

                    meals=day_data.get(
                        "meals",
                        []
                    ),

                    travel_tips=day_data.get(
                        "travel_tips",
                        []
                    ),

                    weather_note=day_data.get(
                        "weather_note"
                    ),
                )
            )

        return itinerary

    # =========================================================
    # GENERATE ITINERARY
    # =========================================================

    def generate(
        self,
        request: TravelRequest,
        flights: FlightRecommendation | None,
        hotels: HotelRecommendation | None,
        weather: WeatherRecommendation | None,
    ) -> list[DayPlan]:

        prompt = self.build_prompt(
            request,
            flights,
            hotels,
            weather,
        )

        print("\n===== ITINERARY AGENT =====")

        response = self.llm.generate(prompt)

        print("===== ITINERARY GENERATED =====\n")

        itinerary = self.parse_response(response)

        # -----------------------------------------------------
        # Defensive validation
        # -----------------------------------------------------

        if len(itinerary) != request.days:
            raise ValueError(
                f"ItineraryAgent returned "
                f"{len(itinerary)} days, expected "
                f"{request.days}"
            )

        return itinerary