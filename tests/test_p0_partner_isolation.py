import unittest

from p0_partner_isolation import eligible_partner_offer


class PartnerIsolationTests(unittest.TestCase):
    def setUp(self):
        self.offer = {
            "id": 116, "partner_id": 10, "partner_name": "Shopee",
            "domain": "shopee.com.br",
            "authorized_url": "https://s.shopee.com.br/example",
            "offer_active": True, "partner_active": True,
        }

    def test_eligible_requires_both_active(self):
        self.assertTrue(eligible_partner_offer(self.offer))
        for field in ("offer_active", "partner_active"):
            row = {**self.offer, field: False}
            self.assertFalse(eligible_partner_offer(row))
            row[field] = None
            self.assertFalse(eligible_partner_offer(row))

    def test_partner_identity_is_required(self):
        for field, value in (("partner_id", 0), ("partner_id", None),
                             ("partner_id", True), ("id", -1),
                             ("partner_name", ""), ("domain", ""),
                             ("authorized_url", "")):
            self.assertFalse(eligible_partner_offer({**self.offer, field: value}))

    def test_offer_never_changes_partner(self):
        amazon = {**self.offer, "id": 20, "partner_id": 1,
                  "partner_name": "Amazon", "domain": "amazon.com.br",
                  "authorized_url": "https://amazon.com.br/product"}
        self.assertTrue(eligible_partner_offer(amazon))
        self.assertTrue(eligible_partner_offer(self.offer))
        self.assertNotEqual(amazon["partner_id"], self.offer["partner_id"])


if __name__ == "__main__":
    unittest.main()
