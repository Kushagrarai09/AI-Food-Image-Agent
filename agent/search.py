from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List
from urllib.parse import quote
import requests

from config.settings import REQUEST_TIMEOUT

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"

@dataclass
class ImageCandidate:
    title: str
    image_url: str
    page_url: str
    source: str = "Wikimedia Commons"
    license: str = ""
    author: str = ""
    retrieved_at: str = ""
    width: int = 0
    height: int = 0


def _clean_html(value: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", value or "").strip()


def search_wikimedia(food_name: str, limit: int = 5) -> List[ImageCandidate]:
    """Search Wikimedia Commons for food images and return metadata + image URLs."""
    queries = [food_name, f"{food_name} food", f"{food_name} dish"]
    seen = set()
    candidates = []

    for query in queries:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": max(limit, 5),
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 2200,
        }
        r = requests.get(WIKIMEDIA_API, params=params, timeout=REQUEST_TIMEOUT,
                         headers={"User-Agent": "AI-Food-Image-Agent/1.0"})
        r.raise_for_status()
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            url = info.get("thumburl") or info.get("url")
            mime = info.get("mime", "")
            if not url or not mime.startswith("image/"):
                continue
            if url in seen:
                continue
            seen.add(url)
            meta = info.get("extmetadata", {})
            license_name = _clean_html(meta.get("LicenseShortName", {}).get("value", ""))
            author = _clean_html(meta.get("Artist", {}).get("value", ""))
            page_id = page.get("pageid")
            page_url = f"https://commons.wikimedia.org/?curid={page_id}" if page_id else "https://commons.wikimedia.org/"
            candidates.append(ImageCandidate(
                title=page.get("title", "").replace("File:", "", 1),
                image_url=url,
                page_url=page_url,
                license=license_name,
                author=author,
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                width=int(info.get("width") or 0),
                height=int(info.get("height") or 0),
            ))
            if len(candidates) >= limit:
                return candidates
    return candidates


def download_image(candidate: ImageCandidate) -> bytes:
    r = requests.get(candidate.image_url, timeout=REQUEST_TIMEOUT,
                     headers={"User-Agent": "AI-Food-Image-Agent/1.0"})
    r.raise_for_status()
    return r.content
