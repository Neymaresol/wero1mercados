import unittest
from decimal import Decimal
from hotmart_intent_funnel import IntentEvent, classify, allowed_hotlink, simulate_retained_commission

class FunnelTests(unittest.TestCase):
    def test_zero_or_untrusted(self):
        self.assertEqual(classify([]), "NONE")
        self.assertEqual(classify([IntentEvent("campaign_landing", False, "x")]), "NONE")
    def test_intent(self):
        self.assertEqual(classify([IntentEvent("campaign_landing", True, "a")]), "INT.1")
        self.assertEqual(classify([IntentEvent("campaign_landing", True, "a"), IntentEvent("offer_detail", True, "b")]), "INT.2")
    def test_hotlink(self):
        self.assertTrue(allowed_hotlink("https://go.hotmart.com/G108129576P"))
        self.assertFalse(allowed_hotlink("https://evil.example/G108129576P"))
    def test_retained_simulation(self):
        r=simulate_retained_commission("100.00", "0.40")
        self.assertEqual(r["commission"], "40.00")
        self.assertFalse(r["provider_confirmed"])
        self.assertEqual(r["bank_transfer"], "NOT_REQUESTED")

if __name__ == "__main__":
    unittest.main()
