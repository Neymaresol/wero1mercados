"""Offline P0 contract checks; no synthetic events are sent to production."""
import unittest
from urllib.parse import urlparse

def safe_affiliate_destination(url, domains):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and any(host == d or host.endswith("." + d) for d in domains)

def confirmed_commission(event):
    return event.get("commission_brl", 0) if event.get("partner_authenticated") is True and event.get("status") == "confirmed" else 0

class FunnelContracts(unittest.TestCase):
    def test_spoofed_partner_url(self):
        self.assertFalse(safe_affiliate_destination("https://amazon.com.br.evil.test/item", {"amazon.com.br"}))
    def test_authorized_redirect(self):
        self.assertTrue(safe_affiliate_destination("https://www.amazon.com.br/item", {"amazon.com.br"}))
    def test_click_is_not_sale(self):
        self.assertEqual(confirmed_commission({"status":"clicked","commission_brl":100}), 0)
    def test_unverified_conversion_not_counted(self):
        self.assertEqual(confirmed_commission({"status":"confirmed","commission_brl":100}), 0)
    def test_partner_confirmed_conversion(self):
        self.assertEqual(confirmed_commission({"status":"confirmed","partner_authenticated":True,"commission_brl":100}), 100)

if __name__ == "__main__":
    unittest.main()
