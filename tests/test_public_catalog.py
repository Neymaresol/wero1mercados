"""Public catalog contract checks without production DB or secrets."""
from unittest.mock import patch
from fastapi.testclient import TestClient
import main

class Cursor:
    def execute(self, sql):
        assert "o.active=TRUE AND p.active=TRUE" in sql
    def fetchall(self):
        return [
            {"id": 7, "title": "Oferta <teste>", "authorized_url": "https://go.hotmart.com/O107910953Y?dp=1", "partner_name": "Hotmart", "domain": "go.hotmart.com"},
            {"id": 8, "title": "Oferta indisponível", "authorized_url": "http://invalid.test", "partner_name": "Outro", "domain": "invalid.test"},
        ]
    def __enter__(self): return self
    def __exit__(self, *args): return False

class Connection:
    def cursor(self): return Cursor()
    def __enter__(self): return self
    def __exit__(self, *args): return False

def test_catalog_only_active_authorized_and_escaped():
    with patch.object(main, "db", return_value=Connection()):
        response = TestClient(main.app).get("/catalogo")
    assert response.status_code == 200
    assert 'href="/go/7?channel=catalogo"' in response.text
    assert "Oferta &lt;teste&gt;" in response.text
    assert "Oferta indisponível" not in response.text
    assert "<meta name=\"viewport\"" in response.text
