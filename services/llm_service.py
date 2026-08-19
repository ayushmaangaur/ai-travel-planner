from google import genai
import json
import re

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

    def normalize_budget(self, value):

        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        value = str(value).lower().strip()
        value = value.replace("₹", "").replace(",", "").replace("rs", "").strip()

        if value.endswith("k"):
            return float(value[:-1]) * 1000

        try:
            return float(value)
        except ValueError:
            return None

    def normalize_days(self, value):

        if value is None:
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value)

        match = re.search(r"\d+", str(value))

        if match:
            return int(match.group())

        return None

    def normalize_travelers(self, value):

        if value is None:
            return None

        if isinstance(value, (int, float)):
            return int(value)

        value = str(value).lower().strip()

        if "alone" in value or "myself" in value:
            return 1

        match = re.search(r"\d+", value)

        if match:
            return int(match.group())

        return None

    def parse_travel_request(self, prompt: str) -> TravelRequest:

        response = self.generate(prompt)

        data = json.loads(response)

        budget = self.normalize_budget(data.get("budget"))
        days = self.normalize_days(data.get("days"))
        travelers = self.normalize_travelers(data.get("travelers"))

        return TravelRequest(
            current_location=data.get("current_location"),
            origin=data.get("origin"),
            destination=data.get("destination"),
            days=days,
            budget=budget,
            travelers=travelers,
            preference=data.get("preference"),
        )