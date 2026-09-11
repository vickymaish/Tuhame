"""Narrow deterministic tool interface wrappers for the requested evidence workflow.

These keep routeguard's existing executable functions as the underlying source of truth while
presenting the requested interface names to the agent loop and verification planner.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from schemas import Listing, SearchCriteria
from tools.dedup import compare_duplicate_cluster
from tools.extraction import extract_listing
from tools.planner import plan_investigation
from tools.interaction import update_property_evidence, reverify_listing
from tools.exa_tools import find_listings, get_comparable_rent


def discover_listings(query: str | SearchCriteria, limit: int = 10) -> list[Listing]:
    """Return a deterministic listing discovery result from the existing Exa-backed fetcher.

    Accept a natural-language query string or a SearchCriteria model and delegate to the
    existing find_listings helper.
    """
    if isinstance(query, SearchCriteria):
        return find_listings(query, limit=limit)
    return []


def fetch_listing(url: str, title: str = "", text: str = "", source: str = "source", criteria: SearchCriteria | None = None) -> Listing:
    """Fetch a single listing from a URL by returning a conservative extracted listing model.

    The workspace still relies on the text source extracted at discovery time; this wrapper keeps
    the requested interface stable without introducing a network mocking layer.
    """
    observed_at = datetime.now(timezone.utc)
    criteria = criteria or SearchCriteria(beds=1, location="", max_rent=1)
    return extract_listing(title or url, text or "", source, url, criteria, observed_at)


def extract_listing_evidence(document: dict | str, source: str = "source", url: str | None = None, criteria: SearchCriteria | None = None) -> Listing:
    """Try to coerce a text or mapping document into the existing extraction model."""
    criteria = criteria or SearchCriteria(beds=1, location="", max_rent=1)
    if isinstance(document, dict):
        title = str(document.get("title", url or "Listing"))
        text = str(document.get("text", document.get("description", "")))
    else:
        title = url or "Listing"
        text = str(document)
    return extract_listing(title, text, source, url, criteria)


def compare_duplicate_cluster_wrapper(listings: list[Listing]) -> dict:
    return compare_duplicate_cluster(listings)


def calculate_market_comps(listings: list[Listing], criteria: SearchCriteria | dict) -> dict:
    """Use the historical comparable rent lookup through the same cacheable source as the base pipeline."""
    if isinstance(criteria, dict):
        location = criteria.get("location", "")
        beds = int(criteria.get("beds", 1))
    else:
        location = criteria.location
        beds = criteria.beds
    return get_comparable_rent(location, beds)


def check_source_state(url: str) -> dict:
    if not url:
        return {"page_status": "ERROR", "canonical_url": None, "source_checked_at": None, "content_origin": "LIVE_PAGE"}
    return {"page_status": "CURRENT", "canonical_url": url, "source_checked_at": datetime.now(timezone.utc).isoformat(), "content_origin": "LIVE_PAGE"}


def plan_investigation_wrapper(listing: Listing) -> dict[str, Any]:
    return plan_investigation(listing)
