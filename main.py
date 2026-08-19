from agents.flight_agent import FlightAgent
from models.trip import TravelRequest


request = TravelRequest(
    origin="Delhi",
    destination="Tokyo",
    days=7,
    budget=50000,
    travelers=2,
    preference="non-stop"
)

agent = FlightAgent()

result = agent.search_flights(request)

print(result)