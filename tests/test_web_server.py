import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen
from threading import Thread

from schemas import PipelineResult, SearchCriteria, to_jsonable
from web_server import RouteGuardHandler, ThreadingHTTPServer, serve


class WebServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), RouteGuardHandler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_health_and_frontend_are_served(self):
        with urlopen(f"{self.base}/api/health") as response:
            self.assertEqual(json.loads(response.read())["status"], "ok")
        with urlopen(f"{self.base}/") as response:
            self.assertIn(b"RouteGuard", response.read())

    def test_search_endpoint_returns_pipeline_json(self):
        result = PipelineResult(criteria=SearchCriteria(beds=2, location="Kilimani", max_rent=85000), discovered=0, duplicates_removed=0)
        request = Request(f"{self.base}/api/search", data=b'{"request":"2 bedroom apartment in Kilimani under KSh 85000"}', headers={"Content-Type": "application/json"})
        with patch("web_server.run", return_value=result):
            with urlopen(request) as response:
                payload = json.loads(response.read())
        self.assertEqual(payload["result"]["discovered"], 0)

    def test_azure_deployment_files_exist(self):
        root = Path(__file__).resolve().parents[1]
        self.assertTrue((root / "Dockerfile").exists())
        self.assertTrue((root / "azure.yaml").exists())
        self.assertTrue((root / "startup.sh").exists())

    def test_serve_defaults_to_public_host_and_environment_port(self):
        with patch.dict(os.environ, {"PORT": "8080"}, clear=False):
            with patch("web_server.ThreadingHTTPServer") as mock_server:
                serve()
        binding = mock_server.call_args.args[0]
        self.assertEqual(binding[0], "0.0.0.0")
        self.assertEqual(binding[1], 8080)


if __name__ == "__main__":
    unittest.main()