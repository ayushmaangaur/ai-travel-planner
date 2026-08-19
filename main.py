from agents.root_agent import RootTravelAgent


agent = RootTravelAgent()

result = agent.plan_trip(
    input("You: ")
)

print(result)