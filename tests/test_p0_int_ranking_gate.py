"""Offline unittest contracts; no HTTP, database writes, clicks or conversions."""
import unittest
from hotmart_intent_funnel import IntentEvent
from p0_int_ranking_gate import eligible_int_ranking


def offer(offer_id, **overrides):
    row = {"offer_id": offer_id, "active": True,
           "partner_active": True, "affiliate_authorized": True}
    row.update(overrides)
    return row


class P0IntRankingGateTests(unittest.TestCase):
    def test_unverified_source_fails_closed(self):
        evidence = {1: [IntentEvent("campaign_landing", True, "a")]}
        self.assertEqual(eligible_int_ranking([offer(1)], evidence), [])
        self.assertEqual(eligible_int_ranking([offer(1)], evidence, source_authenticated=1), [])

    def test_zero_int_scores_never_enter_ranking(self):
        self.assertEqual(eligible_int_ranking([offer(1)], {1: []}, source_authenticated=True), [])
        self.assertEqual(eligible_int_ranking(
            [offer(1)], {1: [IntentEvent("offer_detail", True, "x")]},
            source_authenticated=True), [])

    def test_untrusted_events_and_inactive_offers_excluded(self):
        evidence = {1: [IntentEvent("campaign_landing", False, "a")],
                    2: [IntentEvent("campaign_landing", True, "b")]}
        self.assertEqual(eligible_int_ranking([offer(1), offer(2, active=False)], evidence,
                                              source_authenticated=True), [])

    def test_authenticated_int2_precedes_int1(self):
        evidence = {1: [IntentEvent("campaign_landing", True, "a")],
                    2: [IntentEvent("campaign_landing", True, "b"),
                        IntentEvent("offer_detail", True, "c")]}
        self.assertEqual(eligible_int_ranking([offer(1), offer(2)], evidence,
                                              source_authenticated=True), [
            {"offer_id": 2, "intent_tier": "INT.2"},
            {"offer_id": 1, "intent_tier": "INT.1"},
        ])

    def test_duplicate_event_id_does_not_create_int2(self):
        evidence = {1: [IntentEvent("campaign_landing", True, "same"),
                        IntentEvent("offer_detail", True, "same")]}
        self.assertEqual(eligible_int_ranking([offer(1)], evidence, source_authenticated=True), [
            {"offer_id": 1, "intent_tier": "INT.1"}
        ])

    def test_authorization_and_limit(self):
        evidence = {1: [IntentEvent("campaign_landing", True, "a")],
                    2: [IntentEvent("campaign_landing", True, "b")]}
        self.assertEqual(eligible_int_ranking(
            [offer(1, affiliate_authorized=False), offer(2)], evidence,
            source_authenticated=True, limit=1), [
                {"offer_id": 2, "intent_tier": "INT.1"}
            ])
        with self.assertRaises(ValueError):
            eligible_int_ranking([], {}, source_authenticated=True, limit=0)


if __name__ == "__main__":
    unittest.main()
