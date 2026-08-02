from agents.root_agent import RootTravelAgent


def main():

    agent = RootTravelAgent()

    while True:

        user = input("\nYou: ")

        if user.lower() == "exit":
            break

        response = agent.plan_trip(user)

        print("\nTravel Agent:\n")
        print(response)


if __name__ == "__main__":
    main()