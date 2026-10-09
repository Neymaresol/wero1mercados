import unittest

from ai_acquisition import Campaign, recommend_campaigns


class AcquisitionTests(unittest.TestCase):
    def test_only_active_authorized_https_offers(self):
        offers = [
            Campaign(1, "Eletronicos", "https://amazon.com.br/test", True, True),
            Campaign(2, "Inativo", "https://amazon.com.br/test", False, True),
            Campaign(3, "Inseguro", "http://example.com", True, True),
            Campaign(4, "Parceiro inativo", "https://example.com", True, False),
        ]
        result = recommend_campaigns(offers, "instagram")
        self.assertEqual([item.offer_id for item in result], [1])
        self.assertTrue(result[0].requires_approval)
        self.assertIn("Publicidade", result[0].disclosure)

    def test_reject_credentials_and_missing_titles(self):
        offers = [
            Campaign(1, "Secret", "https://user:pass@example.com/path", True, True),
            Campaign(2, None, "https://example.com/path", True, True),
            Campaign(3, "Valid", "https://example.com/path", True, True),
        ]
        self.assertEqual(
            [item.offer_id for item in recommend_campaigns(offers, "facebook")],
            [3],
        )

    def test_channel_allowlist(self):
        with self.assertRaises(ValueError):
            recommend_campaigns([], "email-spam")

    def test_limit(self):
        offers = [Campaign(i, f"Oferta {i}", "https://example.com", True, True) for i in range(5)]
        self.assertEqual(len(recommend_campaigns(offers, "kwai", limit=2)), 2)


if __name__ == "__main__":
    unittest.main()
