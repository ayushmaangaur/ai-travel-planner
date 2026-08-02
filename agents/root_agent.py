from services.llm_service import LLMService
from prompts.system_prompts import ROOT_AGENT_PROMPT

import json

from models.trip import TravelRequest

class RootTravelAgent:

    def __init__(self):
        self.llm = LLMService()
        self.system_prompt = ROOT_AGENT_PROMPT

    def build_prompt(self, user_request):

        return f"""
{self.system_prompt}

User Request:

{user_request}
"""

    def plan_trip(self, user_request: str) -> TravelRequest:

        prompt = self.build_prompt(user_request)

        response = self.llm.generate(prompt)

        data = json.loads(response)

        return TravelRequest(
            destination=data.get("destination"),
            days=data.get("days"),
            budget=data.get("budget"),
            travelers=data.get("travelers"),
            preference=data.get("preference"),
        )