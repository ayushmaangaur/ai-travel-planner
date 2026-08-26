from agents.root_agent import RootTravelAgent
from models.trip import TravelPlan


class TravelService:
    """
    Application-layer service for the AI Travel Planner.

    This class exposes the travel-planning use case to
    external interfaces such as APIs, CLI applications,
    or web applications.

    It does not contain agent orchestration logic.
    """

    def __init__(self, agent: RootTravelAgent):
        if agent is None:
            raise ValueError(
                "TravelService requires a RootTravelAgent"
            )

        self.agent = agent

    def plan_trip(self, message: str) -> TravelPlan:
        """
        Execute the travel-planning use case.
        """
        if not isinstance(message, str):
            raise TypeError(
                "TravelService.plan_trip expects a string"
            )

        if not message.strip():
            raise ValueError(
                "TravelService.plan_trip requires a non-empty message"
            )

        return self.agent.plan_trip(message)