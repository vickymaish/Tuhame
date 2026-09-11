import json
import unittest
from datetime import datetime, timezone

from report import render_report
from schemas import Freshness, Listing, PipelineResult, SearchCriteria, to_jsonable


class ReportTests(unittest.TestCase):
    def test_report_renders_source_image_and_link(self):
        listing = Listing(source="source", url="https://example.test/listing", beds=2, location="Kilimani", rent=50000, description="parking", freshness=Freshness(explanation="AGE UNKNOWN"), observed_at=datetime.now(timezone.utc), image_urls=["https://example.test/house.jpg"])
        result = PipelineResult(criteria=SearchCriteria(beds=2, location="Kilimani", max_rent=60000), discovered=1, duplicates_removed=0, survivors=[{"listing": listing, "match_reasons": ["within budget"]}])
        html = render_report(result)
        self.assertIn("https://example.test/house.jpg", html)
        self.assertIn("Open source listing", html)

    def test_to_jsonable_serializes_datetime_fields_for_json_round_trip(self):
        listing = Listing(source="source", url="https://example.test/listing", beds=2, location="Kilimani", rent=50000, description="parking", freshness=Freshness(explanation="AGE UNKNOWN"), observed_at=datetime.now(timezone.utc), image_urls=["https://example.test/house.jpg"])
        result = PipelineResult(criteria=SearchCriteria(beds=2, location="Kilimani", max_rent=60000), discovered=1, duplicates_removed=0, survivors=[{"listing": listing, "match_reasons": ["within budget"]}])

        payload = to_jsonable(result)
        serialized = json.dumps(payload, indent=2)

        self.assertIn('"observed_at"', serialized)
        self.assertNotIn("datetime", serialized)


if __name__ == "__main__":
    unittest.main()