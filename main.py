from agents.root_agent import RootTravelAgent

agent = RootTravelAgent()

while True:
    user = input("\nYou: ")

    if user.lower() == "exit":
        break

    response = agent.plan_trip(user)

    print("\nAgent:")
    print(response)