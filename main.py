from app.composition import create_local_agent


agent = create_local_agent()

while True:

    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        break

    result = agent.plan_trip(user_input)

    print("Agent:", result)