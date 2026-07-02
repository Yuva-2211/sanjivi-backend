"""
Yoga Image Search Agent — Wikimedia Commons.

Replaces DuckDuckGo (rate-limited, unreliable) with Wikimedia Commons API.
Free, no API key, no rate limits for normal usage, always returns stable URLs.
"""

from __future__ import annotations

import re
import asyncio
import urllib.parse

import httpx

from app.schemas.chat import YogaPoseImage
from app.utils.logger import get_logger

log = get_logger(__name__)

# Wikimedia Commons search endpoint
_WMC_SEARCH_URL = "https://commons.wikimedia.org/w/api.php"
# Wikipedia summary fallback (has thumbnail images for most yoga poses)
_WP_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"


def _extract_pose_name(pose_description: str) -> str:
    """
    Extract the core pose name from a formatted string like:
    'Trikonasana (Triangle Pose) — hold for 30 seconds on each side'
    Returns a clean search term like 'Trikonasana yoga pose'.
    """
    # Grab text before any dash/em-dash (instructions come after)
    base = re.split(r"[—–-]", pose_description)[0].strip()
    # Keep both Sanskrit and English name (strip parens)
    clean = re.sub(r"[()]", " ", base).strip()
    # Collapse multiple spaces
    clean = re.sub(r"\s+", " ", clean)
    return clean


async def _fetch_wikimedia_image(pose_description: str, client: httpx.AsyncClient) -> YogaPoseImage | None:
    """
    Search Wikimedia Commons for an image of the yoga pose.

    Strategy:
    1. Search Commons file namespace for "{pose} yoga pose"
    2. If found, get the direct image URL via imageinfo
    3. Fallback: Wikipedia article thumbnail via REST API summary
    """
    pose_name = _extract_pose_name(pose_description)
    search_query = f"{pose_name} yoga pose"

    # ── Step 1: Wikimedia Commons file search ──────────────────────────────
    try:
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": search_query,
            "srnamespace": "6",  # File namespace
            "srlimit": "3",
            "format": "json",
            "origin": "*",
        }
        resp = await client.get(_WMC_SEARCH_URL, params=search_params, timeout=6.0)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("query", {}).get("search", [])

        for result in results:
            title = result.get("title", "")
            if not title.startswith("File:"):
                continue
            # Only use image files
            ext = title.rsplit(".", 1)[-1].lower()
            if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
                continue

            # ── Step 2: Get direct image URL ──────────────────────────────
            info_params = {
                "action": "query",
                "titles": title,
                "prop": "imageinfo",
                "iiprop": "url|thumburl",
                "iiurlwidth": "400",
                "format": "json",
                "origin": "*",
            }
            info_resp = await client.get(_WMC_SEARCH_URL, params=info_params, timeout=6.0)
            info_resp.raise_for_status()
            info_data = info_resp.json()
            pages = info_data.get("query", {}).get("pages", {})

            for page in pages.values():
                imageinfo = page.get("imageinfo", [{}])
                if not imageinfo:
                    continue
                thumb_url = imageinfo[0].get("thumburl", "")
                orig_url = imageinfo[0].get("url", "")
                image_url = thumb_url or orig_url
                if image_url:
                    encoded = urllib.parse.quote(title[5:], safe="")  # strip "File:"
                    source_url = f"https://commons.wikimedia.org/wiki/File:{encoded}"
                    log.debug("wikimedia_image_found", pose=pose_description[:50], url=image_url[:80])
                    return YogaPoseImage(
                        pose_name=pose_description,
                        image_url=image_url,
                        source_url=source_url,
                    )

    except Exception as exc:
        log.warning("wikimedia_commons_search_failed", pose=pose_description[:50], error=str(exc))

    # ── Step 3: Wikipedia article thumbnail fallback ───────────────────────
    try:
        # Build a Wikipedia-friendly title from the pose name
        wp_title = pose_name.replace(" ", "_")
        wp_resp = await client.get(
            _WP_SUMMARY_URL.format(title=urllib.parse.quote(wp_title)),
            timeout=5.0,
        )
        if wp_resp.status_code == 200:
            wp_data = wp_resp.json()
            thumbnail = wp_data.get("thumbnail", {})
            image_url = thumbnail.get("source", "")
            page_url = wp_data.get("content_urls", {}).get("desktop", {}).get("page", "")
            if image_url:
                log.debug("wikipedia_thumbnail_found", pose=pose_description[:50])
                return YogaPoseImage(
                    pose_name=pose_description,
                    image_url=image_url,
                    source_url=page_url or f"https://en.wikipedia.org/wiki/{wp_title}",
                )
    except Exception as exc:
        log.warning("wikipedia_fallback_failed", pose=pose_description[:50], error=str(exc))

    log.warning("yoga_image_not_found", pose=pose_description[:50])
    return None


async def search_yoga_images(
    poses: list[str],
    max_images: int = 3,
) -> list[YogaPoseImage]:
    """
    Fetch images for the first *max_images* yoga poses concurrently.
    Uses a single shared httpx.AsyncClient for connection pooling.
    """
    if not poses:
        return []

    target_poses = poses[:max_images]
    log.info("yoga_image_search_start", num_poses=len(target_poses))

    async with httpx.AsyncClient(
        headers={"User-Agent": "SanjiviAI/1.0 (https://sanjivi.ai; healthcare bot)"},
        follow_redirects=True,
    ) as client:
        tasks = [_fetch_wikimedia_image(pose, client) for pose in target_poses]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    images: list[YogaPoseImage] = []
    for result in results:
        if isinstance(result, YogaPoseImage):
            images.append(result)
        elif isinstance(result, Exception):
            log.warning("yoga_image_result_error", error=str(result))

    log.info("yoga_image_search_done", found=len(images))
    return images
