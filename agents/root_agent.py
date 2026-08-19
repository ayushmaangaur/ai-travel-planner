import json
from services.llm_service import LLMService
from prompts.system_prompts import ROOT_AGENT_PROMPT
from utils.validator import TravelRequestValidator
from models.session import ConversationSession
from models.trip import TravelPlan, TravelRequest

from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.weather_agent import WeatherAgent

from utils.itinerary_generator import ItineraryGenerator


class RootTravelAgent:

    def __init__(self):
        self.llm = LLMService()
        self.system_prompt = ROOT_AGENT_PROMPT
        self.session = ConversationSession()

        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.weather_agent = WeatherAgent()
        self.itinerary_generator = ItineraryGenerator()

    def build_prompt(self, user_request: str) -> str:

        request = self.session.request

        return f"""
{self.system_prompt}

Current Travel Request:

Current Location: {request.current_location}
Origin: {request.origin}
Destination: {request.destination}
Days: {request.days}
Budget: {request.budget}
Travelers: {request.travelers}
Preference: {request.preference}

New User Message:

{user_request}
"""

    def ask_for_missing_information(
        self,
        missing_fields: list[str]
    ) -> str:

        questions = {
            "current_location": "📍 Where are you currently located?",
            "origin": "✈️ Where would you like your journey to start from?",
            "destination": "🌍 Where would you like to travel?",
            "days": "📅 How many days are you planning to stay?",
            "budget": "💰 What's your approximate budget?",
            "travelers": "👥 How many people are travelling?",
        }

        return "\n".join(
            questions[field]
            for field in missing_fields
            if field in questions
        )

    def generate_itinerary(
        self,
        request: TravelRequest,
        flight_result,
        hotel_result,
        weather_result,
    ) -> list[str]:

        prompt = f"""
    You are an expert travel itinerary planner.

    Create a practical day-by-day itinerary for this trip.

    TRAVEL REQUEST:
    Destination: {request.destination}
    Origin: {request.origin}
    Days: {request.days}
    Travelers: {request.travelers}
    Budget: {request.budget}
    Preference: {request.preference}

    FLIGHTS:
    {flight_result}

    HOTELS:
    {hotel_result}

    WEATHER:
    {weather_result}

    INSTRUCTIONS:

    - Generate EXACTLY {request.days} days.
    - Generate one itinerary string for every day.
    - Every string MUST start with "Day X:".
    - Consider the hotel location when planning activities.
    - Consider the weather forecast when deciding outdoor activities.
    - Consider flight arrival information for Day 1.
    - Do not invent flight or hotel details.
    - Keep activities realistic and varied.
    - Do not repeat the same activities every day.
    - Return ONLY JSON.
    - Do not use Markdown.
    - Do not add explanations before or after the JSON.

    The response MUST have exactly this structure:

    {{
        "itinerary": [
            "Day 1: ...",
            "Day 2: ...",
            "Day 3: ..."
        ]
    }}
    """

        try:
            response = self.llm.generate(prompt)

            print("ITINERARY LLM RESPONSE:")
            print(response)

            response = response.strip()

            # Remove Markdown code fences if Gemini adds them
            if response.startswith("```"):
                lines = response.splitlines()

                if lines and lines[0].startswith("```"):
                    lines = lines[1:]

                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]

                response = "\n".join(lines).strip()

            data = json.loads(response)

            if not isinstance(data, dict):
                raise ValueError("Itinerary response is not a JSON object")

            itinerary = data.get("itinerary")

            if not isinstance(itinerary, list):
                raise ValueError(
                    "Itinerary response does not contain a valid itinerary list"
                )

            # Remove invalid entries
            itinerary = [
                str(item).strip()
                for item in itinerary
                if item is not None and str(item).strip()
            ]

            # The LLM MUST produce exactly the requested number of days
            if len(itinerary) != request.days:
                raise ValueError(
                    f"Expected {request.days} itinerary days, "
                    f"but received {len(itinerary)}"
                )

            return itinerary

        except Exception as e:
            print(f"LLM itinerary generation failed: {e}")

            # -----------------------------------
            # Deterministic fallback
            # -----------------------------------

            print("Using fallback itinerary.")

            days = request.days or 1

            fallback = []

            for day in range(1, days + 1):

                if day == 1:
                    activity = (
                        f"Arrive in {request.destination}, "
                        "check in to the hotel, rest, and explore the nearby area."
                    )

                elif day == days:
                    activity = (
                        f"Enjoy a relaxed final day in {request.destination}, "
                        "do some shopping or sightseeing, and prepare for departure."
                    )

                else:
                    activity = (
                        f"Explore attractions and local experiences in "
                        f"{request.destination}, while enjoying local food and "
                        "taking breaks throughout the day."
                    )

                fallback.append(f"Day {day}: {activity}")

            return fallback

    def plan_trip(self, user_request: str):

        # -----------------------------
        # Parse user message
        # -----------------------------

        prompt = self.build_prompt(user_request)

        new_request = self.llm.parse_travel_request(prompt)

        self.session.update_request(new_request)

        request = self.session.request

        # -----------------------------
        # Determine origin
        # -----------------------------

        if request.current_location and not request.origin:
            request.origin = request.current_location

        # -----------------------------
        # Validate request
        # -----------------------------

        missing_fields = TravelRequestValidator.validate(request)

        if missing_fields:
            return self.ask_for_missing_information(missing_fields)

        # -----------------------------
        # Call specialized agents
        # -----------------------------

        flight_result = None
        hotel_result = None
        weather_result = None

        flight_status = "available"
        hotel_status = "available"
        weather_status = "available"

        errors = []

        # Flight Agent
        try:
            flight_result = self.flight_agent.search_flights(request)

        except Exception as e:
            print(f"FlightAgent failed: {e}")
            errors.append(f"FlightAgent: Flight service unavailable: {e}")
            flight_result = None
            flight_status = "unavailable"

        # Hotel Agent
        try:
            hotel_result = self.hotel_agent.search_hotels(request)

        except Exception as e:
            print(f"HotelAgent failed: {e}")
            errors.append(f"HotelAgent: Hotel service unavailable: {e}")
            hotel_result = None
            hotel_status = "unavailable"     

        # Weather Agent
        try:
            weather_result = self.weather_agent.get_weather(request)

        except Exception as e:
            print(f"WeatherAgent failed: {e}")
            errors.append(f"WeatherAgent: Weather service unavailable: {e}")
            weather_result = None
            weather_status = "unavailable"

        # -----------------------------
        # Generate itinerary
        # -----------------------------

        try:
            itinerary = self.itinerary_generator.generate(
                request,
                flight_result,
                hotel_result,
                weather_result
            )

        except Exception as e:
            print(f"Itinerary generation failed: {e}")
            errors.append(f"Itinerary service unavailable: {e}")
            itinerary = []

        # -----------------------------
        # Build final TravelPlan
        # -----------------------------

        return TravelPlan(
            destination=request.destination,
            itinerary=itinerary,
            flights=flight_result,
            hotels=hotel_result,
            weather=weather_result,
            flight_status=flight_status,
            hotel_status=hotel_status,
            weather_status=weather_status,
            errors=errors,
        )