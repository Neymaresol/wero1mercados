"""Regression: zero-INT offers must not be ranked or misreported as absent."""
import unittest

from p0_acquisition_rules import acquisition_decision


class AcquisitionDecisionTests(unittest.TestCase):
    def test_empty_catalog(self):
        self.assertEqual(
            acquisition_decision(active_offers=0, ranked_clicks=0, pending_conversions=0, confirmed_sales=0)[0],
            "NO_ACTIVE_OFFERS",
        )

    def test_active_catalog_without_clicks(self):
        self.assertEqual(
            acquisition_decision(active_offers=19, ranked_clicks=0, pending_conversions=0, confirmed_sales=0),
            ("NO_TRACKED_TRAFFIC", "DISTRIBUTE_TRACKED_CAMPAIGNS"),
        )

    def test_clicks_without_partner_conversion(self):
        self.assertEqual(
            acquisition_decision(active_offers=19, ranked_clicks=55, pending_conversions=0, confirmed_sales=0)[0],
            "NO_CONVERSION_SIGNAL",
        )

    def test_pending_without_confirmation(self):
        self.assertEqual(
            acquisition_decision(active_offers=19, ranked_clicks=2, pending_conversions=1, confirmed_sales=0)[0],
            "PENDING_WITHOUT_CONFIRMED_SALE",
        )

    def test_confirmed_sale(self):
        self.assertEqual(
            acquisition_decision(active_offers=19, ranked_clicks=2, pending_conversions=0, confirmed_sales=1)[0],
            "FUNNEL_CONVERTING",
        )


if __name__ == "__main__":
    unittest.main()
