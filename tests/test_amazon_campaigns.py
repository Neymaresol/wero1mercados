import ast
import pathlib
import unittest
from urllib.parse import urlparse, parse_qs

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'main.py').read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)


def campaigns():
    for node in TREE.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'AMAZON_CURATED_CAMPAIGNS' for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError('Curated campaign list missing')


class AmazonCampaignTests(unittest.TestCase):
    def test_twelve_distinct_campaigns(self):
        items = campaigns()
        self.assertEqual(12, len(items))
        self.assertEqual(12, len({item[0] for item in items}))

    def test_links_and_categories(self):
        for sku, title, category, url in campaigns():
            with self.subTest(sku=sku):
                self.assertTrue(sku and title and category)
                parsed = urlparse(url)
                self.assertEqual('https', parsed.scheme)
                self.assertEqual('www.amazon.com.br', parsed.hostname)
                self.assertEqual(['wero1mercados-20'], parse_qs(parsed.query).get('tag'))
                self.assertTrue(parse_qs(parsed.query).get('linkId'))

    def test_five_new_categories(self):
        items = {item[0]: item for item in campaigns()}
        for sku in ('amazon-videogames-20261009', 'amazon-escritorio-20261009', 'amazon-moda-feminina-20261009', 'amazon-mercado-alimentos-20261009', 'amazon-moda-meninas-20261009'):
            self.assertIn(sku, items)

    def test_legacy_kindle_quarantine_present(self):
        self.assertIn('amazon-kindle-16gb-2024', SOURCE)
        self.assertIn('link.amazon', SOURCE)
        self.assertIn('UPDATE offers o SET active=FALSE', SOURCE)


if __name__ == '__main__':
    unittest.main()
