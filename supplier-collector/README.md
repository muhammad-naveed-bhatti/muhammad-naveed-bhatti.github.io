# Supplier Catalogue Collector 1.0.0
By Muhammad Naveed · https://muhammad-naveed-bhatti.github.io/

A Windows desktop tool for collecting public catalogue records into Excel-ready CSV.

## Windows quick start
1. Download `Supplier-Catalogue-Collector-Windows.zip` from this repository's Releases.
2. Extract the complete ZIP into a folder.
3. Open `SupplierCatalogueCollector.exe` inside the extracted folder. Keep its `_internal` folder beside it.
4. Choose **Load offline demo** to try three fictional sample records without internet.
5. For a live demonstration, use `https://books.toscrape.com/`, set Max pages to 3, and click **Collect products**.
6. Review records, double-click to view the source, and choose **Export CSV**. Excel can open the CSV directly.

Windows x64; Python is bundled. Internet is needed only for live collection. No account, API key or subscription.
The executable is unsigned; Windows may show an unfamiliar-publisher warning. Verify the SHA256SUMS.txt checksum and publisher/source before deciding whether to run it. Do not disable antivirus.

## Supported sources
- Books to Scrape: purpose-built public practice catalogue with next-page support. Demo prices are fictional.
- Public HTML pages containing schema.org **Product JSON-LD**: product name, SKU, exact listed price, currency, availability and links, where provided. Paste product-page URLs one per line.
- Up to 25 input URLs and 25 requested product/catalogue pages per run. Robots requests and redirects are additional network requests.
- Automatic pagination is limited to Books to Scrape. Other sites need individual URLs or a future site-specific adapter.
- JavaScript-rendered data, login-only pages, CAPTCHA pages, and unsupported HTML layouts are not supported. A page returning zero records is reported, not guessed.

## Data handling
Records stay on your computer. There is no telemetry or cloud upload. Each export includes supplier, product, sku, price, currency, availability, product_url, source_url and collected_utc.
Missing fields stay blank. Currency conversions are not performed. Aggregate price ranges are not treated as an exact unit price. Listed prices are not binding quotations and may exclude delivery/tax. Check source pages before procurement decisions.
CSV cells are protected against spreadsheet-formula injection. Only public HTTP(S) destinations are supported; robots exclusions and crawl delays are respected. Requests are spaced at least 1.5 seconds apart. No access-control bypass is attempted.

## Quotation Analyzer handoff
Use the catalogue CSV as a research sheet. Select the same item/specification and currency across suppliers, confirm unit prices and delivery/tax/warranty terms, then enter verified quotations in the portfolio's Procurement Quotation Analyzer. This catalogue CSV is not its quotation-import template.

## Source / development
Python 3.12 with Tkinter.
```
python -m pip install -r requirements.txt
python app.py
python -m unittest discover -s tests -v
```
Build on Windows:
```
python -m pip install pyinstaller==6.22.0
python -m PyInstaller --noconfirm --clean --onedir --windowed --name SupplierCatalogueCollector app.py
```
The GitHub workflow runs extraction tests, builds Windows x64, launches a GUI smoke test, then publishes the ZIP and SHA-256 checksum as a Release.
