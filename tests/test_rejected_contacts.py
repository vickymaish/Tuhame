import unittest

from agents.analyst import analyze
from schemas import SearchCriteria
from tools.extraction import extract_listing


class RejectedContactTests(unittest.TestCase):
    def test_rejected_listing_keeps_public_contact_summary(self):
        criteria = SearchCriteria(beds=2, location="Kilimani", max_rent=85000)
        listing = extract_listing(
            "2 bedroom apartment for rent",
            "KSh 90,000 monthly. Email: adam@example.test. Office: 0710570715.",
            "agency.example",
            "https://agency.example/property/1",
            criteria,
        )
        _, rejected, _ = analyze([listing], criteria)
        self.assertEqual(rejected[0]["contactability"], "EMAIL")
        self.assertTrue(any(contact["value"] == "adam@example.test" for contact in rejected[0]["contacts"]))


if __name__ == "__main__":
    unittest.main()