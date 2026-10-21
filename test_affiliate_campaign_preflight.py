import unittest
from affiliate_campaign_preflight import Campaign, check_campaign

class CampaignPreflightTests(unittest.TestCase):
    def test_tiktok_png_blocked(self):
        c=Campaign("amazon","https://www.amazon.com.br/item?tag=wero1mercados-20",True,True,True,"image/png","tiktok")
        self.assertFalse(check_campaign(c)["ready_to_submit_for_review"])
        self.assertFalse(check_campaign(c)["checks"]["tiktok_media_supported"])
    def test_tiktok_jpeg_eligible_for_review(self):
        c=Campaign("amazon","https://www.amazon.com.br/item?tag=wero1mercados-20",True,True,True,"image/jpeg","tiktok")
        self.assertTrue(check_campaign(c)["ready_to_submit_for_review"])
    def test_shopee_inactive_blocked(self):
        c=Campaign("shopee","https://s.shopee.com.br/20wE9HOs46",False,True,True,"image/jpeg","facebook")
        self.assertFalse(check_campaign(c)["ready_to_submit_for_review"])
    def test_hotmart_missing_approval_blocked(self):
        c=Campaign("hotmart","https://go.hotmart.com/G108129576P",True,False,False,"image/jpeg","facebook")
        self.assertFalse(check_campaign(c)["ready_to_submit_for_review"])
    def test_invalid_host_blocked(self):
        c=Campaign("hotmart","https://go.hotmart.com.evil.test/G108129576P",True,True,True,"image/jpeg","facebook")
        self.assertFalse(check_campaign(c)["ready_to_submit_for_review"])

if __name__ == "__main__":
    unittest.main()
