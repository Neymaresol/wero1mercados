"""Offline P0 tests for diagnostic logic (no production access or fake sales)."""
import unittest

from p0_funnel_audit import audit_funnel


class FakeCursor:
    def __init__(self, responses):
        self.responses = list(responses)
        self.queries = []

    def execute(self, statement, parameters):
        sql = " ".join(statement.split())
        self.queries.append((sql, parameters))
        if not sql.upper().startswith("SELECT "):
            raise AssertionError("diagnostic must only issue SELECT")

    def fetchall(self):
        return self.responses.pop(0)


def valid_amazon_destination(url, domain):
    from urllib.parse import urlsplit
    if not url.startswith("https://") or urlsplit(url).hostname != "www.amazon.com.br" or domain != "amazon.com.br":
        raise ValueError("invalid")


class FunnelAuditOfflineTests(unittest.TestCase):
    def cursor(self, *, tag="wero1mercados-20"):
        return FakeCursor([
            [{"id": 802, "title": "Casa e Jardim - Amazon", "active": True,
              "partner_active": True, "domain": "amazon.com.br",
              "authorized_url": "https://www.amazon.com.br/s?k=casa&tag=" + tag}],
            [{"offer_id": 802, "channel": "facebook", "campaign": "casa-jardim-out26", "n": 22}],
            [{"offer_id": 802, "channel": "facebook", "campaign": "casa-jardim-out26", "n": 1},
             {"offer_id": 802, "channel": "social", "campaign": "werozinha-amazon", "n": 4}],
            [],
        ])

    def test_counts_are_per_campaign_not_human_or_sales(self):
        cur = self.cursor()
        report = audit_funnel(cur, valid_amazon_destination, (802,))
        offer = report["offers"][0]
        self.assertTrue(offer["active_authorized_url"])
        self.assertTrue(offer["amazon_associate_tag_matches_expected"])
        self.assertEqual(offer["landing_visits"], 22)
        self.assertEqual(offer["outbound_records"], 5)
        self.assertEqual(offer["diagnosis"], "PARTNER_CONVERSION_NOT_RECONCILED")
        self.assertIsNone(offer["partner_verified_sales"])
        self.assertEqual(len(cur.queries), 4)
        self.assertTrue(all("802" not in sql for sql, _ in cur.queries))
        self.assertTrue(all(params == ([802],) for _, params in cur.queries))
        by_campaign = {x["campaign"]: x for x in offer["campaigns"]}
        self.assertEqual(by_campaign["casa-jardim-out26"]["outbound_records"], 1)
        self.assertEqual(by_campaign["werozinha-amazon"]["outbound_evidence"], "UNVERIFIED_GET_REDIRECT")
        self.assertEqual(by_campaign["werozinha-amazon"]["landing_visits"], 0)
        self.assertNotIn("'authorized_url':", str(report))
        self.assertNotIn("https://", str(report))

    def test_missing_or_wrong_amazon_tag_is_diagnosed(self):
        report = audit_funnel(self.cursor(tag="another-account-20"), valid_amazon_destination, (802,))
        offer = report["offers"][0]
        self.assertFalse(offer["amazon_associate_tag_matches_expected"])
        self.assertEqual(offer["diagnosis"], "AMAZON_ASSOCIATE_TAG_NOT_MATCHED")

    def test_missing_offer_does_not_invent_events(self):
        cur = FakeCursor([[], [], [], []])
        report = audit_funnel(cur, valid_amazon_destination, (164,))
        offer = report["offers"][0]
        self.assertFalse(offer["found"])
        self.assertEqual(offer["status"], "NOT_FOUND")
        self.assertEqual(offer["outbound_records"], 0)
        self.assertIsNone(offer["partner_verified_sales"])

    def test_invalid_selection_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_funnel(FakeCursor([]), valid_amazon_destination, (-1,))
        with self.assertRaises(ValueError):
            audit_funnel(FakeCursor([]), valid_amazon_destination, range(1, 50))


if __name__ == "__main__":
    unittest.main()
