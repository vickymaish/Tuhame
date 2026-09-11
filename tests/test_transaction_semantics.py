import unittest

from agents.analyst import analyze
from main import parse_request
from schemas import EvidenceStatus, PricePeriod, PriceType, SearchCriteria, TransactionType
from tools.extraction import extract_listing
from tools.exa_tools import find_listings


class TransactionAndLocationTests(unittest.TestCase):
    def test_natural_language_locations_are_not_restricted(self):
        cases = [
            ("2 bedroom Kilimani under 85k with parking", "Kilimani"),
            ("2 bedroom Ruaka under 60k", "Ruaka"),
            ("3 bedroom somewhere around Nairobi under 100k", "Nairobi"),
            ("house near Westlands, open to nearby areas", "Westlands"),
            ("2 bedroom in Kiambu Road or Ruiru under 70k", "Kiambu Road"),
        ]
        for request, location in cases:
            criteria = parse_request(request)
            self.assertEqual(criteria.location, location)
            self.assertTrue(criteria.location_raw)

        broad = parse_request("house near Westlands, open to nearby areas")
        self.assertIsNone(broad.beds)
        self.assertIsNone(broad.max_rent)

        self.assertEqual(parse_request("2 bedroom Kilimani under 85k with parking").max_rent, 85000)
        self.assertEqual(parse_request("2 bedroom Ruaka under 60k").max_rent, 60000)

    def test_discovery_query_uses_arbitrary_location_text(self):
        criteria = parse_request("2 bedroom in Ruaka under 60k")
        self.assertEqual(criteria.locations, ["Ruaka"])
        self.assertIn("Ruaka", f"{criteria.location_raw}")

    def test_sale_price_is_not_rent(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=85000)
        listing = extract_listing("2 Bedroom Apartment for Sale", "KSh 15,000,000", "source", "https://x/sale", criteria)
        self.assertEqual(listing.transaction_type, TransactionType.SALE)
        self.assertEqual(listing.price_period, PricePeriod.TOTAL)
        self.assertEqual(listing.sale_price, 15000000)
        self.assertIsNone(listing.rent)
        self.assertTrue(any(item.claim == "transaction_type" for item in listing.evidence))
        _, rejected, _ = analyze([listing], criteria)
        self.assertIn("not monthly rent", rejected[0]["reason"])

    def test_daily_and_short_let_are_distinct_from_monthly_rent(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=85000)
        daily = extract_listing("2 Bedroom Furnished Apartment", "KSh 8,000 per day", "source", "https://x/daily", criteria)
        short_let = extract_listing("Apartment short let", "KSh 130,000 /mo", "source", "https://x/short", criteria)
        self.assertEqual(daily.transaction_type, TransactionType.RENT_DAILY)
        self.assertEqual(daily.price_period, PricePeriod.DAY)
        self.assertEqual(short_let.transaction_type, TransactionType.SHORT_LET)
        self.assertEqual(short_let.price_period, PricePeriod.MONTH)


if __name__ == "__main__":
    unittest.main()