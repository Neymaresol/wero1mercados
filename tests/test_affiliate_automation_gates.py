import unittest
from affiliate_automation.gates import Offer, Decision, evaluate, publication_payload

BASE = dict(product_id="degrade", url="https://www.cursomanicure.com/degrade/?ref=G108129576P",
            affiliate_ref="G108129576P", affiliation_authorized=True,
            checkout_ref_verified=True, media_rights_confirmed=True,
            media_public_url="https://example.org/media/video.mp4")
class GateTests(unittest.TestCase):
    def test_happy_path_requires_approval(self):
        o = Offer(**BASE)
        self.assertEqual(evaluate(o).decision, Decision.READY)
        with self.assertRaises(ValueError): publication_payload(o, False)
        self.assertEqual(publication_payload(o, True)["media"], [BASE["media_public_url"]])
    def test_missing_checkout_blocks(self):
        self.assertIn("checkout_attribution_unverified", evaluate(Offer(**(BASE | {"checkout_ref_verified": False}))).reasons)
    def test_stripped_ref_blocks(self):
        self.assertIn("affiliate_url_invalid", evaluate(Offer(**(BASE | {"url": "https://example.org/course"}))).reasons)
    def test_unapproved_affiliation_blocks(self):
        self.assertEqual(evaluate(Offer(**(BASE | {"affiliation_authorized": False}))).decision, Decision.QUARANTINED)
    def test_local_media_blocks(self):
        self.assertIn("public_media_missing", evaluate(Offer(**(BASE | {"media_public_url": "/mnt/data/video.mp4"}))).reasons)
    def test_rights_blocks(self):
        self.assertIn("media_rights_unverified", evaluate(Offer(**(BASE | {"media_rights_confirmed": False}))).reasons)
if __name__ == "__main__":
    unittest.main()
