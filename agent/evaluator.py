import json
import re
from io import BytesIO
from typing import Optional
from PIL import Image

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from agent.validator import image_stats

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover
    genai = None
    types = None


def _extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            return json.loads(match.group(0))
        raise


def _heuristic_score(food_name: str, image_bytes: bytes) -> dict:
    stats = image_stats(image_bytes)
    resolution_score = 100 if not stats["is_low_resolution"] else 45
    blur_score = min(100, max(0, stats["blur_score"] / 3))
    overall = round(0.55 * resolution_score + 0.45 * blur_score)
    return {
        "food_match": 50,
        "clarity": round(blur_score),
        "centering": 50,
        "framing": 50,
        "menu_suitability": round(overall),
        "overall_score": overall,
        "decision": "ACCEPT" if overall >= 75 else "REJECT",
        "reason": "Heuristic fallback; set GEMINI_API_KEY for visual AI evaluation.",
    }


def evaluate_image(food_name: str, image_bytes: bytes, threshold: int = 75) -> dict:
    """Use Gemini Vision to judge food match, clarity and menu suitability.
    Falls back to deterministic checks if no Gemini key is configured.
    """
    if not GEMINI_API_KEY or genai is None:
        result = _heuristic_score(food_name, image_bytes)
        result["decision"] = "ACCEPT" if result["overall_score"] >= threshold else "REJECT"
        return result

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"""
You are a restaurant menu image quality evaluator.
Requested food item: {food_name}

Evaluate this image for the exact requested food item and return ONLY valid JSON.
Score each field from 0 to 100:
- food_match: does the image visually represent the requested dish?
- clarity: is it sharp and clear enough for a menu?
- centering: is the dish reasonably centered?
- framing: is it well framed without excessive zoom/cropping?
- menu_suitability: overall suitability for a restaurant menu.
Then calculate overall_score as a weighted judgement from these factors.
Set decision to ACCEPT only if overall_score >= {threshold}.
Do not identify people or infer anything unrelated to the food.
JSON keys exactly:
food_match, clarity, centering, framing, menu_suitability, overall_score, decision, reason
"""
    try:
        image = Image.open(BytesIO(image_bytes))
        mime_type = Image.MIME.get(image.format, "image/jpeg")
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            ],
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )
        result = _extract_json(response.text)
        result["overall_score"] = int(float(result.get("overall_score", 0)))
        result["decision"] = "ACCEPT" if result["overall_score"] >= threshold else "REJECT"
        return result
    except Exception as exc:
        result = _heuristic_score(food_name, image_bytes)
        result["decision"] = "ACCEPT" if result["overall_score"] >= threshold else "REJECT"
        result["reason"] = f"Gemini evaluation failed; heuristic fallback used: {exc}"
        return result
