import unittest
from datetime import datetime, timezone

from schemas import EvidenceStatus, FinancialStatus, Freshness, SearchCriteria, PriceType, SourcePageStatus, SourceContentOrigin
from tools.extraction import extract_listing


class EvidenceStateRegressionTests(unittest.TestCase):
    def test_positive_availability_is_available(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani listing", "currently accepting inquiries", "source", "https://x/avail", criteria)
        self.assertEqual(listing.availability_status, EvidenceStatus.AVAILABLE)

    def test_available_for_occupation_is_available(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani listing", "available for occupation", "source", "https://x/avail2", criteria)
        self.assertEqual(listing.availability_status, EvidenceStatus.AVAILABLE)

    def test_negated_availability_is_not_available(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani listing", "not currently accepting inquiries", "source", "https://x/neg", criteria)
        self.assertEqual(listing.availability_status, EvidenceStatus.NOT_AVAILABLE)

    def test_no_longer_accepting_inquiries_is_not_available(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani listing", "no longer accepting inquiries", "source", "https://x/neg2", criteria)
        self.assertEqual(listing.availability_status, EvidenceStatus.NOT_AVAILABLE)

    def test_listing_is_no_longer_available_is_not_available(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani listing", "listing is no longer available", "source", "https://x/old", criteria)
        self.assertEqual(listing.availability_status, EvidenceStatus.NOT_AVAILABLE)

    def test_unknown_availability_stays_unknown(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani listing", "contact agent for availability", "source", "https://x/unknown", criteria)
        self.assertEqual(listing.availability_status, EvidenceStatus.UNKNOWN)

    def test_conflicting_availability_is_conflict(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani listing", "available for occupation. listing is no longer available.", "source", "https://x/conflict", criteria)
        self.assertEqual(listing.availability_status, EvidenceStatus.CONFLICT)

    def test_source_state_defaults_to_current_live_page_and_is_serializable(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani rent KSh 75,000", "source text", "source", "https://x/source", criteria)
        self.assertEqual(listing.source_state["page_status"], SourcePageStatus.CURRENT)
        self.assertEqual(listing.source_state["content_origin"], SourceContentOrigin.LIVE_PAGE)

    def test_price_type_and_fee_statuses_are_extracted_conservatively(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani rent KSh 75,000/month", "service charge included. dedicated parking.", "source", "https://x/fee", criteria)
        self.assertEqual(listing.price_type, PriceType.EXACT_PRICE)
        self.assertEqual(listing.rent, 75000)
        self.assertEqual(listing.financial_charges[0].status, FinancialStatus.INCLUDED)

    def test_exact_price_is_classified_as_exact(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani listing", "KSh 75,000/month", "source", "https://x/exact", criteria)
        self.assertEqual(listing.price_type, PriceType.EXACT_PRICE)
        self.assertEqual(listing.rent, 75000)

    def test_starting_from_price_is_classified_as_starting_from(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani listing", "From KSh 75,000/month", "source", "https://x/from", criteria)
        self.assertEqual(listing.price_type, PriceType.STARTING_FROM)
        self.assertEqual(listing.rent, 75000)

    def test_variant_price_is_classified_as_variant(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani listing", "75,000 unfurnished / 150,000 furnished", "source", "https://x/variant", criteria)
        self.assertEqual(listing.price_type, PriceType.VARIANT_PRICE)
        self.assertEqual(listing.rent, 75000)

    def test_range_price_is_classified_as_price_range(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani listing", "100,000–140,000", "source", "https://x/range", criteria)
        self.assertEqual(listing.price_type, PriceType.PRICE_RANGE)
        self.assertIsNone(listing.rent)

    def test_conflicting_prices_are_classified_as_conflict(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani listing", "main price 120,000, description says 100,000", "source", "https://x/conflict", criteria)
        self.assertEqual(listing.price_type, PriceType.CONFLICT)
        self.assertIsNone(listing.rent)

    def test_repeated_identical_prices_remain_exact(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=60000)
        listing = extract_listing("2 bedroom Kilimani rent KSh 75,000", "The listed price is KSh 75,000 per month.", "source", "https://x/repeated", criteria)
        self.assertEqual(listing.price_type, PriceType.EXACT_PRICE)
        self.assertEqual(listing.rent, 75000)


if __name__ == "__main__":
    unittest.main()
