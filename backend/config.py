import os
from dotenv import load_dotenv

# Load .env file if it exists locally
load_dotenv()

# API Keys
JUSTTCG_API_KEY = os.getenv("JUSTTCG_API_KEY", "tcg_8de0be839c274f1a857254c6497d0f55")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pokemon_inventory.db")

# Server settings
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")

# Rate limit settings
POLITENESS_DELAY = float(os.getenv("POLITENESS_DELAY", 1.2))
