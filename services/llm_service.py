from google import genai
import json

from config.settings import GEMINI_API_KEY, MODEL_NAME, USE_MOCK_LLM
from models.trip import TravelRequest


class LLMService:

    def __init__(self):
        self.mock = USE_MOCK_LLM

        if not self.mock:
            self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate(self, prompt: str) -> str:

        if self.mock:
            return self.mock_generate(prompt)

        response = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        return response.text

    def parse_travel_request(self, prompt: str) -> TravelRequest:

        response = self.generate(prompt)

        data = json.loads(response)

        return TravelRequest(
            current_location=data.get("current_location"),
            origin=data.get("origin"),
            destination=data.get("destination"),
            days=data.get("days"),
            budget=data.get("budget"),
            travelers=data.get("travelers"),
            preference=data.get("preference"),
        )

    def mock_generate(self, prompt: str) -> str:

        prompt_lower = prompt.lower()

        # Root Agent mock
        if "new user message" in prompt_lower:
            return json.dumps({
                "current_location": "Delhi",
                "origin": "Delhi",
                "destination": "Tokyo",
                "days": 7,
                "budget": 50000,
                "travelers": 2,
                "preference": "non-stop"
            })

        # Flight Agent mock
        if "flight agent" in prompt_lower:
            return json.dumps({
                "origin": "Delhi",
                "destination": "Tokyo",
                "options": [
                    {
                        "airline": "Air India",
                        "flight_number": "AI 306",
                        "departure_airport": "DEL",
                        "arrival_airport": "NRT",
                        "departure_time": "21:15",
                        "arrival_time": "08:00 (+1)",
                        "duration": "8h 15m",
                        "stops": 0,
                        "price": 45000,
                        "currency": "INR"
                    },
                    {
                        "airline": "VietJet Air",
                        "flight_number": "VJ 896",
                        "departure_airport": "DEL",
                        "arrival_airport": "NRT",
                        "departure_time": "23:50",
                        "arrival_time": "15:25 (+1)",
                        "duration": "12h 05m",
                        "stops": 1,
                        "price": 28000,
                        "currency": "INR"
                    }
                ]
            })

        # Hotel Agent mock
        if "hotel agent" in prompt_lower:
            return json.dumps({
                "destination": "Tokyo",
                "options": [
                    {
                        "name": "Tokyo Budget Hotel",
                        "location": "Shinjuku",
                        "rating": 4.1,
                        "price_per_night": 5000,
                        "currency": "INR",
                        "amenities": [
                            "Free Wi-Fi",
                            "Air Conditioning"
                        ]
                    },
                    {
                        "name": "Tokyo Premium Hotel",
                        "location": "Ginza",
                        "rating": 4.6,
                        "price_per_night": 9000,
                        "currency": "INR",
                        "amenities": [
                            "Free Wi-Fi",
                            "Restaurant",
                            "Pool"
                        ]
                    }
                ]
            })

        # Weather Agent mock
        if "weather agent" in prompt_lower:
            return json.dumps({
                "destination": "Tokyo",
                "forecast": [
                    {
                        "date": "Day 1",
                        "condition": "Sunny",
                        "temperature": "25°C",
                        "precipitation": "10%"
                    },
                    {
                        "date": "Day 2",
                        "condition": "Partly Cloudy",
                        "temperature": "24°C",
                        "precipitation": "20%"
                    },
                    {
                        "date": "Day 3",
                        "condition": "Light Rain",
                        "temperature": "22°C",
                        "precipitation": "60%"
                    }
                ]
            })

        return "{}"