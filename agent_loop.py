"""Sequential Nyumba Hunter pipeline."""
from agents.analyst import analyze_with_conflicts
from agents.verifier import verify_listing_decision
from schemas import PipelineResult, SearchCriteria
from tools.exa_tools import find_listings, get_comparable_rent
from tools.cache import event


def run(criteria: SearchCriteria) -> PipelineResult:
    event("scout", "searching live listings", criteria.model_dump())
    listings = find_listings(criteria)
    event("scout", f"found {len(listings)} listings")
    survivors, rejected, duplicates_removed, duplicate_conflicts = analyze_with_conflicts(listings, criteria)
    for survivor in survivors:
        decision = verify_listing_decision(survivor.listing, criteria.must_haves)
        survivor.verification = decision
        survivor.red_flags.extend(decision.flags)
        survivor.status = "shortlisted" if decision.status == "VERIFIED" else "verify_required"
        if criteria.beds:
            survivor.comp_stats = get_comparable_rent(survivor.listing.location or criteria.location, survivor.listing.beds or criteria.beds)
        if survivor.comp_stats.get("p75") and survivor.listing.rent is not None and survivor.listing.rent > survivor.comp_stats["p75"]:
            survivor.red_flags.append("Listed above the 75th percentile of comparable rents")
    event("briefing", f"shortlisted {len(survivors)} properties")
    return PipelineResult(criteria=criteria, discovered=len(listings), duplicates_removed=duplicates_removed, rejected=rejected, survivors=list(survivors), duplicate_conflicts=duplicate_conflicts)
