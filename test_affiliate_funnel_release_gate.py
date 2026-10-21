import unittest
from affiliate_funnel_release_gate import validate_affiliate_destination, intent_tier, release_gate

class ReleaseGateTests(unittest.TestCase):
    def test_hotmart(self):
        self.assertTrue(validate_affiliate_destination("hotmart", "https://go.hotmart.com/G108129576P"))
        self.assertFalse(validate_affiliate_destination("hotmart", "https://go.hotmart.com.evil.test/G108129576P"))
    def test_amazon(self):
        self.assertTrue(validate_affiliate_destination("amazon", "https://www.amazon.com.br/item?tag=wero1mercados-20"))
        self.assertFalse(validate_affiliate_destination("amazon", "https://www.amazon.com.br/item"))
    def test_shopee(self):
        self.assertTrue(validate_affiliate_destination("shopee", "https://s.shopee.com.br/20wE9HOs46"))
        self.assertFalse(validate_affiliate_destination("shopee", "https://s.shopee.com.br.evil.test/item"))
    def test_intent_provenance(self):
        self.assertEqual(intent_tier("a", "b", True, True), "INT.2")
        self.assertEqual(intent_tier("a", "a", True, True), "INT.1")
        self.assertEqual(intent_tier("a", "b", True, False), "INT.1")
        self.assertEqual(intent_tier("a", "b", False, False), "NONE")
    def test_go_live_fails_closed(self):
        url="https://go.hotmart.com/G108129576P"
        self.assertFalse(release_gate("hotmart", url)["go_live"])
        self.assertFalse(release_gate("hotmart", url, authorized=True)["go_live"])
        self.assertTrue(release_gate("hotmart", url, authorized=True, source_verified=True,
            redirect_tested=True, reconciliation_tested=True, rollback_tested=True,
            staging_isolated=True)["go_live"])

if __name__ == "__main__":
    unittest.main()
