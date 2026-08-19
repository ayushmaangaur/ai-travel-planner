from agents.weather_agent import WeatherAgent
from models.trip import TravelRequest


request = TravelRequest(
    origin="Delhi",
    destination="Tokyo",
    days=7,
    budget=50000,
    travelers=2,
    preference="non-stop"
)

agent = WeatherAgent()

result = agent.get_weather(request)

print(result)