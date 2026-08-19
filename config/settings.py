import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.5-flash"

USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"

if not GEMINI_API_KEY and not USE_MOCK_LLM:
    raise ValueError("GEMINI_API_KEY not found.")