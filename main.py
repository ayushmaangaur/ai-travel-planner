from services.llm_service import GeminiService


def main():
    gemini = GeminiService()

    question = input("You: ")

    answer = gemini.generate_response(question)

    print("\nGemini:")
    print(answer)


if __name__ == "__main__":
    main()