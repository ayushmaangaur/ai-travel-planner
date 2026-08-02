from services.llm_service import LLMService
from prompts.system_prompts import ROOT_AGENT_PROMPT

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

    def plan_trip(self, user_request):

        prompt = self.build_prompt(user_request)

        return self.llm.generate_response(prompt)