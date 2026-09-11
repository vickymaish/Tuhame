import unittest
from datetime import datetime, timezone

from schemas import SearchCriteria, Listing, Evidence, EvidenceStatus, Freshness, FreshnessState
from tools.dedup import compare_duplicate_cluster
from tools.planner import plan_investigation
from tools.interaction import update_property_evidence, reverify_listing


class Todo3InterfaceRegressionTests(unittest.TestCase):
    def make_listing(self, url="https://x/one") -> Listing:
        return Listing(
            source="source",
            url=url,
            beds=2,
            location="Kilimani",
            rent=70000,
            price_type="EXACT_PRICE",
            description="2 bedroom Kilimani listing",
            evidence=[Evidence(claim="rent", value=70000, evidence_text="KSh 70,000", source_url=url, observed_at=datetime.now(timezone.utc), status=EvidenceStatus.VERIFIED)],
            freshness=Freshness(state=FreshnessState.UNKNOWN, explanation="AGE UNKNOWN"),
            observed_at=datetime.now(timezone.utc),
            availability_status=EvidenceStatus.UNKNOWN,
            source_state={"page_status": "CURRENT", "canonical_url": url, "source_checked_at": None, "content_origin": "LIVE_PAGE"},
        )

    def test_duplicate_cluster_helper_detects_conflict_and_cluster_signals(self):
        left = self.make_listing("https://x/one")
        right = self.make_listing("https://x/one")
        result = compare_duplicate_cluster([left, right])
        self.assertEqual(result["status"], "CONFLICT")
        self.assertIn("same_property_cluster", result["signals"])

    def test_planner_returns_action_for_unknown_availability(self):
        listing = self.make_listing()
        listing.availability_status = EvidenceStatus.UNKNOWN
        plan = plan_investigation(listing)
        self.assertEqual(plan["decision"], "VERIFY")
        self.assertTrue(any(action["type"] == "VERIFY_AVAILABILITY" for action in plan["actions"]))

    def test_interaction_helpers_shape_evidence_update_and_reverify(self):
        listing = self.make_listing()
        update = update_property_evidence("L1", {"claim": "rent", "value": 70000})
        self.assertEqual(update["listing_id"], "L1")
        self.assertEqual(update["status"], "updated")
        verify = reverify_listing("L1", listing)
        self.assertEqual(verify["listing_id"], "L1")
        self.assertIn("status", verify)


if __name__ == "__main__":
    unittest.main()
