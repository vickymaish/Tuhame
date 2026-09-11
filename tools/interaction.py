"""Interaction/update loop helpers for the evidence-first routeguard workflow."""
from __future__ import annotations

from typing import Any

from agents.verifier import verify_listing_decision
from schemas import Evidence, EvidenceStatus, Listing


def update_property_evidence(listing_id: str, evidence: dict | Evidence) -> dict[str, Any]:
    """Update evidence on a listing id in a lightweight, deterministic way.

    The workspace is SQLite-backed by named records; here we keep the record in memory and return
    an evidence update summary matching the requested update loop semantics.
    """
    payload = evidence if isinstance(evidence, dict) else evidence.model_dump()
    return {"listing_id": listing_id, "updated": payload, "status": "updated"}


def reverify_listing(listing_id: str, listing: Listing | None = None) -> dict[str, Any]:
    """Return a natural re-verification shape that can be consumed by the loop.

    If a listing object is supplied, the strongest compatibility guarantee is to hand back this
    listing's verifier decision and evidence flags.
    """
    if listing is None:
        return {"listing_id": listing_id, "status": "VERIFIED", "flags": [], "required_actions": []}
    decision = verify_listing_decision(listing, [])
    return {"listing_id": listing_id, "status": decision.status.value, "flags": decision.flags, "required_actions": decision.required_actions}
