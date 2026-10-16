import unittest
from shopee_werozinha_config import (
    SHOPEE_WEROZINHA_URL, SHOPEE_SUB_ID, validate_shopee_link, shopee_werozinha_ready
)

class ShopeeWerozinhaLinkTests(unittest.TestCase):
    def test_approved_link(self):
        self.assertTrue(shopee_werozinha_ready())
        self.assertEqual(SHOPEE_SUB_ID, "wero1mercados")
        self.assertTrue(validate_shopee_link(SHOPEE_WEROZINHA_URL))

    def test_reject_unsafe_redirects(self):
        for url in [
            "http://s.shopee.com.br/5q8zszhUm7",
            "https://s.shopee.com.br.evil.test/5q8zszhUm7",
            "https://evil.test/5q8zszhUm7",
            "https://s.shopee.com.br/other",
            "https://s.shopee.com.br/5q8zszhUm7?redirect=evil",
            "https://s.shopee.com.br/5q8zszhUm7#fragment",
            "https://user@s.shopee.com.br/5q8zszhUm7",
        ]:
            with self.subTest(url=url):
                self.assertFalse(validate_shopee_link(url))

if __name__ == "__main__":
    unittest.main()
