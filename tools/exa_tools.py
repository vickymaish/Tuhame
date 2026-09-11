"""Live listing discovery and comparable-rent search through Exa."""
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

from exa_py import Exa
from dotenv import load_dotenv

from schemas import Listing, SearchCriteria
from tools.cache import get, key_for, put
from tools.extraction import extract_listing
from tools.history import record_observation
from tools.images import discover_image_urls

load_dotenv()


def _client() -> Exa:
    return Exa(api_key=os.environ["EXA_API_KEY"])


def find_listings(criteria: SearchCriteria, limit: int = 10) -> list[Listing]:
    location = criteria.location_raw or " ".join(criteria.locations) or criteria.location or "Nairobi and nearby areas"
    transaction_terms = {
        "RENT_MONTHLY": "for rent monthly KES to let",
        "RENT_DAILY": "daily rent per day KES",
        "SHORT_LET": "short let furnished KES monthly",
        "SALE": "for sale KES",
        "LAND_SALE": "land for sale KES",
        "COMMERCIAL_RENT": "commercial space for rent KES",
    }.get(criteria.transaction_type.value, "property KES")
    bed_term = f"{criteria.beds} bedroom" if criteria.beds else "residential property"
    query = f"{bed_term} {location} {transaction_terms}"
    cache_key = key_for("listings", {"query": query, "limit": limit})
    cached = get(cache_key)
    results = cached or _client().search_and_contents(query, type="auto", num_results=limit, text=True).results
    if not cached:
        put(cache_key, [{"title": item.title, "url": item.url, "text": getattr(item, "text", "")} for item in results])
    listings = []
    for item in results:
        title = item["title"] if isinstance(item, dict) else item.title
        url = item["url"] if isinstance(item, dict) else item.url
        text = item.get("text", "") if isinstance(item, dict) else getattr(item, "text", "")
        domain = urlparse(url).netloc.removeprefix("www.")
        observed_at = datetime.now(timezone.utc)
        history = record_observation(url, observed_at) if url else {}
        listing = extract_listing(title, text[:12000], domain or "Exa", url, criteria, observed_at)
        listing.observation_history = history
        listing.image_urls = discover_image_urls(url) if url else []
        listings.append(listing)
    return listings


def get_comparable_rent(location: str, beds: int) -> dict:
    query = f"{beds} bedroom {location} Nairobi rent price"
    cache_key = key_for("comps", query)
    cached = get(cache_key)
    if cached:
        return cached
    results = _client().search_and_contents(query, type="auto", num_results=8, text=True).results
    stats = {"median": None, "p25": None, "p75": None, "n": len(results)}
    put(cache_key, stats)
    return stats
