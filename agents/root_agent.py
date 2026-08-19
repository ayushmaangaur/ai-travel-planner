from services.llm_service import LLMService
from prompts.system_prompts import ROOT_AGENT_PROMPT
from utils.validator import TravelRequestValidator
from models.session import ConversationSession
from models.trip import TravelPlan

from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.weather_agent import WeatherAgent


class RootTravelAgent:

    def __init__(self):
        self.llm = LLMService()
        self.system_prompt = ROOT_AGENT_PROMPT
        self.session = ConversationSession()

        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.weather_agent = WeatherAgent()

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
        # Build final TravelPlan
        # -----------------------------

        return TravelPlan(
            destination=request.destination,
            flights=flight_result,
            hotels=hotel_result,
            weather=weather_result,
            flight_status=flight_status,
            hotel_status=hotel_status,
            weather_status=weather_status,
            errors=errors,
        )