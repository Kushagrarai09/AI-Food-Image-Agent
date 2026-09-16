from io import BytesIO
import cv2
import numpy as np
from PIL import Image


def image_stats(image_bytes: bytes) -> dict:
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    arr = np.array(image)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return {
        "width": image.width,
        "height": image.height,
        "blur_score": round(blur_score, 2),
        "is_low_resolution": image.width < 800 or image.height < 600,
    }


def passes_basic_quality(image_bytes: bytes, blur_threshold: float = 80) -> tuple[bool, dict]:
    stats = image_stats(image_bytes)
    reasons = []
    if stats["is_low_resolution"]:
        reasons.append("low resolution")
    if stats["blur_score"] < blur_threshold:
        reasons.append("possible blur")
    return len(reasons) == 0, {**stats, "reasons": reasons}
