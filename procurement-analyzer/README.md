# Procurement Quotation Analyzer

A procurement decision-support portfolio project by Muhammad Naveed Bhatti.

Compare supplier quotations for the same item, specification, quantity and currency. Includes editable quotations, CSV template/import, cost breakdown, delivery/warranty requirements, weighted ranking, CSV report export and printable reports.

## Cost calculation

Gross goods = quantity × unit price. Discount applies to gross goods; tax applies to discounted goods. Total = discounted goods + tax + freight. Freight is an inclusive total; freight taxes, if any, must be included there. Other fees/duties are not calculated. Monetary calculations use JavaScript floating-point numbers; displayed amounts are rounded to two decimals. This is a comparison tool, not an accounting ledger.

## Ranking

Only suppliers meeting delivery and warranty requirements are scored. A delivery limit of zero disables that constraint. Eligible suppliers receive min/max normalized scores for cost, delivery and warranty, with configurable nonnegative weights normalized to 100%. Identical criterion values receive full marks. Scores depend on the current set of eligible suppliers. Highest-score ties are explicitly reported. Display tie-breaks: lower total, shorter delivery, supplier name.

Commercial award still requires specification, quality, compliance and supplier verification. Fictional sample data is provided.

## Run

No dependencies, API key, server or payment required by the application. Open `index.html` locally or serve this directory with `python -m http.server 8000`. GitHub Pages serves the same files.

All input is processed in the browser; no application upload or persistent storage is used. Reloading resets data. CSV import supports up to 50 supplier rows and 250 KB; it replaces current supplier rows while keeping purchase requirements. Export before reloading to retain the comparison.

CSV columns: `supplier,unitPrice,discount,tax,freight,days,warranty`. Quotes containing commas must use standard double-quoted CSV fields. No currency conversion is performed. CSV exports protect formula-leading text to reduce spreadsheet formula injection.
