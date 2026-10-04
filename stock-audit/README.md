# Warehouse Stock Audit

Browser-based inventory reconciliation project by Muhammad Naveed Bhatti. Compare recorded quantities with physical counts; review shortages/excess, count match rate and PKR value differences; record local adjustments with reason and name; import and export CSV; print reports.

Blank physical count means pending. Zero means counted and empty. Variance is physical minus recorded stock. Match rate is matched counted rows divided by counted rows. Mixed units are never summed. Shortage and excess monetary values are shown separately using supplied unit costs. One row per item/location; negative quantities and duplicate keys are rejected.

Adjustments replace this tool's recorded quantity with physical quantity and append before/after values, date, reason and name to browser history. They do not update any external system. History is self-reported and editable through browser storage, not an authenticated audit trail. Browser storage may be blocked or cleared; export records for retention. Import and sample reset replace only count-sheet items and retain history.

No dependencies, payment or API keys. Open index.html locally or use GitHub Pages. All application data stays in the browser. Maximum 500 items, 1 MB CSV and 10,000 history entries. CSV headers: itemCode,itemName,location,unit,bookQty,physicalQty,unitCost. Excel users can save a sheet as CSV in this format. XLSX is not directly imported. Values use JavaScript numbers; display rounds monetary amounts to two decimals. This is a portfolio reconciliation tool, not an accounting system.
