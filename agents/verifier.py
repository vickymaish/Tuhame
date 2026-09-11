"""Evidence checks that do not invent certainty."""
from schemas import EvidenceStatus, FinancialStatus, Listing, VerificationDecision


def verify_listing_decision(listing: Listing, must_haves: list[str]) -> VerificationDecision:
    flags = []
    actions = []
    status = EvidenceStatus.VERIFIED
    rent_claim = next((item for item in listing.evidence if item.claim == "rent"), None)
    if rent_claim is None or rent_claim.status == EvidenceStatus.UNKNOWN:
        flags.append("Rent UNKNOWN: no source price was extracted")
        actions.append("Ask the agent to confirm the current monthly rent")
        status = EvidenceStatus.UNKNOWN
    elif rent_claim.status == EvidenceStatus.CONFLICT:
        flags.append("Rent CONFLICT: source contains multiple prices")
        actions.append("Ask the agent which advertised rent applies to this unit")
        status = EvidenceStatus.CONFLICT
    for requirement in must_haves:
        if requirement.lower() not in [amenity.lower() for amenity in listing.amenities]:
            flags.append(f"{requirement}: UNVERIFIED")
            actions.append(f"Ask the agent to confirm {requirement}")
            if status == EvidenceStatus.VERIFIED:
                status = EvidenceStatus.UNVERIFIED
    for charge in listing.financial_charges:
        if charge.status == FinancialStatus.CONFLICT:
            flags.append(f"{charge.name}: CONFLICT")
            actions.append(f"Ask the agent to confirm the {charge.name} amount")
            status = EvidenceStatus.CONFLICT
    if listing.freshness.state.value == "UNKNOWN":
        flags.append("AGE UNKNOWN: publication/availability date not established")
    if listing.availability_status == EvidenceStatus.CONFLICT:
        flags.append("Availability CONFLICT: source contains opposing availability claims")
        actions.append("Verify availability with the agent for this exact unit")
        status = EvidenceStatus.CONFLICT
    elif listing.availability_status == EvidenceStatus.UNKNOWN:
        flags.append("Availability UNKNOWN")
        actions.append("Verify availability with the agent for this exact unit")
        if status == EvidenceStatus.VERIFIED:
            status = EvidenceStatus.UNKNOWN
    elif listing.availability_status == EvidenceStatus.NOT_AVAILABLE:
        flags.append("Availability NOT_AVAILABLE: explicit non-availability signal")
    elif listing.availability_status == EvidenceStatus.AVAILABLE:
        flags.append("Availability AVAILABLE: explicit positive signal")
    return VerificationDecision(status=status, flags=flags, required_actions=actions)


def verify_listing(listing: Listing, must_haves: list[str]) -> list[str]:
    """Compatibility wrapper for report consumers that only need text flags."""
    return verify_listing_decision(listing, must_haves).flags