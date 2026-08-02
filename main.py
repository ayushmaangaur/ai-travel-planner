from agents.root_agent import RootTravelAgent

agent = RootTravelAgent()

request = agent.plan_trip(
    input("You: ")
)

print(request)