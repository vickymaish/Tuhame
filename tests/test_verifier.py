import unittest

from agents.verifier import verify_listing_decision
from schemas import EvidenceStatus, FinancialStatus, SearchCriteria
from tools.extraction import extract_listing


class VerifierTests(unittest.TestCase):
    def test_included_parking_is_distinct_from_unknown(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani KSh 60,000", "Parking included.", "source", "https://x/2", criteria)
        parking = next(item for item in listing.financial_charges if item.name == "parking")
        self.assertEqual(parking.status, FinancialStatus.INCLUDED)

    def test_charge_and_availability_conflicts_require_small_actions(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000, must_haves=["parking"])
        listing = extract_listing("2 bedroom Kilimani KSh 60,000", "Parking fee KSh 5,000. Available. Not accepting inquiries.", "source", "https://x/1", criteria)
        decision = verify_listing_decision(listing, criteria.must_haves)
        self.assertEqual(decision.status, EvidenceStatus.CONFLICT)
        self.assertTrue(any("availability" in action.lower() for action in decision.required_actions))


if __name__ == "__main__":
    unittest.main()