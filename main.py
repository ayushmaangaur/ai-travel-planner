from agents.flight_agent import FlightAgent
from models.trip import TravelRequest


request = TravelRequest(
    origin="Delhi",
    destination="Tokyo",
    days=7,
    budget=100000,
    travelers=2
)

agent = FlightAgent()

result = agent.search_flights(request)

print(result)