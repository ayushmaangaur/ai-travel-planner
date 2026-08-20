import json

from services.llm_service import LLMService
from models.trip import TravelRequest
from models.weather import WeatherRecommendation, WeatherDay


class WeatherAgent:

    def __init__(self):
        self.llm = LLMService()

    def build_prompt(self, request: TravelRequest) -> str:

        return f"""
You are a Weather Agent in an AI Travel Planner.

Provide a weather forecast for the destination.

Travel Request:

Destination: {request.destination}
Days: {request.days}

Generate a forecast that can be used by an itinerary planner.

Consider:
- Date or day
- Weather condition
- Temperature
- Precipitation probability

IMPORTANT:
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include explanations.
- forecast MUST be a JSON list.
- Each forecast item must be a JSON object.

Return exactly this structure:

{{
    "destination": "{request.destination}",
    "forecast": [
        {{
            "date": "Day 1",
            "condition": "...",
            "temperature": "...",
            "precipitation": "..."
        }}
    ]
}}
"""

    def get_weather(
        self,
        request: TravelRequest
    ) -> WeatherRecommendation:

        prompt = self.build_prompt(request)

        response = self.llm.generate(prompt)

        try:
            data = json.loads(response)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(
                f"WeatherAgent received invalid JSON: {e}"
            ) from e

        if not isinstance(data, dict):
            raise ValueError(
                "WeatherAgent response must be a JSON object"
            )

        raw_forecast = data.get("forecast", [])

        if not isinstance(raw_forecast, list):
            raise ValueError(
                "WeatherAgent forecast must be a list"
            )

        forecast = []

        for day in raw_forecast:

            if not isinstance(day, dict):
                continue

            forecast.append(
                WeatherDay(
                    date=day.get("date"),
                    condition=day.get("condition"),
                    temperature=day.get("temperature"),
                    precipitation=day.get("precipitation"),
                )
            )

        return WeatherRecommendation(
            destination=data.get(
                "destination",
                request.destination
            ),
            forecast=forecast,
        )