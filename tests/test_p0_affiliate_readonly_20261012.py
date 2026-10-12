"""Opt-in GET-only tests. Do not request /go links: they record clicks."""
import json
import os
import unittest
from urllib.request import urlopen

BASE = os.getenv("WERO_MERCADOS_URL", "").rstrip("/")

@unittest.skipUnless(BASE, "WERO_MERCADOS_URL not set")
class AffiliateReadOnly(unittest.TestCase):
    def get(self, path):
        with urlopen(BASE + path, timeout=15) as response:
            self.assertEqual(response.status, 200)
            return json.load(response)

    def test_health(self):
        self.assertEqual(self.get("/health").get("status"), "ok")

    def test_public_offers_response(self):
        self.assertIsInstance(self.get("/api/offers"), (dict, list))

if __name__ == "__main__":
    unittest.main()
