"""Public catalogue extraction. No login, browser automation, or credentials."""
import csv
import ipaddress
import json
import re
import socket
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, urldefrag
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

VERSION = '1.0.0'
AGENT = 'NaveedCatalogueCollector/1.0'
FIELDS = ['supplier', 'product', 'sku', 'price', 'currency', 'availability', 'product_url', 'source_url', 'collected_utc']
DEMO_HTML = '''<script type="application/ld+json">{"@graph":[
{"@type":"Product","name":"Safety gloves (sample)","sku":"DEMO-001","offers":{"price":"450.00","priceCurrency":"PKR","availability":"https://schema.org/InStock"}},
{"@type":"Product","name":"Storage bin (sample)","sku":"DEMO-002","offers":{"price":"1250.00","priceCurrency":"PKR","availability":"https://schema.org/InStock"}},
{"@type":"Product","name":"Packing tape (sample)","sku":"DEMO-003","offers":{"price":"190.00","priceCurrency":"PKR","availability":"https://schema.org/OutOfStock"}}
]}</script>'''


def clean(value):
    return re.sub(r'\s+', ' ', str(value if value is not None else '')).strip()


def web_url(url):
    p = urlsplit(url)
    if p.scheme not in ('https', 'http') or not p.hostname or p.username or p.password or p.port not in (None, 80, 443):
        raise ValueError('Use a public http/https URL without credentials or a custom port.')
    return urldefrag(url)[0]


def public_url(url):
    url = web_url(url)
    addresses = socket.getaddrinfo(urlsplit(url).hostname, None)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Local and private network addresses are not supported.')
    return url


def safe_link(base, value):
    try:
        return web_url(urljoin(base, clean(value)))
    except (ValueError, TypeError):
        return ''


def walk_products(value):
    if isinstance(value, list):
        for item in value:
            yield from walk_products(item)
    elif isinstance(value, dict):
        kinds = value.get('@type', [])
        if isinstance(kinds, str):
            kinds = [kinds]
        if 'Product' in kinds or 'https://schema.org/Product' in kinds:
            yield value
        for child in value.values():
            if isinstance(child, (dict, list)):
                yield from walk_products(child)


def extract(html, url, supplier=''):
    soup = BeautifulSoup(html, 'html.parser')
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    rows = []
    def row(name, sku='', price='', currency='', availability='', link=''):
        if not clean(name):
            return
        rows.append(dict(zip(FIELDS, [clean(supplier) or urlsplit(url).hostname, clean(name), clean(sku), clean(price), clean(currency), clean(availability), safe_link(url, link), url, stamp])))
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue
        for p in walk_products(data):
            offers = p.get('offers', {})
            if not isinstance(offers, list):
                offers = [offers]
            if not offers:
                offers = [{}]
            for offer in offers:
                if not isinstance(offer, dict):
                    continue
                # AggregateOffer ranges are deliberately not represented as exact prices.
                price = offer.get('price', '')
                spec = offer.get('priceSpecification', {})
                if price == '' and isinstance(spec, dict):
                    price = spec.get('price', '')
                currency = offer.get('priceCurrency', '') or (spec.get('priceCurrency', '') if isinstance(spec, dict) else '')
                row(p.get('name', ''), p.get('sku', ''), price, currency,
                    str(offer.get('availability', '')).rsplit('/', 1)[-1], offer.get('url') or p.get('url') or url)
    if urlsplit(url).hostname == 'books.toscrape.com':
        for card in soup.select('article.product_pod'):
            a, price, stock = card.select_one('h3 a'), card.select_one('.price_color'), card.select_one('.availability')
            if a:
                amount = price.get_text(strip=True) if price else ''
                row(a.get('title') or a.get_text(), price=amount.replace('£', '').replace('Â', ''), currency='GBP' if '£' in amount else '', availability=stock.get_text(' ', strip=True) if stock else '', link=a.get('href', ''))
    unique = {}
    for r in rows:
        key = tuple(r[k] for k in FIELDS if k != 'collected_utc')
        unique[key] = r
    next_page = ''
    if urlsplit(url).hostname == 'books.toscrape.com':
        a = soup.select_one('li.next a')
        if a:
            next_page = safe_link(url, a.get('href', ''))
    return list(unique.values()), next_page


class Client:
    def __init__(self, stop=None):
        self.stop = stop or threading.Event()
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers['User-Agent'] = AGENT
        self.rules = {}
        self.last_request = 0
        self.delay = 1.5

    def raw(self, url, redirects=0, check_rules=False):
        if redirects > 4:
            raise ValueError('Too many redirects.')
        public_url(url)
        if check_rules:
            self.allowed(url)
        if self.stop.wait(max(0, self.delay - (time.monotonic() - self.last_request))):
            raise InterruptedError('Stopped; collected records are available to export.')
        self.last_request = time.monotonic()
        with self.session.get(url, timeout=(10, 20), allow_redirects=False, stream=True) as response:
            if response.is_redirect:
                return self.raw(urljoin(url, response.headers.get('Location', '')), redirects + 1, check_rules)
            if response.status_code == 429:
                raise ValueError('Website rate limit reached. Please try later.')
            response.raise_for_status()
            chunks, size = [], 0
            for chunk in response.iter_content(65536):
                if self.stop.is_set():
                    raise InterruptedError('Stopped.')
                size += len(chunk)
                if size > 3_000_000:
                    raise ValueError('Page exceeds the 3 MB limit.')
                chunks.append(chunk)
            data = b''.join(chunks)
            return data.decode(response.encoding if response.encoding and response.encoding.lower() != 'iso-8859-1' else 'utf-8', errors='replace'), url

    def allowed(self, url):
        p = urlsplit(url)
        origin = f'{p.scheme}://{p.netloc}'
        if origin not in self.rules:
            parser = RobotFileParser()
            try:
                text, _ = self.raw(origin + '/robots.txt')
                parser.parse(text.splitlines())
            except requests.HTTPError as exc:
                if exc.response.status_code == 404:
                    parser.parse([])
                else:
                    raise ValueError('Could not check robots.txt. This site was skipped.') from exc
            self.rules[origin] = parser
        parser = self.rules[origin]
        if not parser.can_fetch(AGENT, url):
            raise ValueError('This path is excluded by robots.txt.')
        self.delay = max(1.5, parser.crawl_delay(AGENT) or 0)

    def get(self, url):
        return self.raw(url, check_rules=True)


def csv_cell(value):
    value = str(value)
    if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')):
        return "'" + value
    return value


def export_csv(path, rows):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({k: csv_cell(row.get(k, '')) for k in FIELDS} for row in rows)
