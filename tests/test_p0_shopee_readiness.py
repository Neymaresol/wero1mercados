from p0_shopee_readiness import inspect_shopee

class Cursor:
    def __init__(self, rows): self.rows = rows
    def execute(self, query, params):
        assert "SELECT" in query and params == ("Shopee Brasil",)
    def fetchall(self): return self.rows

def test_shopee_fail_closed_even_when_active():
    data = inspect_shopee(Cursor([{"id": 116, "offer_active": True, "partner_active": True, "domain": "shopee.com.br", "authorized_url": "https://s.shopee.com.br/20wE9HOs46"}]))
    assert data["offers"][0]["ready_for_traffic"]
    assert not data["production_release_approved"]
    assert not data["attribution_verified"]

def test_shopee_inactive_and_external_host_blocked():
    data = inspect_shopee(Cursor([{"id": 116, "offer_active": False, "partner_active": False, "domain": "shopee.com.br", "authorized_url": "https://evil.example/path"}]))
    assert not data["offers"][0]["ready_for_traffic"]
    assert not data["offers"][0]["destination_allowed"]
