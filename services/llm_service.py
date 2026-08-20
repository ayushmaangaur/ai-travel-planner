import json

from google import genai

from config.settings import GEMINI_API_KEY, MODEL_NAME
from models.trip import TravelRequest


class LLMService:

    def __init__(self):
        """
        Create the LLM service without initializing the Gemini client.

        The actual Gemini client is created lazily inside generate().
        This keeps unit tests from accidentally initializing Gemini.
        """

        self.client = None

    def _get_client(self):
        """
        Lazily initialize and return the Gemini client.
        """

        if self.client is None:
            if not GEMINI_API_KEY:
                raise RuntimeError(
                    "GEMINI_API_KEY is not configured."
                )

            self.client = genai.Client(
                api_key=GEMINI_API_KEY
            )

        return self.client

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to Gemini and return the text response.

        Gemini is only initialized when this method is actually called.
        """

        client = self._get_client()

        print("\n===== GEMINI API CALLED =====")
        print(f"Model: {MODEL_NAME}")

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        print("===== GEMINI API RESPONSE RECEIVED =====\n")

        if response is None:
            raise ValueError(
                "Gemini returned no response."
            )

        text = getattr(response, "text", None)

        if not text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        return text.strip()

    def parse_travel_request(self, prompt: str) -> TravelRequest:
        """
        Ask Gemini to extract a structured TravelRequest from the
        user's natural-language request.
        """

        response = self.generate(prompt)

        try:
            data = json.loads(response)

        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(
                f"LLM returned invalid JSON for TravelRequest: {e}"
            ) from e

        if not isinstance(data, dict):
            raise ValueError(
                "LLM TravelRequest response must be a JSON object."
            )

        return TravelRequest(
            current_location=data.get("current_location"),
            origin=data.get("origin"),
            destination=data.get("destination"),
            days=self._parse_int(data.get("days")),
            budget=self._parse_float(data.get("budget")),
            travelers=self._parse_int(data.get("travelers")),
            preference=data.get("preference"),
        )

    @staticmethod
    def _parse_int(value):
        """
        Safely convert an LLM-produced value to int.

        Examples:
            7       -> 7
            "7"     -> 7
            "7 days" -> 7
        """

        if value is None:
            return None

        if isinstance(value, bool):
            return None

        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_float(value):
        """
        Safely convert an LLM-produced value to float.

        Examples:
            50000       -> 50000.0
            "50000"     -> 50000.0
            "50000 INR" -> 50000.0
        """

        if value is None:
            return None

        if isinstance(value, bool):
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            pass

        # Handle strings containing currency symbols/text.
        if isinstance(value, str):

            cleaned = (
                value
                .replace(",", "")
                .replace("₹", "")
                .replace("INR", "")
                .strip()
            )

            try:
                return float(cleaned)
            except ValueError:
                return None

        return None