import unittest

from main import parse_request


class IntakeTests(unittest.TestCase):
    def test_frontend_query_preserves_requested_criteria(self):
        criteria = parse_request("2-bedroom Kilimani, max KES 85000, parking")
        self.assertEqual(criteria.beds, 2)
        self.assertEqual(criteria.location, "Kilimani")
        self.assertEqual(criteria.max_rent, 85000)
        self.assertEqual(criteria.must_haves, ["parking"])

    def test_user_can_choose_another_location(self):
        criteria = parse_request("2 bedroom apartment in Westlands under KSh 95000 with parking")
        self.assertEqual(criteria.location, "Westlands")
        self.assertEqual(criteria.max_rent, 95000)

    def test_location_can_be_omitted(self):
        criteria = parse_request("2 bedroom apartment under KSh 95000 with parking")
        self.assertEqual(criteria.location, "")
    def test_budget_is_taken_from_user_request(self):
        criteria = parse_request("2-bedroom Kilimani, max KES 85000, parking")
        self.assertEqual(criteria.max_rent, 85000)

    def test_different_budget_is_preserved(self):
        criteria = parse_request("3-bedroom Westlands, under 120,000")
        self.assertEqual(criteria.beds, 3)
        self.assertEqual(criteria.location, "Westlands")
        self.assertEqual(criteria.max_rent, 120000)


if __name__ == "__main__":
    unittest.main()