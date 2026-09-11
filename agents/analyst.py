"""Dedupe, filter, and explain listing decisions."""
from rapidfuzz.fuzz import token_set_ratio

from schemas import EvidenceStatus, Listing, PriceType, SearchCriteria, Survivor, TransactionType
from tools.cache import event
from tools.dedup import cluster_duplicates, compare_duplicate_cluster


def analyze(listings: list[Listing], criteria: SearchCriteria) -> tuple[list[Survivor], list[dict], int]:
    survivors, rejected, duplicates_removed, _ = analyze_with_conflicts(listings, criteria)
    return survivors, rejected, duplicates_removed


def analyze_with_conflicts(listings: list[Listing], criteria: SearchCriteria) -> tuple[list[Survivor], list[dict], int, list[dict]]:
    unique: list[Listing] = []
    rejected: list[dict] = []
    survivors: list[Survivor] = []
    duplicate_conflicts = [compare_duplicate_cluster(cluster) for cluster in cluster_duplicates(listings)]
    for listing in listings:
        duplicate = next((item for item in unique if listing.url and listing.url == item.url or (token_set_ratio(listing.description, item.description) >= 85 and listing.location == item.location and listing.beds == item.beds)), None)
        if duplicate:
            event("analyst", "duplicate removed", {"url": listing.url})
            continue
        unique.append(listing)
        reasons = []
        rent_evidence = next((item for item in listing.evidence if item.claim == "rent"), None)
        hard_reject_reason = None
        verification_required = False
        if criteria.transaction_type == TransactionType.RENT_MONTHLY and listing.transaction_type in {TransactionType.SALE, TransactionType.LAND_SALE, TransactionType.RENT_DAILY, TransactionType.SHORT_LET, TransactionType.COMMERCIAL_RENT}:
            hard_reject_reason = f"listing is {listing.transaction_type.value.lower().replace('_', ' ')}, not monthly rent"
        elif listing.availability_status == EvidenceStatus.NOT_AVAILABLE:
            hard_reject_reason = "listing is no longer available"
        elif criteria.max_rent is not None and listing.rent is not None and listing.rent > criteria.max_rent and listing.price_type != PriceType.CONFLICT:
            hard_reject_reason = f"rent {listing.rent} exceeds max {criteria.max_rent}"
        elif listing.rent is None or rent_evidence is None or rent_evidence.status in {EvidenceStatus.UNKNOWN, EvidenceStatus.CONFLICT} or listing.price_type == PriceType.CONFLICT:
            verification_required = True
        if hard_reject_reason:
            rejected.append({
                "url": listing.url,
                "reason": hard_reject_reason,
                "contactability": listing.contactability.value,
                "contacts": [
                    {"type": contact.type.value if contact.type else contact.kind, "value": contact.value, "scope": contact.contact_scope.value}
                    for contact in listing.contacts
                ],
            })
            event("analyst", "rejected over budget", {"url": listing.url})
            continue
        missing = [item for item in criteria.must_haves if item.lower() not in [a.lower() for a in listing.amenities]]
        if missing:
            verification_required = True
            reasons.append(f"{', '.join(missing)} evidence is not established")
        reasons.extend([f"{listing.rent:,} KES is within budget" if listing.rent is not None else "Rent is not established", f"{listing.beds or 'Unknown'} bedrooms in {listing.location or 'unknown location'}"])
        if listing.amenities:
            reasons.append(f"mentions {', '.join(listing.amenities)}")
        if listing.price_type == PriceType.VARIANT_PRICE:
            reasons.append("Lower furnished/unfurnished price variant is within budget")
        event("analyst", "listing survived filters", {"url": listing.url})
        survivor = Survivor(listing=listing, match_reasons=reasons)
        if verification_required:
            survivor.status = "verify_required"
        survivors.append(survivor)
    return survivors, rejected, len(listings) - len(unique), duplicate_conflicts
