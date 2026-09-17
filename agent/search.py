from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List
import random
import time
import requests

from config.settings import REQUEST_TIMEOUT


WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"

USER_AGENT = (
    "AI-Food-Image-Agent/1.0 "
    "(automated food image processing assignment)"
)

MAX_RETRIES = 4
BASE_DELAY = 2.0


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


def _request_with_retry(url, params=None):
    """
    Make a Wikimedia request with retry and exponential backoff.

    Handles:
    - HTTP 429 rate limiting
    - temporary 5xx server errors
    - connection errors
    - timeouts
    """

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
                headers=headers,
            )

            # Wikimedia rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    try:
                        wait_time = float(retry_after)
                    except ValueError:
                        wait_time = BASE_DELAY * (2 ** attempt)
                else:
                    wait_time = BASE_DELAY * (2 ** attempt)

                wait_time += random.uniform(0.5, 1.5)

                time.sleep(min(wait_time, 60))
                continue

            # Temporary server-side problems
            if response.status_code in (500, 502, 503, 504):
                wait_time = BASE_DELAY * (2 ** attempt)
                wait_time += random.uniform(0.5, 1.5)

                time.sleep(min(wait_time, 30))
                continue

            response.raise_for_status()
            return response

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as exc:
            last_error = exc

            wait_time = BASE_DELAY * (2 ** attempt)
            wait_time += random.uniform(0.5, 1.5)

            time.sleep(min(wait_time, 30))

        except requests.exceptions.RequestException as exc:
            last_error = exc
            break

    if last_error:
        raise last_error

    raise RuntimeError("Wikimedia request failed after retries.")


def search_wikimedia(
    food_name: str,
    limit: int = 5
) -> List[ImageCandidate]:
    """
    Search Wikimedia Commons for food images.

    Uses a small number of query variants and only performs
    additional searches when the first search does not return
    enough candidates.
    """

    food_name = food_name.strip()

    if not food_name:
        return []

    # Query variants.
    # We start with the most specific search and only move
    # to broader searches if necessary.
    queries = [
        food_name,
        f"{food_name} food",
        f"{food_name} dish",
        f"{food_name} recipe",
    ]

    seen = set()
    candidates = []

    # Never request an unnecessarily large candidate set.
    requested_limit = max(1, min(int(limit), 10))

    for query in queries:

        # Stop as soon as enough candidates have been collected.
        if len(candidates) >= requested_limit:
            break

        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": min(max(requested_limit, 3), 10),
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 1800,
        }

        try:
            response = _request_with_retry(
                WIKIMEDIA_API,
                params=params,
            )

        except Exception:
            # If one query fails, try the next query instead
            # of terminating the whole food item.
            continue

        try:
            data = response.json()
        except ValueError:
            continue

        pages = data.get("query", {}).get("pages", {})

        for page in pages.values():

            info = (page.get("imageinfo") or [{}])[0]

            url = info.get("thumburl") or info.get("url")
            mime = info.get("mime", "")

            if not url:
                continue

            if not mime.startswith("image/"):
                continue

            if url in seen:
                continue

            seen.add(url)

            metadata = info.get("extmetadata", {})

            license_name = _clean_html(
                metadata.get(
                    "LicenseShortName",
                    {}
                ).get("value", "")
            )

            author = _clean_html(
                metadata.get(
                    "Artist",
                    {}
                ).get("value", "")
            )

            page_id = page.get("pageid")

            page_url = (
                f"https://commons.wikimedia.org/?curid={page_id}"
                if page_id
                else "https://commons.wikimedia.org/"
            )

            candidates.append(
                ImageCandidate(
                    title=page.get(
                        "title",
                        ""
                    ).replace("File:", "", 1),

                    image_url=url,

                    page_url=page_url,

                    license=license_name,

                    author=author,

                    retrieved_at=datetime.now(
                        timezone.utc
                    ).isoformat(),

                    width=int(
                        info.get("width") or 0
                    ),

                    height=int(
                        info.get("height") or 0
                    ),
                )
            )

            if len(candidates) >= requested_limit:
                return candidates

        # Small pause between different search queries.
        # This reduces Wikimedia rate limiting.
        if len(candidates) < requested_limit:
            time.sleep(random.uniform(0.7, 1.4))

    return candidates


def download_image(candidate: ImageCandidate) -> bytes:
    """
    Download an image with retry handling.
    """

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }

    last_error = None

    for attempt in range(MAX_RETRIES):

        try:
            response = requests.get(
                candidate.image_url,
                timeout=REQUEST_TIMEOUT,
                headers=headers,
            )

            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After"
                )

                if retry_after:
                    try:
                        wait_time = float(retry_after)
                    except ValueError:
                        wait_time = BASE_DELAY * (2 ** attempt)
                else:
                    wait_time = BASE_DELAY * (2 ** attempt)

                wait_time += random.uniform(0.5, 1.5)

                time.sleep(min(wait_time, 60))
                continue

            if response.status_code in (
                500,
                502,
                503,
                504,
            ):
                wait_time = BASE_DELAY * (2 ** attempt)
                wait_time += random.uniform(0.5, 1.5)

                time.sleep(min(wait_time, 30))
                continue

            response.raise_for_status()

            if not response.content:
                raise RuntimeError(
                    "Downloaded image is empty."
                )

            return response.content

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as exc:

            last_error = exc

            wait_time = BASE_DELAY * (2 ** attempt)
            wait_time += random.uniform(0.5, 1.5)

            time.sleep(min(wait_time, 30))

        except requests.exceptions.RequestException as exc:

            last_error = exc
            break

    if last_error:
        raise last_error

    raise RuntimeError(
        f"Unable to download image: {candidate.title}"
    )