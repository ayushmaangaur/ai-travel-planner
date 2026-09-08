import json

from google import genai

from config.settings import GEMINI_API_KEY, MODEL_NAME

from models.trip import TravelRequest, DayPlan, Activity


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

    # ================================================================
    # ITINERARY GENERATION
    # ================================================================

    def generate_itinerary(
        self,
        request: TravelRequest,
        flight_recommendation=None,
        hotel_recommendation=None,
        weather_recommendation=None,
    ) -> list[DayPlan]:
        """
        Generate a destination-aware itinerary using Gemini.
        """

        prompt = self._build_itinerary_prompt(
            request=request,
            flight_recommendation=flight_recommendation,
            hotel_recommendation=hotel_recommendation,
            weather_recommendation=weather_recommendation,
        )

        response = self.generate(prompt)

        data = self._parse_json_response(response)

        if isinstance(data, dict):
            data = data.get("itinerary", [])

        if not isinstance(data, list):
            raise ValueError(
                "LLM itinerary response must contain a list of days."
            )

        return self._parse_itinerary(data, request)

    def _build_itinerary_prompt(
        self,
        request: TravelRequest,
        flight_recommendation=None,
        hotel_recommendation=None,
        weather_recommendation=None,
    ) -> str:

        destination = request.destination or "the destination"
        days = request.days or 1
        travelers = request.travelers or 1
        budget = request.budget or 0
        preference = request.preference or "general sightseeing"

        flight_context = self._format_flight_context(
            flight_recommendation
        )

        hotel_context = self._format_hotel_context(
            hotel_recommendation
        )

        weather_context = self._format_weather_context(
            weather_recommendation
        )

        return f"""
    You are an expert travel planner.

    Create a practical, destination-specific itinerary.

    TRIP REQUIREMENTS

    Destination: {destination}
    Number of days: {days}
    Number of travelers: {travelers}
    Total trip budget: INR {budget}
    Travel preferences: {preference}

    {flight_context}

    {hotel_context}

    {weather_context}

    IMPORTANT:

    - Recommend REAL attractions and places in {destination}.
    - Do NOT use generic phrases such as:
    "Explore major attractions"
    "Explore the city"
    "Local experience"
    "Evening exploration"
    - Name the actual attraction, landmark, beach, museum, market,
    neighborhood, fort, temple, viewpoint, etc.
    - Group geographically sensible attractions together.
    - Consider the traveler's preferences.
    - Consider the flight arrival time if available.
    - Activity costs are ESTIMATES in INR for the entire group.
    - Use 0 for normally free activities.
    - Do not include hotel, flight, food, or general transportation costs
    in activity estimated_cost.
    - Return exactly {days} days.
    - Return ONLY valid JSON.

    OUTPUT FORMAT:

    [
    {{
        "day": 1,
        "title": "Specific title",
        "summary": "Summary of the day",
        "morning": [
        {{
            "name": "Actual attraction",
            "description": "What the traveler will do",
            "location": "Area",
            "duration": "1-2 hours",
            "estimated_cost": 300,
            "currency": "INR"
        }}
        ],
        "afternoon": [],
        "evening": [],
        "meals": [],
        "travel_tips": [],
        "weather_note": null
    }}
    ]
    """

    # ================================================================
    # CONTEXT FORMATTERS
    # ================================================================

    def _format_flight_context(self, recommendation) -> str:
        if recommendation is None:
            return """
FLIGHT INFORMATION
No flight information is currently available.
"""

        options = getattr(recommendation, "options", [])

        if not options:
            return """
FLIGHT INFORMATION
No flight options are currently available.
"""

        lines = ["FLIGHT INFORMATION"]

        for option in options[:3]:
            lines.append(
                f"- {getattr(option, 'airline', 'Unknown airline')}"
                f" {getattr(option, 'flight_number', '') or ''}"
                f": departure {getattr(option, 'departure_time', 'unknown')},"
                f" arrival {getattr(option, 'arrival_time', 'unknown')}"
            )

        return "\n".join(lines)

    def _format_hotel_context(self, recommendation) -> str:
        if recommendation is None:
            return """
HOTEL INFORMATION
No hotel information is currently available.
"""

        options = getattr(recommendation, "options", [])

        if not options:
            return """
HOTEL INFORMATION
No hotel options are currently available.
"""

        lines = ["HOTEL INFORMATION"]

        for option in options[:3]:
            lines.append(
                f"- {getattr(option, 'name', 'Unknown hotel')}"
                f" | location: {getattr(option, 'location', 'unknown')}"
                f" | rating: {getattr(option, 'rating', 'unknown')}"
                f" | price/night: INR "
                f"{getattr(option, 'price_per_night', 'unknown')}"
            )

        return "\n".join(lines)

    def _format_weather_context(self, recommendation) -> str:
        if recommendation is None:
            return """
WEATHER INFORMATION
No weather information is currently available.
"""

        return f"""
WEATHER INFORMATION
{recommendation}
"""

    # ================================================================
    # RESPONSE PARSING
    # ================================================================

    def _parse_json_response(self, response: str):
        """
        Parse JSON returned by Gemini.

        Handles both plain JSON and JSON accidentally wrapped in
        markdown code fences.
        """

        if not response:
            raise ValueError(
                "LLM returned an empty itinerary response."
            )

        cleaned = response.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(
                f"LLM returned invalid JSON for itinerary: {e}"
            ) from e

    def _parse_itinerary(
        self,
        data: list,
        request: TravelRequest,
    ) -> list[DayPlan]:
        """
        Convert the LLM JSON response into DayPlan objects.
        """

        itinerary = []

        for index, day_data in enumerate(data, start=1):

            if not isinstance(day_data, dict):
                raise ValueError(
                    f"Invalid itinerary day at index {index}."
                )

            day_number = self._parse_int(
                day_data.get("day")
            ) or index

            morning = self._parse_activities(
                day_data.get("morning", [])
            )

            afternoon = self._parse_activities(
                day_data.get("afternoon", [])
            )

            evening = self._parse_activities(
                day_data.get("evening", [])
            )

            meals = self._parse_string_list(
                day_data.get("meals", [])
            )

            travel_tips = self._parse_string_list(
                day_data.get("travel_tips", [])
            )

            weather_note = day_data.get("weather_note")

            if weather_note is not None:
                weather_note = str(weather_note)

            itinerary.append(
                DayPlan(
                    day=day_number,
                    title=str(
                        day_data.get(
                            "title",
                            f"Day {day_number}",
                        )
                    ),
                    summary=str(
                        day_data.get(
                            "summary",
                            "",
                        )
                    ),
                    morning=morning,
                    afternoon=afternoon,
                    evening=evening,
                    meals=meals,
                    travel_tips=travel_tips,
                    weather_note=weather_note,
                )
            )

        return itinerary

    def _parse_activities(self, activities) -> list[Activity]:
        """
        Convert LLM activity dictionaries into Activity objects.
        """

        if not isinstance(activities, list):
            return []

        parsed = []

        for activity in activities:

            if not isinstance(activity, dict):
                continue

            name = activity.get("name")

            if not name:
                continue

            parsed.append(
                Activity(
                    name=str(name),
                    description=str(
                        activity.get(
                            "description",
                            "",
                        )
                    ),
                    location=self._optional_string(
                        activity.get("location")
                    ),
                    duration=self._optional_string(
                        activity.get("duration")
                    ),
                    estimated_cost=self._parse_float(
                        activity.get("estimated_cost")
                    ),
                    currency=str(
                        activity.get(
                            "currency",
                            "INR",
                        )
                    ),
                )
            )

        return parsed

    @staticmethod
    def _parse_string_list(value) -> list[str]:
        if not isinstance(value, list):
            return []

        return [
            str(item)
            for item in value
            if item is not None
        ]

    @staticmethod
    def _optional_string(value):
        if value is None:
            return None

        return str(value)

    # ================================================================
    # VALUE PARSERS
    # ================================================================

    @staticmethod
    def _parse_int(value):
        """
        Safely convert an LLM-produced value to int.

        Examples:
            7 -> 7
            "7" -> 7
            "7 days" -> 7
        """

        if value is None:
            return None

        if isinstance(value, bool):
            return None

        try:
            return int(float(value))

        except (TypeError, ValueError):

            if isinstance(value, str):
                digits = ""

                for char in value:
                    if char.isdigit() or char == ".":
                        digits += char
                    elif digits:
                        break

                try:
                    return int(float(digits))

                except (ValueError, TypeError):
                    return None

            return None

    @staticmethod
    def _parse_float(value):
        """
        Safely convert an LLM-produced value to float.

        Examples:
            50000 -> 50000.0
            "50000" -> 50000.0
            "50000 INR" -> 50000.0
            "₹1,500" -> 1500.0
        """

        if value is None:
            return None

        if isinstance(value, bool):
            return None

        try:
            return float(value)

        except (TypeError, ValueError):
            pass

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
                pass

        return None