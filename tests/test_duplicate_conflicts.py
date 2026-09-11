import unittest
from datetime import datetime, timezone

from schemas import EvidenceStatus, FinancialCharge, FinancialStatus, Freshness, FreshnessState, Listing
from tools.dedup import compare_duplicate_cluster


class DuplicateConflictTests(unittest.TestCase):
    def make_listing(self, source, deposit_status, availability):
        return Listing(
            source=source,
            url=f"https://{source}.test/listing",
            beds=2,
            location="Kilimani",
            rent=75000,
            description="same property description",
            freshness=Freshness(state=FreshnessState.UNKNOWN, explanation="AGE UNKNOWN"),
            observed_at=datetime.now(timezone.utc),
            financial_charges=[FinancialCharge(name="deposit", amount=150000 if deposit_status == FinancialStatus.EXPLICIT_AMOUNT else None, status=deposit_status)],
            availability_status=availability,
        )

    def test_duplicate_sources_preserve_fee_and_availability_conflicts(self):
        result = compare_duplicate_cluster([
            self.make_listing("source-a", FinancialStatus.EXPLICIT_AMOUNT, EvidenceStatus.AVAILABLE),
            self.make_listing("source-b", FinancialStatus.NOT_MENTIONED, EvidenceStatus.UNKNOWN),
        ])

        self.assertEqual(result["status"], "CONFLICT")
        self.assertIn("deposit", result["signals"])
        self.assertIn("availability", result["signals"])
        self.assertIn("CONFLICT / FEE_AMBIGUITY: deposit", result["inconsistencies"])
        self.assertEqual(result["sources"], ["source-a", "source-b"])


if __name__ == "__main__":
    unittest.main()