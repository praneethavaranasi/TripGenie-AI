import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================
# API KEYS
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is missing.")

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY is missing.")

# ============================================================
# APPLICATION
# ============================================================

APP_NAME = "TripGenie AI"
APP_VERSION = "1.0.0"

# ============================================================
# AI MODELS
# ============================================================

# Gemini primary provider
GEMINI_MODEL = "gemini-3.8-flash"

# Groq backup provider
GROQ_MODEL = "openai/gpt-oss-120b"

# ============================================================
# RETRY SETTINGS
# ============================================================

MAX_RETRIES = 2

RETRY_DELAYS = [
    2,
    5,
]