import unittest
from commercial_evidence import Evidence


class CommercialEvidenceTests(unittest.TestCase):
    def test_redirect_is_not_a_sale(self):
        evidence = Evidence(True, True, False, False, False)
        self.assertEqual(evidence.status(), "AFFILIATE_OWNERSHIP_UNVERIFIED")

    def test_unverified_report_is_not_a_sale(self):
        evidence = Evidence(True, True, True, False, False)
        self.assertEqual(evidence.status(), "PARTNER_REPORT_NOT_AUTHENTICATED")

    def test_authenticated_report_without_sale(self):
        evidence = Evidence(True, True, True, True, False)
        self.assertEqual(evidence.status(), "NO_PARTNER_CONFIRMED_SALE")

    def test_confirmed_sale_requires_all_gates(self):
        evidence = Evidence(True, True, True, True, True)
        self.assertEqual(evidence.status(), "PARTNER_CONFIRMED_SALE")


if __name__ == "__main__":
    unittest.main()
