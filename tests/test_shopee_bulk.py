import unittest
from integrations.shopee_bulk import prepare_batch

class BulkIntakeTests(unittest.TestCase):
    def test_valid_draft_is_never_published(self):
        rows, errors = prepare_batch([{"title":"ALSONEW kit", "affiliate_url":"https://s.shopee.com.br/20wE9HOs46"}])
        self.assertFalse(errors)
        self.assertFalse(rows[0]["active"])
        self.assertIsNone(rows[0]["commission_brl"])
        self.assertIsNone(rows[0]["price_brl"])

    def test_duplicate_and_untrusted_domain_rejected(self):
        rows, errors = prepare_batch([
            {"title":"A", "affiliate_url":"https://s.shopee.com.br/20wE9HOs46"},
            {"title":"B", "affiliate_url":"https://s.shopee.com.br/20wE9HOs46"},
            {"title":"C", "affiliate_url":"https://shopee.com.br.evil.test/offer"}])
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(errors), 2)

    def test_existing_url_skipped(self):
        rows, errors = prepare_batch([{"title":"A", "affiliate_url":"https://s.shopee.com.br/20wE9HOs46"}],
                                     existing_urls={"https://s.shopee.com.br/20wE9HOs46"})
        self.assertEqual(len(rows), 0)
        self.assertEqual(len(errors), 1)

    def test_batch_limit(self):
        with self.assertRaises(ValueError):
            prepare_batch([{}] * 501)
