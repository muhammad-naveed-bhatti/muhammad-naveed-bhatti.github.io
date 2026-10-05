"""One-page check against the site's explicitly provided scraping sandbox."""
from collector import Client, extract
client = Client()
try:
    html, url = client.get('https://books.toscrape.com/')
    rows, next_url = extract(html, url)
    assert len(rows) == 20, f'Expected 20 catalogue entries, got {len(rows)}'
    assert next_url and all(r['product'] and r['price'] and r['currency'] == 'GBP' for r in rows)
    print(f'Live sandbox check passed: {len(rows)} records, prices/currency and next-page URL verified.')
finally:
    client.session.close()
