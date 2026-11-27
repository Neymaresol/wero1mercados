import unittest

from int_qualification import INT_GATE_STATUS, filter_int_qualified_offers


class IntQualificationFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.offers = [{"offer_id": 1}, {"offer_id": 2}]

    def test_missing_evidence_blocks_every_offer(self):
        self.assertEqual(filter_int_qualified_offers(self.offers), [])
        self.assertEqual(filter_int_qualified_offers(self.offers, {}), [])

    def test_forged_authentication_and_positive_scores_do_not_bypass(self):
        fake = {1: {"source_authenticated": True, "int1_event_id": "a",
                    "int2_event_id": "b", "int1_score": 100, "int2_score": 100}}
        self.assertEqual(filter_int_qualified_offers(self.offers, fake), [])

    def test_zero_int1_or_int2_blocks(self):
        for field in ("int1_score", "int2_score"):
            with self.subTest(field=field):
                fake = {1: {"source_authenticated": True, "int1_event_id": "a",
                            "int2_event_id": "b", "int1_score": 1, "int2_score": 1}}
                fake[1][field] = 0
                self.assertEqual(filter_int_qualified_offers(self.offers, fake), [])

    def test_replay_and_cross_offer_ids_block(self):
        fake = {
            1: {"source_authenticated": True, "int1_event_id": "same",
                "int2_event_id": "same", "int1_score": 1, "int2_score": 1},
            2: {"source_authenticated": True, "int1_event_id": "same",
                "int2_event_id": "other", "int1_score": 1, "int2_score": 1},
        }
        self.assertEqual(filter_int_qualified_offers(self.offers, fake), [])

    def test_does_not_mutate_source_offers(self):
        original = list(self.offers)
        self.assertEqual(filter_int_qualified_offers(self.offers), [])
        self.assertEqual(self.offers, original)
        self.assertEqual(INT_GATE_STATUS, "BLOCKED_NO_VERIFIED_EVENT_PIPELINE")


if __name__ == "__main__":
    unittest.main()
