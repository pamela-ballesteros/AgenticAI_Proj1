import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")  # optional; add to .env if available
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not GOOGLE_MAPS_API_KEY:
    raise ValueError("Google Maps API key not found")

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found")
