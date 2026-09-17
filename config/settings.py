import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]

load_dotenv(ROOT / ".env")


# ============================================================
# DIRECTORIES
# ============================================================

DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output" / "images"
CREDENTIALS_DIR = ROOT / "credentials"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# GOOGLE DRIVE
# ============================================================

TOKEN_FILE = CREDENTIALS_DIR / "token.json"
GOOGLE_CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"


DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "").strip()

if not DRIVE_FOLDER_ID:
    try:
        DRIVE_FOLDER_ID = str(
            st.secrets.get("DRIVE_FOLDER_ID", "")
        ).strip()
    except Exception:
        DRIVE_FOLDER_ID = ""


# ============================================================
# AI
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

if not GEMINI_API_KEY:
    try:
        GEMINI_API_KEY = str(
            st.secrets.get("GEMINI_API_KEY", "")
        ).strip()
    except Exception:
        GEMINI_API_KEY = ""


GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
).strip()


# ============================================================
# PROCESSING
# ============================================================

AI_THRESHOLD = int(
    os.getenv("AI_THRESHOLD", "75")
)

CANDIDATES = int(
    os.getenv("CANDIDATES", "5")
)

BLUR_THRESHOLD = float(
    os.getenv("BLUR_THRESHOLD", "80")
)

REQUEST_TIMEOUT = int(
    os.getenv("REQUEST_TIMEOUT", "20")
)


# ============================================================
# IMAGE REQUIREMENTS
# ============================================================

TARGET_WIDTH = 1800
TARGET_HEIGHT = 1200

MAX_BYTES = 10 * 1024 * 1024