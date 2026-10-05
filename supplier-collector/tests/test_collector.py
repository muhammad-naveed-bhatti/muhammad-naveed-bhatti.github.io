import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from collector import DEMO_HTML, extract, export_csv, public_url, web_url, Client


class CollectorTests(unittest.TestCase):
    def test_sample_and_missing_values(self):
        rows, _ = extract(DEMO_HTML, 'https://example.com/demo', 'Test')
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]['currency'], 'PKR')
        self.assertEqual(rows[2]['availability'], 'OutOfStock')
        rows, _ = extract('<script type="application/ld+json">{"@type":"Product","name":"Bolt","offers":{"@type":"AggregateOffer","lowPrice":"1","highPrice":"3"}}</script>', 'https://example.com')
        self.assertEqual(rows[0]['price'], '')

    def test_nested_offers_and_malformed_json(self):
        h = '<script type="application/ld+json">bad</script><script type="application/ld+json">{"@graph":[{"@type":["Product"],"name":"Bolt","sku":"B1","offers":[{"price":0,"priceCurrency":"USD","url":"/bolt"},{"price":"2","priceCurrency":"USD"}]}]}</script>'
        rows, _ = extract(h, 'https://example.com/list')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['price'], '0')
        self.assertEqual(rows[0]['product_url'], 'https://example.com/bolt')

    def test_books_pagination(self):
        h = '<article class="product_pod"><h3><a title="Full title" href="book/index.html">Short</a></h3><p class="price_color">£12.34</p><p class="availability"> In stock </p></article><li class="next"><a href="page-2.html">next</a></li>'
        rows, next_url = extract(h, 'https://books.toscrape.com/catalogue/page-1.html')
        self.assertEqual(rows[0]['product'], 'Full title')
        self.assertEqual(rows[0]['price'], '12.34')
        self.assertEqual(next_url, 'https://books.toscrape.com/catalogue/page-2.html')

    def test_csv_excel_safety_and_unicode(self):
        rows, _ = extract(DEMO_HTML, 'https://example.com', '=cmd')
        rows[0]['product'] = 'حفاظتی دستانے, "large"'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'test.csv'
            export_csv(p, rows)
            with p.open(encoding='utf-8-sig', newline='') as f:
                result = list(csv.DictReader(f))
            self.assertEqual(result[0]['supplier'], "'=cmd")
            self.assertEqual(result[0]['product'], rows[0]['product'])

    def test_bad_urls(self):
        for url in ['file:///etc/passwd', 'https://user:pw@example.com', 'javascript:alert(1)', 'https://example.com:22/']:
            with self.assertRaises(ValueError):
                web_url(url)
        with patch('socket.getaddrinfo', return_value=[(None,None,None,None,('127.0.0.1', 0))]):
            with self.assertRaises(ValueError):
                public_url('https://example.com')

    def test_robot_exclusion(self):
        c = Client()
        with patch.object(c, 'raw', return_value=('User-agent: *\nDisallow: /private', 'https://example.com/robots.txt')):
            with self.assertRaises(ValueError):
                c.allowed('https://example.com/private')
            c.allowed('https://example.com/public')
        c.session.close()

if __name__ == '__main__':
    unittest.main()
