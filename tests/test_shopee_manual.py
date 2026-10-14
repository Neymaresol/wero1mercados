import unittest
from integrations.shopee_manual import ShopeeAffiliateOffer

class ShopeeManualTests(unittest.TestCase):
    def test_unapproved_is_hidden(self):
        self.assertIsNone(ShopeeAffiliateOffer("Item", "https://shope.ee/example").public_link())

    def test_approved_link_is_preserved(self):
        url = "https://s.shopee.com.br/example"
        self.assertEqual(ShopeeAffiliateOffer("Item", url, True).public_link(), url)

    def test_rejects_host_spoofing(self):
        with self.assertRaises(ValueError):
            ShopeeAffiliateOffer("Item", "https://shopee.com.br.evil.test/a", True).public_link()

if __name__ == "__main__":
    unittest.main()
