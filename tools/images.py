"""Discover source-hosted listing image URLs without downloading images."""
import json
import re
from html import unescape
from urllib.parse import urljoin

import httpx


def extract_image_urls(html: str, page_url: str) -> list[str]:
    candidates = []
    candidates.extend(re.findall(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)', html, re.IGNORECASE))
    for block in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.IGNORECASE | re.DOTALL):
        try:
            data = json.loads(unescape(block))
        except json.JSONDecodeError:
            continue
        records = data if isinstance(data, list) else [data]
        for record in records:
            image = record.get("image") if isinstance(record, dict) else None
            if isinstance(image, str):
                candidates.append(image)
            elif isinstance(image, list):
                candidates.extend(item for item in image if isinstance(item, str))
            elif isinstance(image, dict) and isinstance(image.get("url"), str):
                candidates.append(image["url"])
    results = []
    for candidate in candidates:
        absolute = urljoin(page_url, candidate.strip())
        if absolute.startswith(("http://", "https://")) and absolute not in results:
            results.append(absolute)
    return results[:12]


def discover_image_urls(page_url: str) -> list[str]:
    try:
        response = httpx.get(page_url, timeout=10, follow_redirects=True, headers={"User-Agent": "RouteGuard/0.1 listing evidence"})
        response.raise_for_status()
    except httpx.HTTPError:
        return []
    return extract_image_urls(response.text, page_url)