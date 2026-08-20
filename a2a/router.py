from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.weather_agent import WeatherAgent

from a2a.messages import (
    A2ARequest,
    A2AResponse,
)


class A2ARouter:
    """
    Routes A2A requests from RootTravelAgent
    to the appropriate specialized agent.

    The router does not call Gemini itself.
    Gemini remains inside the specialized agents.
    """

    def __init__(
        self,
        flight_agent=None,
        hotel_agent=None,
        weather_agent=None,
    ):
        self.flight_agent = flight_agent or FlightAgent()
        self.hotel_agent = hotel_agent or HotelAgent()
        self.weather_agent = weather_agent or WeatherAgent()

    def send(self, message: A2ARequest) -> A2AResponse:
        """
        Route one A2A request to the correct specialized agent.
        """

        try:

            if message.task == "search_flights":

                result = self.flight_agent.search_flights(
                    message.payload
                )

            elif message.task == "search_hotels":

                result = self.hotel_agent.search_hotels(
                    message.payload
                )

            elif message.task == "get_weather":

                result = self.weather_agent.get_weather(
                    message.payload
                )

            else:
                # This should normally be unreachable because
                # A2ARequest validates the task before routing.
                return A2AResponse(
                    sender="A2ARouter",
                    recipient=message.sender,
                    success=False,
                    result=None,
                    error=f"Unsupported task: {message.task}",
                )

            return A2AResponse(
                sender=message.recipient,
                recipient=message.sender,
                success=True,
                result=result,
                error=None,
            )

        except Exception as e:

            return A2AResponse(
                sender=message.recipient,
                recipient=message.sender,
                success=False,
                result=None,
                error=str(e),
            )