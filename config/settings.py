import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output" / "images"
CREDENTIALS_DIR = ROOT / "credentials"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"
GOOGLE_CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
AI_THRESHOLD = int(os.getenv("AI_THRESHOLD", "75"))
CANDIDATES = int(os.getenv("CANDIDATES", "5"))
BLUR_THRESHOLD = float(os.getenv("BLUR_THRESHOLD", "80"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "").strip()

TARGET_WIDTH = 1800
TARGET_HEIGHT = 1200
MAX_BYTES = 10 * 1024 * 1024
