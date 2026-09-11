"""Investigation and action planning helpers built around deterministic evidence states."""
from typing import Any

from schemas import EvidenceStatus, FinancialStatus, Listing


def plan_investigation(listing: Listing) -> dict[str, Any]:
    """Convert unresolved or contradictory fields into a small structured action plan.

    The output uses routeguard-friendly action semantics without inventing facts.
    """
    actions = []
    decision = "VERIFY"

    if listing.availability_status == EvidenceStatus.UNKNOWN:
        actions.append({"type": "VERIFY_AVAILABILITY", "field": "availability", "question": "Verify current availability for this exact unit."})
    elif listing.availability_status == EvidenceStatus.CONFLICT:
        actions.append({"type": "VERIFY_AVAILABILITY", "field": "availability", "question": "Resolve the source availability contradiction from the listing."})

    for charge in listing.financial_charges:
        if charge.status in {FinancialStatus.UNKNOWN, FinancialStatus.NOT_MENTIONED}:
            field = charge.name
            actions.append({"type": "ASK_AGENT", "field": field, "question": f"Is the {field} included in the stated rent or is there a separate {field}?"})

    if listing.rent is None:
        actions.append({"type": "VERIFY", "field": "rent", "question": "Inspect the source payment terms and confirm the monthly rent."})

    st = listing.source_state.get("page_status") if isinstance(listing.source_state, dict) else None
    if st in {"EXPIRED", "REDIRECTED", "ERROR"}:
        actions.append({"type": "SOURCE_VERIFICATION", "field": "source_state", "question": "Verify the live page status and whether the listing remains current."})

    if not actions:
        decision = "VERIFIED"
    elif any(item.get("type") == "ASK_AGENT" for item in actions):
        decision = "ASK_AGENT"
    return {"decision": decision, "actions": actions}
