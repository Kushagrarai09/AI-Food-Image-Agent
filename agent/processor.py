from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps

from config.settings import TARGET_WIDTH, TARGET_HEIGHT, MAX_BYTES


def process_image(image_bytes: bytes, food_name: str, output_dir: Path) -> tuple[Path, dict]:
    """Center-crop to exactly 1800x1200 and compress to a JPG below 10 MB."""
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    target_ratio = TARGET_WIDTH / TARGET_HEIGHT
    src_ratio = image.width / image.height

    if src_ratio > target_ratio:
        new_width = round(image.height * target_ratio)
        left = (image.width - new_width) // 2
        image = image.crop((left, 0, left + new_width, image.height))
    else:
        new_height = round(image.width / target_ratio)
        top = (image.height - new_height) // 2
        image = image.crop((0, top, image.width, top + new_height))

    image = image.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

    # Keep the food item text intact except characters Windows/filesystems reject.
    safe_name = "".join(c if c not in '<>:"/\\|?*' else "_" for c in food_name).strip()
    path = output_dir / f"{safe_name}.jpg"

    quality = 92
    while quality >= 45:
        buf = BytesIO()
        image.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
        if len(buf.getvalue()) < MAX_BYTES:
            path.write_bytes(buf.getvalue())
            return path, {
                "width": TARGET_WIDTH,
                "height": TARGET_HEIGHT,
                "format": "JPG",
                "size_bytes": len(buf.getvalue()),
                "quality": quality,
            }
        quality -= 5

    # Extremely unusual fallback: maximum compression while preserving dimensions.
    image.save(path, format="JPEG", quality=40, optimize=True)
    return path, {
        "width": TARGET_WIDTH,
        "height": TARGET_HEIGHT,
        "format": "JPG",
        "size_bytes": path.stat().st_size,
        "quality": 40,
    }
