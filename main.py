from agents.root_agent import RootTravelAgent


agent = RootTravelAgent()

while True:

    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        break

    result = agent.plan_trip(user_input)

    print("Agent:", result)