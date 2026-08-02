from services.llm_service import LLMService
from prompts.system_prompts import ROOT_AGENT_PROMPT
from utils.validator import TravelRequestValidator
from models.session import ConversationSession


class RootTravelAgent:

    def __init__(self):
        self.llm = LLMService()
        self.system_prompt = ROOT_AGENT_PROMPT
        self.session = ConversationSession()

    def build_prompt(self, user_request: str) -> str:

        request = self.session.request

        return f"""
{self.system_prompt}

Current Travel Request:

Destination: {request.destination}
Days: {request.days}
Budget: {request.budget}
Travelers: {request.travelers}
Preference: {request.preference}

New User Message:

{user_request}
"""

    def ask_for_missing_information(self, missing_fields: list[str]) -> str:

        questions = {
            "destination": "📍 Where would you like to travel?",
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

        prompt = self.build_prompt(user_request)

        new_request = self.llm.parse_travel_request(prompt)

        self.session.update_request(new_request)

        request = self.session.request

        missing_fields = TravelRequestValidator.validate(request)

        if missing_fields:
            return self.ask_for_missing_information(missing_fields)

        return request