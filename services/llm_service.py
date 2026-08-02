from google import genai

from config.settings import GEMINI_API_KEY, MODEL_NAME


class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate_response(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        return response.text