"""Offline contract tests for TAG 01 and TAG 02 pilot."""
import unittest
from paradigma_tags import search_tag, trend_tag, match_catalog

class TagPilotTests(unittest.TestCase):
    def test_search_intent(self):
        tag = search_tag("Quero ver o preço da BMW X5")
        self.assertEqual(tag["terms"], ["bmw", "x5"])
        self.assertTrue(tag["eligible"])
        self.assertNotIn("user_id", tag)
        self.assertNotIn("query", tag)

    def test_trend_requires_authorized_aggregate_signal(self):
        blocked = trend_tag("Batom roxo degradê", 1000, 100, False, 1_000_000)
        self.assertFalse(blocked["eligible"])
        self.assertFalse(blocked["distribution_authorized"])
        approved_signal = trend_tag("Batom roxo degradê", 1000, 100, True, 1_000_000)
        self.assertTrue(approved_signal["eligible"])
        self.assertTrue(approved_signal["high_audience_signal"])
        self.assertFalse(approved_signal["distribution_authorized"])

    def test_catalog_only_approved_active(self):
        tag = search_tag("BMW X5")
        offers = [
            {"id": 1, "title": "BMW X5", "active": True, "approved": True},
            {"id": 2, "title": "BMW X5", "active": True, "approved": False},
            {"id": 3, "title": "BMW X5", "active": False, "approved": True},
            {"id": 4, "title": "Batom roxo", "active": True, "approved": True},
        ]
        self.assertEqual([o["id"] for o in match_catalog(tag, offers)], [1])

    def test_empty_query_no_matches(self):
        self.assertEqual(match_catalog(search_tag("eu quero ver"), []), [])

if __name__ == "__main__":
    unittest.main()
