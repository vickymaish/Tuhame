import unittest

from schemas import EvidenceStatus, FreshnessState, PriceType, SearchCriteria
from tools.extraction import extract_listing


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)

    def test_preserves_source_rent(self):
        listing = extract_listing("2 bedroom Kilimani - KSh 100,000/month", "", "source", "https://x/1", self.criteria)
        self.assertEqual(listing.rent, 100000)
        self.assertEqual(listing.evidence[0].status, EvidenceStatus.VERIFIED)

    def test_missing_date_is_unknown(self):
        listing = extract_listing("2 bedroom Kilimani - KSh 60,000/month", "", "source", "https://x/2", self.criteria)
        self.assertEqual(listing.freshness.state, FreshnessState.UNKNOWN)
        self.assertIn("AGE UNKNOWN", listing.freshness.explanation)

    def test_conflicting_prices_are_not_collapsed(self):
        listing = extract_listing("2 bedroom Kilimani rent KSh 60,000 and rent KSh 100,000", "", "source", "https://x/3", self.criteria)
        self.assertIsNone(listing.rent)
        self.assertEqual(listing.evidence[0].status, EvidenceStatus.CONFLICT)

    def test_equivalent_price_mentions_are_one_exact_price(self):
        listing = extract_listing("2 bedroom Kilimani KSh 100,000/month", "Rent KES 100,000 per month. KES 100,000.", "source", "https://x/4", self.criteria)
        self.assertEqual(listing.rent, 100000)
        self.assertEqual(listing.price_type, PriceType.EXACT_PRICE)
        self.assertEqual({item.value for item in listing.evidence if item.claim == "rent"}, {100000})

    def test_furnished_variants_keep_lower_variant_for_budget_filtering(self):
        listing = extract_listing("2 bedroom Kilimani", "KSh 75,000 unfurnished / KSh 150,000 furnished. Parking.", "source", "https://x/5", self.criteria)
        self.assertEqual(listing.rent, 75000)
        self.assertEqual(listing.price_type, PriceType.VARIANT_PRICE)
        self.assertIn("parking", listing.amenities)

    def test_navigation_price_range_does_not_override_listing_rent(self):
        listing = extract_listing("2 bedroom Kilimani", "Price Range: from KSh. 70,000 to KSh. 500,000,000. Rent: KES 100,000 per month.", "source", "https://x/6", self.criteria)
        self.assertEqual(listing.rent, 100000)
        self.assertEqual(listing.price_type, PriceType.EXACT_PRICE)

    def test_table_price_variants_remain_variants(self):
        listing = extract_listing("2 bedroom Kilimani", "| Apartment Type | Monthly Rent |\n| Unfurnished | 75,000 |\n| Furnished | 150,000 |", "source", "https://x/8", self.criteria)
        self.assertEqual(listing.rent, 75000)
        self.assertEqual(listing.price_type, PriceType.VARIANT_PRICE)

    def test_different_labeled_rents_remain_conflict(self):
        listing = extract_listing("2 bedroom Kilimani KES 120,000", "Affordable luxury at KES 100,000 per month.", "source", "https://x/7", self.criteria)
        self.assertIsNone(listing.rent)
        self.assertEqual(listing.price_type, PriceType.CONFLICT)


if __name__ == "__main__":
    unittest.main()