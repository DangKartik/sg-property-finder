# Frozen Specification — v1

This file records the frozen rules that implementation follows. Resolved
decisions and accepted limitations are summarized in `docs/OPEN_ISSUES.md` and
`PROJECT_STATUS.md`.

## 1. Criterion catalogue

| ID | Name | Unit | Direction | Fixed domain | Radius / basis | Default importance |
| --- | --- | --- | --- | --- | --- | --- |
| `PRICE` | Housing affordability | SGD (median) | MINIMIZE | 200,000–1,500,000 | Selected flat types, 12-month window | 5 |
| `COMMUTE_TIME` | Commute duration | minutes | MINIMIZE | 0–90 | Workplace / CBD, fixed departure | 5 |
| `SCHOOL_PROXIMITY` | School access | count | MAXIMIZE | 0–4 | 1.0 km | 5 |
| `GREEN_COVERAGE` | Green coverage | percent | MAXIMIZE | 0–100 | 500 m buffer | 5 |
| `AMENITIES_DENSITY` | Amenity access | count | MAXIMIZE | 0–10 | Malls 1 km, polyclinics/hospitals 2 km, MRT/LRT 800 m | 5 |

The default importance above is an assumption for the first version. The user
rates every criterion from **1 (not important) to 10 (very important)**;
ratings do not need to sum to 100. `CriterionWeight.criterionId` must match this
catalogue.

## 2. Normalisation and scoring

After the hard budget and amenity-minimum filters, each raw value is normalised
against its **fixed absolute domain** (not the candidate set), so scores remain
comparable when the budget filter removes candidates:

```text
Maximisation:  S = (clamp(X, min, max) - min) / (max - min)
Minimisation:  S = (max - clamp(X, min, max)) / (max - min)
```

- `S` is in `[0, 1]`.
- Values outside the fixed domain are clamped.
- If `max == min`, the criterion is misconfigured; the implementation returns
  `S = 0.0` for safety.
- User importance ratings `Ri` are in `[1, 10]`. Relative weights are computed
  inside the scoring strategy:

```text
Wi = Ri / sum(Rj for all active criteria j)
W'i = Wi / sum(Wj for available criteria j)
```

The first normalisation makes the active weights sum to `1.0`; the second
handles missing criteria by renormalising only over available criteria.

- `CriterionScore.normalisedScore` is `S` in `[0, 1]`.
- `CriterionScore.weight` is `W'i` in `[0, 1]`.
- `CriterionScore.weightedScore = S * W'i`.
- `RecommendationItem.totalScore = 100 * sum(weightedScore)` and is rounded to
  one decimal place.
- If no criterion has usable data, return an error; do not return a ranking.

### Missing-data rules

- A missing source value is not a zero. Mark `CriterionScore.isMissing = true`
  and exclude that criterion from the weighted sum.
- A valid zero (for example, zero malls within 1 km) is a real observation and
  is scored as zero; it must not trigger weight renormalisation.
- `DataAvailabilityWarning.code` distinguishes `MISSING_SOURCE_DATA`,
  `VALID_ZERO`, `STALE_CACHE`, `PARTIAL_DATA` and
  `ESTIMATED_COMMUTE_FALLBACK`.
- If a stale cache is used, keep the cached value and attach a warning; do not
  silently present it as fresh.

### Ranking and tie-breaks

Sort descending by `totalScore`, then ascending by:

1. commute duration (minutes);
2. median price per square metre;
3. `subzoneCode` (deterministic final tie-break).

`RecommendationSet.items` is capped at the **top 20** after sorting; results
outside the top 20 are discarded and their warnings are omitted. The comparison
endpoint uses the full internal ranking so subzones outside the top 20 can still
be compared.

## 3. Budget semantics

- `budgetMax` is a hard filter.
- A subzone is eligible when at least one selected flat type has a median price
  at or below `budgetMax`.
