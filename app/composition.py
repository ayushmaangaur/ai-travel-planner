from agents.root_agent import RootTravelAgent
from a2a.router import A2ARouter
from a2a.local_transport import LocalA2ATransport
from a2a.http_transport import HTTPA2ATransport

from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.weather_agent import WeatherAgent


def create_local_agent() -> RootTravelAgent:
    """
    Create a RootTravelAgent using local in-process A2A communication.
    """

    flight_agent = FlightAgent()
    hotel_agent = HotelAgent()
    weather_agent = WeatherAgent()

    router = A2ARouter(
        flight_agent=flight_agent,
        hotel_agent=hotel_agent,
        weather_agent=weather_agent,
    )

    transport = LocalA2ATransport(router)

    return RootTravelAgent(
        a2a_transport=transport
    )


def create_http_agent(
    server_url: str,
    timeout: float = 10.0,
) -> RootTravelAgent:
    """
    Create a RootTravelAgent using HTTP-based A2A communication.
    """

    transport = HTTPA2ATransport(
        base_url=server_url,
        timeout=timeout,
    )

    return RootTravelAgent(
        a2a_transport=transport
    )

def create_server_app():
    """
    Create the FastAPI A2A server with its
    specialized agents and router.
    """

    from a2a.http_server import create_app

    flight_agent = FlightAgent()
    hotel_agent = HotelAgent()
    weather_agent = WeatherAgent()

    router = A2ARouter(
        flight_agent=flight_agent,
        hotel_agent=hotel_agent,
        weather_agent=weather_agent,
    )

    return create_app(router)