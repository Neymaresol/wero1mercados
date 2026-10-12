"""Exercise the production URL validator offline, without importing the DB-backed app."""
import ast
from pathlib import Path
from urllib.parse import urlparse
import unittest

source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
tree = ast.parse(source)
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate_authorized_url")
module = ast.Module(body=[function], type_ignores=[])

class HTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail

namespace = {"urlparse": urlparse, "HTTPException": HTTPException}
exec(compile(ast.fix_missing_locations(module), "<validated-function>", "exec"), namespace)
validate = namespace["validate_authorized_url"]

class PartnerURLTests(unittest.TestCase):
    def test_authorized_https(self):
        for url in ("https://amazon.com.br/a", "https://www.amazon.com.br/a", "https://amazon.com.br:443/a"):
            with self.subTest(url=url):
                self.assertIsNone(validate(url, "amazon.com.br"))

    def test_reject_unsafe_urls(self):
        urls = [
            "http://amazon.com.br/a", "https://amazon.com.br.evil.test/a",
            "https://evil.test/@amazon.com.br", "https://user:pass@amazon.com.br/a",
            "https://amazon.com.br:444/a", "https://amazon.com.br:bad/a",
            "https://amazon.com.br@evil.test/a", "https:///nohost",
        ]
        for url in urls:
            with self.subTest(url=url), self.assertRaises(HTTPException):
                validate(url, "amazon.com.br")

    def test_invalid_partner_domain(self):
        for domain in ("", "amazon.com.br:443", "amazon.com.br/path"):
            with self.subTest(domain=domain), self.assertRaises(HTTPException):
                validate("https://amazon.com.br/a", domain)

if __name__ == "__main__":
    unittest.main()
