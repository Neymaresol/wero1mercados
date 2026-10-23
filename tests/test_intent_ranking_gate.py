import unittest
from intent_ranking_gate import has_verified_intent, filter_verified_intent_offers

GOOD = {
    "source_authenticated": True,
    "int1_event_id": "server-landing-1",
    "int2_event_id": "server-detail-2",
    "int1_score": 1,
    "int2_score": 1,
}

class VerifiedIntentRankingTests(unittest.TestCase):
    def test_no_evidence_fails_closed(self):
        self.assertEqual(filter_verified_intent_offers([{"offer_id": 1}], {}), [])
        self.assertEqual(filter_verified_intent_offers([{"offer_id": 1}], None), [])

    def test_zero_score_blocks_even_if_clicks_exist(self):
        for field in ("int1_score", "int2_score"):
            with self.subTest(field=field):
                self.assertFalse(has_verified_intent({**GOOD, field: 0}))

    def test_untrusted_duplicate_or_missing_event_blocks(self):
        for change in (
            {"source_authenticated": False},
            {"source_authenticated": "true"},
            {"int2_event_id": "server-landing-1"},
            {"int1_event_id": ""},
            {"int2_event_id": None},
            {"int1_score": float("nan")},
            {"int2_score": float("inf")},
        ):
            with self.subTest(change=change):
                self.assertFalse(has_verified_intent({**GOOD, **change}))

    def test_only_authenticated_distinct_positive_scores_pass(self):
        offers = [{"offer_id": 1}, {"offer_id": 2}, {"offer_id": 3}]
        evidence = {1: GOOD, 2: {**GOOD, "int2_score": 0}, 3: {**GOOD, "source_authenticated": False}}
        self.assertEqual(filter_verified_intent_offers(offers, evidence), [{"offer_id": 1}])

if __name__ == "__main__":
    unittest.main()
