import unittest
from commercial_readiness import assess_channels, acquisition_gaps


class ReadinessTests(unittest.TestCase):
    def test_never_claim_live_from_flags(self):
        result = assess_channels(
            {"instagram": True}, {"instagram": True}, {"instagram": True}
        )
        self.assertEqual(result[0].status, "READY_FOR_LIVE_VALIDATION")
        self.assertEqual(result[1].status, "CREDENTIALS_MISSING")
        self.assertEqual(len(result), 4)

    def test_permission_and_enablement_are_required(self):
        result = assess_channels(
            {"tiktok": True, "kwai": True},
            {"tiktok": False, "kwai": True},
            {"tiktok": True, "kwai": False},
        )
        self.assertEqual(result[2].status, "PERMISSION_NOT_VERIFIED")
        self.assertEqual(result[3].status, "DISABLED")

    def test_gaps_preserve_confirmed_sales_boundary(self):
        self.assertEqual(
            acquisition_gaps(active_offers=12, clicks=4, confirmed_sales=0),
            ["NO_CONFIRMED_CONVERSIONS"],
        )
        self.assertEqual(
            acquisition_gaps(active_offers=0, clicks=0, confirmed_sales=0),
            ["NO_ACTIVE_OFFERS", "NO_TRACKED_TRAFFIC", "NO_CONFIRMED_CONVERSIONS"],
        )
        with self.assertRaises(ValueError):
            acquisition_gaps(active_offers=-1, clicks=0, confirmed_sales=0)


if __name__ == "__main__":
    unittest.main()
