from google import genai
import json

from config.settings import GEMINI_API_KEY, MODEL_NAME
from models.trip import TravelRequest


class LLMService:

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate(self, prompt: str) -> str:
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