- Pricing uses a 12-month rolling window of HDB resale transactions.
- Pricing always uses the **HDB town median**; `HousePricing.isTownProxy` is
  always `true`.
- If no price data exists for any selected flat type, the subzone is excluded
  and a `MISSING_SOURCE_DATA` warning is returned.

**Frozen data decision (22 October 2026):** the published HDB resale dataset is
keyed by HDB town, not URA subzone. The application deliberately keeps the
town-level median proxy and does not build a block-to-subzone mapping. The
UI/PDF labels this as a **Town-Level Median Proxy**.

## 3a. Hard amenity minimums

The profile can specify five whole-number minimums. They are hard filters and
are applied before scoring, after the budget filter:

| Profile field | Indicator | Radius |
| --- | --- | --- |
| `minimumPrimarySchools` | `primarySchoolCount1km` | 1.0 km |
| `minimumSecondarySchools` | `secondarySchoolCount1km` | 1.0 km |
| `minimumTertiarySchools` | `tertiarySchoolCount1km` (JCs + universities) | 1.0 km |
| `minimumMalls` | `mallCount1km` | 1.0 km |
| `minimumHospitals` | `hospitalCount2km` | 2.0 km |

- `0` means no requirement.
- A subzone is discarded immediately when any count is below its minimum.
- If amenity data is unavailable, the minimums are not applied and the normal
  missing-data warning path is used.
- Tertiary schools come from the MOE JC directory plus the
  `tertiary_schools.json` supplement (JCs, Millennia Institute, mixed-level
  schools with JC/IB levels, and autonomous universities).

## 4. Static vs live environment data

### Score-impact data (static baselines)

- Green coverage baseline by planning region (500 m buffer metadata).
- Long-term PM2.5 baseline by planning region.
- Fixed regional weather pattern baseline.

These values must be stored in the data snapshot and must not change between two
identical ranking requests using the same snapshot.

### Display-only data (live)

- Current 1-hour PM2.5.
- Current UVI.
- 24-hour weather forecast.

Live values are shown in `FactSheetUI` with an `asOf` timestamp and must not
affect suitability scores. This preserves deterministic rankings.

## 5. Geography and distance definitions

- **Subzone anchor:** Shapely `representative_point()` of the URA subzone polygon
  (guaranteed to lie inside the polygon).
- **Buffer radii:**
  - Primary/secondary/tertiary schools: 1.0 km;
  - Polyclinics/public hospitals: 2.0 km;
  - Parks/green spaces: 500 m;
  - Shopping malls: 1.0 km;
  - MRT/LRT stations: 800 m.
- **CBD anchor:** Raffles Place MRT centroid, `1.2830, 103.8513` (WGS84).
- **Amenity count method:** buffer-distance density. Every amenity point within
  the fixed radius of the subzone representative point is counted. Park polygons
  are converted to a single `representative_point()` when the amenities snapshot
  is generated, so counts use that point coordinate.

## 6. Commute strategy and latency

- **Default departure:** next weekday at 08:30 SGT.
- **Precomputed matrix:** public-transport travel times for 319/332 subzone
  representative points to Raffles Place. The matrix is never used for driving
  or walking.
- **Cache TTL:** 7 days. The cache key must include workplace/geohash, mode,
  departure date and departure window; a 7-day TTL alone is insufficient because
  OneMap PT results depend on the date/time.
- **Custom workplace, public transport:** live OneMap routing for a top-50
  shortlist selected by straight-line distance. Subzones outside the shortlist
  receive a straight-line PT estimate (with `ESTIMATED_COMMUTE_FALLBACK`) so
  every candidate has a commute value and the criterion is weighted consistently.
- **Driving/walking (all origins):** hybrid shortlist. The nearest 50 subzones
  use live OneMap routing; the remainder use spatial heuristic estimates with a
  **1.35× road factor** for driving and a **1.20× path factor** for walking.
  The PT matrix is never used.
