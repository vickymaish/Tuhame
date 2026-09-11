import unittest

from agents.analyst import analyze
from schemas import Listing, SearchCriteria
from tools.extraction import extract_listing


class FilteringTests(unittest.TestCase):
    def test_over_budget_source_price_is_rejected(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani - KSh 100,000/month", "parking", "source", "https://x/1", criteria)
        survivors, rejected, _ = analyze([listing], criteria)
        self.assertEqual(survivors, [])
        self.assertIn("100000", rejected[0]["reason"])

    def test_variant_under_budget_survives_with_explicit_parking(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=85000, must_haves=["parking"])
        listing = extract_listing("2 bedroom Kilimani", "KSh 75,000 unfurnished / KSh 150,000 furnished. Parking.", "source", "https://x/variant", criteria)
        survivors, rejected, _ = analyze([listing], criteria)
        self.assertEqual(len(survivors), 1)
        self.assertEqual(rejected, [])
        self.assertEqual(survivors[0].listing.rent, 75000)

    def test_unknown_rent_or_parking_is_verification_candidate(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=85000, must_haves=["parking"])
        listing = extract_listing("2 bedroom Kilimani", "Contact agent for current price and availability.", "source", "https://x/unknown", criteria)
        survivors, rejected, _ = analyze([listing], criteria)
        self.assertEqual(len(survivors), 1)
        self.assertEqual(rejected, [])
        self.assertEqual(survivors[0].status, "verify_required")

    def test_not_available_listing_is_hard_rejected(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=85000)
        listing = extract_listing("2 bedroom Kilimani KSh 85,000", "Listing is no longer available.", "source", "https://x/unavailable", criteria)
        survivors, rejected, _ = analyze([listing], criteria)
        self.assertEqual(survivors, [])
        self.assertIn("no longer available", rejected[0]["reason"])


if __name__ == "__main__":
    unittest.main()