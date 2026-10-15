import unittest
from p0_amazon_affiliate_gate import amazon_affiliate_tag


class AmazonAffiliateGateTests(unittest.TestCase):
    def test_valid_tracking_tag(self):
        self.assertEqual(
            amazon_affiliate_tag("https://www.amazon.com.br/dp/B000?tag=example-20"),
            "example-20",
        )

    def test_missing_blank_or_duplicate_tag_is_blocked(self):
        for url in (
            "https://www.amazon.com.br/dp/B000",
            "https://amazon.com.br/s?k=tools&tag=",
            "https://amazon.com.br/dp/B000?tag=one-20&tag=two-20",
            "https://amazon.com.br/dp/B000?tag=%20",
        ):
            with self.subTest(url=url):
                self.assertIsNone(amazon_affiliate_tag(url))

    def test_external_hosts_and_insecure_urls_blocked(self):
        for url in (
            "https://amazon.com.br.evil.example/dp/B000?tag=example-20",
            "http://amazon.com.br/dp/B000?tag=example-20",
            "https://amazon.com.br@evil.example/dp/B000?tag=example-20",
            "https://amazon.com.br:444/dp/B000?tag=example-20",
            "https://s.shopee.com.br/123?tag=example-20",
        ):
            with self.subTest(url=url):
                self.assertIsNone(amazon_affiliate_tag(url))


if __name__ == "__main__":
    unittest.main()
