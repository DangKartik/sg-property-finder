# Data snapshots and fallbacks

`bootstrap.buildContext()` looks for these files in this directory:

```text
subzones.geojson
planning_area_to_hdb_town.json
amenities.json
environment_baselines.json
hdb_resale.csv
commute_matrix.json
```

The small files in `backend/tests/fixtures/` show the expected shapes. The
following real assets are already populated:

- `subzones.geojson` (URA 332 subzones)
- `hdb_resale.csv` (HDB resale transactions)
- `planning_area_to_hdb_town.json`
- `environment_baselines.json`
- `commute_matrix.json`

`amenities.json` is **not** included yet. Without it, factsheets return an empty
amenity list with a `MISSING_SOURCE_DATA` warning and amenity scores are zero.

## `subzones.geojson`

Use the URA **Master Plan 2019 Subzone Boundary (No Sea) (GEOJSON)** dataset:
`d_8594ae9ff96d0c708bc2af633048edfb` on data.gov.sg.

The loader accepts `SUBZONE_C`, `SUBZONE_N`, `PLN_AREA_N` and `REGION_N`
properties. A `townName` or `TOWN` property is optional when
`planning_area_to_hdb_town.json` is populated.

## `planning_area_to_hdb_town.json`

Maps URA planning areas to HDB town names, for example:

```json
{
  "TAMPINES": "TAMPINES",
  "BEDOK": "BEDOK",
  "KALLANG": "KALLANG/WHAMPOA"
}
```

Planning areas without an HDB town should be omitted or mapped to `null`. The
shipped file is empty on purpose; complete it from HDB's town definitions.

## `hdb_resale.csv`

Use the HDB **Resale flat prices based on registration date from Jan-2017
onwards** dataset: `d_8b84c4ee58e3cfc0ece0d773c8ca6abc`.

Required columns:

```text
month,town,flat_type,resale_price,floor_area_sqm
```

Optional:

```text
subzone_code
```

Without `subzone_code`, pricing is always a town-level proxy
(`isTownProxy=true`). With it, the control can use a subzone-level median when at
least 5 transactions exist.

## `amenities.json`

A list of amenity points:

```json
[
  {
    "name": "Tampines Primary School",
    "category": "Primary School",
    "latitude": 1.351,
    "longitude": 103.941
  }
]
```

Supported categories include `Primary School`, `Secondary School`,
`Polyclinic`, `Hospital`, `Park`, `Shopping Mall` and `MRT`. These can be built
from data.gov.sg school data plus OneMap Themes for healthcare, malls and MRT
exits.

## `environment_baselines.json`

Static values used for scoring, keyed by subzone code:

```json
{
  "TAMPINES01": {
    "greenCoveragePercent": 35.5,
    "weatherPattern": "Partly Cloudy",
    "pm25Baseline": 12.0,
    "granularity": "REGION",
    "asOf": "2025-12-01T00:00:00+08:00"
  }
}
```

Live PM2.5, UVI and forecast values are fetched separately by
`LiveEnvironmentProvider` and are display-only; they do not affect scores.

## `commute_matrix.json`

Precomputed CBD commute estimates:

```json
{
  "subzones": {
    "TAMPINES01": {
      "CBD": {
        "durationMinutes": 35,
        "distanceKm": 14.2,
        "transferCount": 1
      }
    }
  }
}
```

The production matrix should cover all subzones used by the app. Custom
workplaces use live OneMap routing for a top-50 shortlist.

## Attribution

Display dataset names, source agencies and `asOf` dates in the UI and PDF report.
Singapore open data is generally available under the Singapore Open Data
Licence; check each source page before redistribution.
