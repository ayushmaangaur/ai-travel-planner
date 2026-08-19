import json

from services.llm_service import LLMService
from models.trip import TravelRequest
from models.weather import WeatherRecommendation, WeatherDay


class WeatherAgent:

    def __init__(self):
        self.llm = LLMService()

    def build_prompt(self, request: TravelRequest) -> str:

        return f"""
You are a Weather Agent.

Your job is to provide a weather forecast for the user's trip.

Travel Request:

Destination: {request.destination}
Days: {request.days}

Provide a weather forecast for each day of the trip.

Consider:
- Date/day
- Weather condition
- Temperature
- Precipitation probability

Return ONLY valid JSON in this format:

{{
    "destination": "{request.destination}",
    "forecast": [
        {{
            "date": "...",
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

        try:
            prompt = self.build_prompt(request)
            response = self.llm.generate(prompt)

            data = json.loads(response)

            if not isinstance(data, dict):
                data = {}

        except (json.JSONDecodeError, TypeError, ValueError):
            data = {}

        raw_forecast = data.get("forecast", [])

        if not isinstance(raw_forecast, list):
            raw_forecast = []

        forecast = []

        for day in raw_forecast:

            if not isinstance(day, dict):
                continue

            forecast.append(
                WeatherDay(
                    date=day.get("date", "Unknown"),
                    condition=day.get("condition", "Unknown"),
                    temperature=day.get("temperature", "Unknown"),
                    precipitation=day.get("precipitation", "Unknown"),
                )
            )

        return WeatherRecommendation(
            destination=request.destination,
            forecast=forecast,
        )