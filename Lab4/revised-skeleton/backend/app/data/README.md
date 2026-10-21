# Static reference data

## `planning_area_to_hdb_town.json`

This file must map every URA planning area used by the app to an HDB town, because
HDB resale prices are published by HDB town rather than by URA subzone.

Expected shape:

```json
{
  "TAMPINES": "TAMPINES",
  "BEDOK": "BEDOK",
  "KALLANG": "KALLANG/WHAMPOA"
}
```

The file is intentionally empty in the skeleton. Populate it and add a validation
check during ingestion. Planning areas without an HDB town (for example, primarily
industrial or nature areas) should be mapped to `null` or omitted, and the pricing
control must emit a warning when no price proxy exists.

Do not infer the mapping from name equality alone; `Kallang` → `KALLANG/WHAMPOA`
is a counter-example.
