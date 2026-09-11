"""Duplicate-cluster comparison helpers for evidence-aware listings."""
from typing import Iterable

from schemas import FinancialStatus, Listing


def _charge_value(listing: Listing, name: str) -> str:
    charge = next((item for item in listing.financial_charges if item.name == name), None)
    if charge is None:
        return "NOT_MENTIONED"
    if charge.status == FinancialStatus.INCLUDED:
        return "INCLUDED"
    if charge.status == FinancialStatus.EXPLICIT_AMOUNT:
        return str(charge.amount)
    return charge.status.value


def cluster_duplicates(listings: Iterable[Listing]) -> list[list[Listing]]:
    """Group only listings with an explicit URL match or strong property signals."""
    clusters: list[list[Listing]] = []
    for listing in listings:
        cluster = next(
            (
                items
                for items in clusters
                if (listing.url and listing.url == items[0].url)
                or (
                    listing.location == items[0].location
                    and listing.beds == items[0].beds
                    and listing.description == items[0].description
                )
            ),
            None,
        )
        if cluster is None:
            clusters.append([listing])
        else:
            cluster.append(listing)
    return [cluster for cluster in clusters if len(cluster) > 1]


def compare_duplicate_cluster(listings: Iterable[Listing]) -> dict:
    """Create a small duplicate comparison cluster summary for same-URL or same-property duplicate signals.

    Returns a conservative structure with status and evidence columns rather than inventing facts.
    """
    rows = list(listings)
    if not rows:
        return {"status": "UNKNOWN", "signals": [], "items": []}

    fields = {
        "rent": [str(row.rent) if row.rent is not None else "UNKNOWN" for row in rows],
        "deposit": [str(row.deposit) if row.deposit is not None else _charge_value(row, "deposit") for row in rows],
        "service_charge": [_charge_value(row, "service_charge") for row in rows],
        "parking": [str(row.parking_fee) if row.parking_fee is not None else _charge_value(row, "parking") for row in rows],
        "availability": [row.availability_status.value for row in rows],
    }
    signals = sorted(field for field, values in fields.items() if len(set(values)) > 1)
    status = "CONFLICT"
    return {
        "status": status,
        "signals": ["same_property_cluster", *signals],
        "items": [r.url for r in rows],
        "sources": [r.source for r in rows],
        "evidence": fields,
        "inconsistencies": [f"CONFLICT / FEE_AMBIGUITY: {field}" if field in {"deposit", "service_charge", "parking"} else f"CONFLICT / {field.upper()}" for field in signals],
    }