- **Failure / missing matrix entry:** use a straight-line distance estimate,
  keep the subzone eligible for ranking, and attach a
  `DataAvailabilityWarning` with code `ESTIMATED_COMMUTE_FALLBACK`. Heuristic
  shortlist outliers carry the same warning.

**SLA risk:** the live shortlist is capped at 50 OneMap calls; the remaining
candidates are estimated in memory. The first cold-cache ranking should still be
benchmarked against the 5-second target.

## 7. Data snapshot and ingestion contract

`DatasetMetadata`:

```text
dataSnapshotId  e.g. SNAPSHOT_2026_Q4
dataAsOf        ISO-8601 timestamp
sourceUrl       original dataset/API URL
recordCount     number of records in the snapshot
```

- Static fallback assets live in `backend/assets/data/`.
- A manifest records the `DatasetMetadata` for every asset.
- If a live call fails (timeout, 429, 5xx), load the last good snapshot and
  attach `DataAvailabilityWarning(isStale=true, code=STALE_CACHE)`.
- `RecommendationSet.dataSnapshotId` and `dataAsOf` must identify the exact
  snapshot used for that ranking.

## 8. API contract

All endpoints return the standard envelope:

```json
{
  "success": true,
  "data": {},
  "warnings": [],
  "error": null
}
```

`ApiEnvelope<T>` and `ApiError` are defined in
`backend/app/schemas/api_envelope.py` and `frontend/src/types/dto.ts`.

### Endpoints

| Method | Path | Request | Response |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | — | service status |
| `GET` | `/health` | — | alias for container/probe health checks |
| `GET` | `/api/v1/ready` | — | data/cache readiness |
| `GET` | `/api/v1/criteria` | - | `CriterionDefinition[]` |
| `GET` | `/api/v1/amenities` | - | amenity points for the map |
| `GET` | `/api/v1/data/status` | - | dataset freshness metadata |
| `POST` | `/api/v1/data/refresh` | - | force live data.gov.sg refresh and local amenity rebuild |
| `POST` | `/api/v1/address/search` | `{ "query": "..." }` | `AddressMatch[]` |
| `POST` | `/api/v1/profiles/validate` | `ProfileDTO` | `ValidationResult` |
| `POST` | `/api/v1/share/decode` | `{ "share": "..." }` | `{ profile, subzoneCodes }` |
| `POST` | `/api/v1/commute/overlay` | origin, destination, mode | `RouteData` |
| `POST` | `/api/v1/recommendations` | `ProfileDTO` | `RecommendationSet` |
| `GET` | `/api/v1/subzones/{code}/factsheet` | profile context | `NeighborhoodDetailDTO` |
| `POST` | `/api/v1/comparison` | `ProfileDTO`, `subzoneCodes[]` | `ComparisonResult` |
| `POST` | `/api/v1/reports/pdf` | `ProfileDTO`, `subzoneCodes[]` | `PdfReport` |
| `GET` | `/api/v1/reports/download/{reportId}` | - | PDF bytes |

HTTP status mapping:

- `200` success;
- `400` validation/input error;
- `404` subzone/report not found;
- `422` schema validation;
- `429` upstream OneMap/data.gov.sg quota;
- `500` unexpected failure;
- `503` required data snapshot unavailable.

Error responses use `success=false`, `data=null`, `error={code,message,details}`.

## 9. PDF report contract

`PdfReport` contains only browser-safe metadata:

```text
reportId, generatedTime, downloadUrl, expiresAt,
fileName, contentType, sizeBytes
```

- Rendering uses **ReportLab Platypus** only; WeasyPrint is not used.
- Download URLs expire after 15 minutes.
- The server file path is never returned to the browser.
- The report includes the profile weights, per-criterion `CriterionScore` rows,
  data `asOf` dates, commute assumptions (mode and departure time), and caveats
  for town-proxy prices and regional environment data.
