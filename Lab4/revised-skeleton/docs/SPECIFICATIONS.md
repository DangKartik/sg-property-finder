# Frozen Specification — v1

This file records the rules that implementation must follow. Values marked **OPEN**
require a product decision and are also listed in `OPEN_ISSUES.md`.

## 1. Criterion catalogue

| ID | Name | Unit | Direction | Radius / basis | Default weight |
| --- | --- | --- | --- | --- | --- |
| `PRICE` | Housing affordability | SGD (median) | MINIMIZE | Selected flat types, 12-month window | 0.20 |
| `COMMUTE_TIME` | Commute duration | minutes | MINIMIZE | Workplace / CBD, fixed departure | 0.20 |
| `SCHOOL_PROXIMITY` | School access | count | MAXIMIZE | 1.0 km (see OPEN-01) | 0.20 |
| `GREEN_COVERAGE` | Green coverage | percent | MAXIMIZE | 500 m buffer | 0.20 |
| `AMENITIES_DENSITY` | Amenity access | count | MAXIMIZE | Malls 1 km, polyclinics/hospitals 2 km, MRT/LRT 800 m | 0.20 |

The default weights above are an assumption for the first version; the user can
override every weight. `CriterionWeight.criterionId` must match this catalogue.

## 2. Normalisation and scoring

After the hard budget filter, for each criterion and candidate subzone:

```text
Maximisation:  S = (X - Xmin) / (Xmax - Xmin)
Minimisation:  S = (Xmax - X) / (Xmax - Xmin)
```

- `S` is in `[0, 1]`.
- If `Xmax == Xmin`, all candidates receive `S = 1.0` for that criterion (no
  differentiation is possible).
- Available weights are renormalised:

```text
W'i = Wi / sum(Wj for available criteria j)
```

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
  `VALID_ZERO`, `STALE_CACHE` and `PARTIAL_DATA`.
- If a stale cache is used, keep the cached value and attach a warning; do not
  silently present it as fresh.

### Ranking and tie-breaks

Sort descending by `totalScore`, then ascending by:

1. commute duration (minutes);
2. median price per square metre;
3. `subzoneCode` (deterministic final tie-break).

## 3. Budget semantics

- `budgetMax` is a hard filter.
- A subzone is eligible when at least one selected flat type has a median price
  at or below `budgetMax`.
- Pricing uses a 12-month rolling window of HDB resale transactions.
- A minimum of 5 transactions is required for a direct price estimate.
- If fewer than 5 transactions exist, use the broader HDB town median and set
  `HousePricing.isTownProxy = true`.
- If no price data exists for any selected flat type, the subzone is excluded
  and a `MISSING_SOURCE_DATA` warning is returned.

**Data caveat:** the published HDB resale dataset is keyed by HDB town, not URA
subzone. A subzone-level median requires a block-to-subzone mapping built from
block geocoding; without that mapping, `isTownProxy` is always true. See
`OPEN_ISSUES.md` OPEN-02.

## 4. Static vs live environment data

### Score-impact data (static baselines)

- Green coverage from park polygons, using a fixed 500 m buffer.
- Long-term PM2.5 baseline by NEA region.
- Fixed regional weather baseline (definition OPEN — see OPEN-04).

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
  - Primary/secondary schools: 1.0 km (OPEN-01 conflicts with 1.5 km);
  - Polyclinics/public hospitals: 2.0 km;
  - Parks/green spaces: 500 m;
  - Shopping malls: 1.0 km;
  - MRT/LRT stations: 800 m.
- **CBD anchor:** Raffles Place MRT centroid, `1.2830, 103.8513` (WGS84).
- Distances to polygon features use the nearest point on the polygon boundary;
  distances to point features use the point coordinate.

## 6. Commute strategy and latency

- **Default departure:** next weekday at 08:30 SGT.
- **Precomputed matrix:** all ~332 subzone representative points to four business
  districts (Raffles Place, Jurong East, One-North, Changi Business Park).
- **Cache TTL:** 7 days. The cache key must include workplace/geohash, mode,
  departure date and departure window; a 7-day TTL alone is insufficient because
  OneMap PT results depend on the date/time.
- **Custom workplace:** live OneMap routing only for a top-50 shortlist selected
  by straight-line distance from the workplace.
- **Failure:** fall back to the last cached route and attach a `STALE_CACHE`
  warning; if no cache exists, return the ranking without the commute criterion
  and renormalise weights.

**SLA risk:** the first ranking for a new workplace may still exceed 5 seconds if
50 OneMap calls are made. Pre-warm popular workplaces or reduce the shortlist;
see `OPEN_ISSUES.md` OPEN-09.

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
| `GET` | `/api/v1/ready` | — | data/cache readiness |
| `GET` | `/api/v1/criteria` | — | `CriterionDefinition[]` |
| `POST` | `/api/v1/address/search` | `{ "query": "..." }` | `AddressMatch[]` |
| `POST` | `/api/v1/recommendations` | `ProfileDTO` | `RecommendationSet` |
| `GET` | `/api/v1/subzones/{code}/factsheet` | profile context (OPEN-10) | `NeighborhoodDetailDTO` |
| `POST` | `/api/v1/comparisons` | `ProfileDTO`, `subzoneCodes[]` | `ComparisonResult` |
| `POST` | `/api/v1/reports/pdf` | `RecommendationSet`, `NeighborhoodDetailDTO[]` | `PdfReport` |
| `GET` | `/api/v1/reports/{reportId}/download` | — | PDF bytes |

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

- Download URLs expire after 15 minutes.
- The server file path is never returned to the browser.
- The report includes the profile weights, per-criterion `CriterionScore` rows,
  data `asOf` dates, commute assumptions (mode and departure time), and caveats
  for town-proxy prices and regional environment data.
