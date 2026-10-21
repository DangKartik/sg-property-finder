# Lab4 Skeleton — Gap Analysis

**Scope:** `Lab4/Skeleton Code` compared against the class diagram, functional/non-functional requirements and tech stack in the project brief.

**Verdict:** The skeleton is a set of valid Python stubs, but it is **not yet a usable starting point for this application**. It was generated from the older Lab3 class diagram (`FILE_RESPONSIBILITIES.md` says so explicitly), so most class signatures no longer match the current diagram. It also has no FastAPI layer, no React/TypeScript layer, no data-ingestion layer, and several required datasets are absent from the chosen source list.

---

## 1. Blockers (fix before writing feature code)

### B1. The skeleton is based on the previous class diagram

The current diagram and the code disagree on roughly two-thirds of the classes. Examples:

| Current diagram | Skeleton |
| --- | --- |
| `RankingControl` ranks subzones | `RankingControl` is a copy of `MapControl`; no ranking methods exist |
| `ProfileControl.createProfile()` returns `String` | Returns `bool` |
| `ScoringStrategy.computeSuitabilityScore(..., commute)` | `calculateScore(subzone, profile)` — no commute parameter |
| `Subzone.subzoneCode`, `boundaryPolygon`, `suitabilityScore` | `subzoneId`, `boundariesGeoJson`, embedded amenities/pricing/environment |
| `HousePricing.averagePrice`, `medianPricePerSqm`, `priceTrend` | `medianPrice`, `propertyType`, `pricePerSqFt` |
| `EnvironmentInfo.weatherPattern`, `greenCoveragePercent` | `airQualityIndex`, `greenSpacePercentage`, `averageNoiseLevelDb` |
| `PdfReport.filePath` | `contentBytes` |

A full class-by-class table is in section 5.

**Action:** decide whether the current diagram or the skeleton is authoritative. For grading, the current diagram almost certainly is. Regenerate or rewrite the skeleton before implementing anything.

### B2. The core ranking use case does not exist

`control/ranking_control.py` contains exactly the same attributes and methods as `control/map_control.py`:

```python
subzoneRegistry: SubzoneRegistry
commuteControl: CommuteControl
mapAdapter: OneMapApiAdapter

getSubzonePolygons() -> MapData
getCommuteOverlay(start, dest) -> RouteData
```

The current diagram requires:

```python
profileCatalog: ProfileCatalog
subzoneRegistry: SubzoneRegistry
scoringStrategy: ScoringStrategy
commuteControl: CommuteControl

selectProfile(profileId)
calculateScore(profileId, subzoneCode) -> float
generateRankedRecommendations(profileId) -> RecommendationSet
```

Nothing in the skeleton can currently produce a ranked recommendation. This is the central feature of the app.

### B3. There is no web application layer

The skeleton is a Java-style OOP package tree. For the stated stack there should be:

- a FastAPI app factory / entry point (`app/main.py`);
- routers for profiles, recommendations, subzones, comparison and reports;
- Pydantic request/response schemas;
- CORS and static-file configuration;
- dependency wiring and a `lifespan` startup hook;
- environment/config handling for OneMap credentials.

None of these exist. `SystemStartupControl.main(args)` and `launchUI()` are desktop-application concepts; they do not map to a React + FastAPI deployment.

### B4. The boundary layer is in the wrong language

All seven `boundary/` classes are Python stubs with `renderForm()`, `renderMap()` and similar methods. In this stack, those classes must be **React/TypeScript components**. Keeping them in Python produces dead code and an unimplementable `DataAvailabilityNotifier -> NotificationModalUI` dependency.

**Action:** move the boundary layer to `frontend/src/components/` (keeping the diagram names for traceability) and replace the Python boundary classes with REST endpoints. If the module requires the Python files to exist for the class diagram, keep them only as documented placeholders and make it explicit that they are not the runtime UI.

### B5. Missing datasets for core criteria

The five chosen datasets do **not** cover subzone boundaries, housing prices, schools, hospitals or shopping malls. The app cannot satisfy the stated functional requirements with them alone. See section 3 for the full matrix.

At minimum, add:

- **URA Master Plan 2019 Subzone Boundary (No Sea)** — the base geography (332 subzones).
- **HDB Resale Flat Prices (Jan 2017 onwards)** — budget, `selectedFlatTypes`, price trend, median price per sqm.
- **LTA MRT Station Exit (GEOJSON)** — public-transport accessibility.
- **MOE General Information of Schools** — school proximity (geocode the postal codes).
- **OneMap Themes / a curated POI list** — hospitals and shopping malls.

### B6. No derived neighbourhood indicators

The skeleton stores raw amenities, raw pricing and raw environment data on `Subzone`, but the scoring strategy has nothing numeric to score. There is no representation of:

- nearest park / school / hospital / mall / MRT distance;
- count of amenities within 800 m / 1 km / 2 km;
- park-connector or cycling-path length within a radius;
- green coverage percentage;
- median resale price and price trend by flat type;
- PM2.5 / UVI / forecast values by region;
- commute minutes, distance and transfers.

Without these, a 0–100 score cannot be calculated accurately, and the PDF cannot explain **why** a neighbourhood ranked where it did.

### B7. Missing DTOs and score breakdown

`entity/types.py` declares empty placeholder classes with no fields:

```python
class Coordinates: ...
class ProfileForm: ...
class ValidationResult: ...
class RawResponse: ...
class MapData: ...
class RouteData: ...
class FactSheetData: ...
class TransitMode: ...
```

`ProfileDTO` and `NeighborhoodDetailDTO` from the diagram are not declared at all. `RecommendationItem` has no `subzoneId` and no `criterionScoreBreakdown`, so the report cannot show the per-criterion contribution that explains a ranking.

### B8. Broken and duplicated environment class

`control/environment_retrieval_control.py` imports a package that does not exist:

```python
from sgpropfinder.control.retrieval_control import RetrievalControl
from sgpropfinder.entity.environment_info import EnvironmentInfo
```

Importing that module raises `ModuleNotFoundError`. It also duplicates `EnvironmentalRetrievalControl` in `control/environmental_retrieval_control.py`, with a different API. One of the two must be deleted and the remaining class must match the diagram's `EnvironmentRetrievalControl`.

---

## 2. Requirements traceability

### Functional requirements

| # | Requirement | Skeleton support | Gap |
| --- | --- | --- | --- |
| FR1 | Key in budget, commute, transport, schools, hospitals, green space, malls | Partial | `ProfileForm` is empty; `PreferenceProfile` only has id/name/weights; no flat types, workplace, anchor, timestamps. |
| FR2 | Assign weight/importance to each criterion | Partial | `CriterionWeight` exists but has no setter; no criterion catalogue; no slider/normalisation rules; no validation. |
| FR3 | See ranked neighbourhoods | **Missing** | `RankingControl` has no ranking logic. |
| FR4 | See details of a neighbourhood | Partial | `NeighborhoodDetailsControl` exists but `FactSheetData` is empty; no commute control; no UI. |
| FR5 | Modify preferences and regenerate | Partial | `updateProfile` stub only; no delete, versioning, invalidation or regenerate endpoint. |
| FR6 | Estimate distance/travel time to work/CBD | Partial | `CommuteControl` stub; no geocoding of workplace; no CBD anchor; no date/time; no mode handling. |
| FR7 | Calculate 0–100 suitability score | **Missing** | No normalisation, weighting, direction handling, missing-data policy or breakdown. |
| FR8 | Inform users when data is unavailable | Partial | `DataAvailabilityNotifier` stub is not wired; no response-level warnings or per-criterion availability. |
| FR9 | Notify users of invalid inputs | Partial | `validateProfileForm` stub; `ValidationResult` has no fields; no rules. |
| FR10 | Access data.gov.sg and OneMap | **Wrong** | Adapter responsibilities are swapped; no token management, polling download, retries or cache. |
| FR11 | Generate a PDF explaining the result | Partial | No template, no details input, no score breakdown, no download endpoint. |
| FR12 | Compare different neighbourhoods | **Missing** | No comparison class, endpoint or UI in either the diagram or the skeleton. |

### Non-functional requirements

| Area | Status | Gap |
| --- | --- | --- |
| Usability | Missing | No frontend; no loading/empty/error states; no design system. |
| Performance | At risk | No timers, timeouts or cache; OneMap calls for all 332 subzones cannot meet 5 s. |
| Accuracy | At risk | HDB prices are town-level, environment is regional; no aggregation definitions, provenance or accuracy tests. |
| Reliability | Missing | No retries, fallback snapshot, health/readiness checks or circuit breaker. |
| Data freshness | Missing | No ingestion job, dataset versioning, `lastUpdated` metadata or refresh policy. |
| Privacy | At risk | No policy; workplace address would be sent to and potentially logged by the backend. |
| Scalability | At risk | Per-process `cachetools` cache; 332-item responses; no pagination/concurrency limit. |
| Maintainability | Partial | Package split and Strategy pattern are good; no config, DI, tests, linting or CI. |
| Accessibility | Missing | No frontend; Leaflet map needs a keyboard-accessible alternative and non-colour cues. |

---

## 3. Data source audit

### 3.1 Coverage matrix

| Criterion | Dataset | In current list? | Granularity | Update cadence | Issue |
| --- | --- | --- | --- | --- | --- |
| Base geography | URA MP2019 Subzone Boundary (No Sea) | **No** | 332 polygons | Ad hoc (latest Dec 2025) | Required; without it there is no `Subzone` entity. |
| Housing price | HDB Resale Flat Prices (Jan 2017+) | **No** | Town × flat type × month | Daily | Required for budget, flat types and price trend. Prices are **town-level**, not subzone-level. |
| Parks / access | Parks@SG | Yes | Points | Last updated Jun 2024 | Point data, stale. Cannot compute green coverage from points. |
| Green coverage | NParks Parks and Nature Reserves | **No** | Polygons | Monthly | Use this for coverage. Label as managed parks only, not total greenery. |
| Park connectors | Park Connector Loop | Yes | Lines | Ad hoc (Jul 2026) | Need length within a radius. |
| Tracks | NParks Tracks | Yes | Lines | Quarterly (Dec 2025) | 24 MB; optional. Precompute, do not load per request. |
| Cycling | Cycling Path Network | Yes | Lines | Every 6 months (Jul 2026) | Need length within a radius. |
| Air quality (historical) | PM2.5 annual mean | Yes | 5 regions | Annual | Not live and not subzone-level. Better as a long-term baseline. |
| Air quality (live) | PM2.5 real-time API | **No** | 5 regions | Hourly | Use for display or a rolling average; map subzone → region. |
| UV | UVI API | Yes | **National only** | Every 30 min | Does not vary by neighbourhood; cannot differentiate subzones. |
| Weather | 24-hour forecast API | Yes | 5 regions | Every 6 h | Does not vary by subzone; the 2-hour forecast has ~47 areas if finer granularity is needed. |
| Schools | MOE General Information of Schools | **No** | Address/postal code | 6-monthly | No lat/lon in the published columns; geocode once via OneMap. |
| Hospitals | MOH health facilities | **No** | Aggregate counts | Stale (2022) | No coordinates; use OneMap Themes or a curated hospital list. |
| Malls | None | **No** | POI | — | Not covered by data.gov.sg's five datasets; use OneMap Themes or a curated list. |
| Public transport | OneMap + LTA MRT exits | Partly | Stations / routes | 6-monthly / live | Add the MRT exit dataset and/or OneMap Nearby Transport. |
| Commute | OneMap Routing | Yes | Route | Live | Token-based auth, departure time required for PT, quota limits. |

### 3.2 Granularity is the biggest accuracy risk

- **HDB resale prices are by town, not subzone.** All subzones in the same town will share the same price metric unless you build a subzone-to-town mapping and clearly label the value as a town-level proxy. This directly affects the accuracy NFR.
- **PM2.5 and 24-hour weather are by five regions; UVI is national.** A "neighbourhood liveability score" cannot honestly claim neighbourhood-level air quality, UV or weather from these sources. Either:
  - score them at region level and show "regional data" in the UI;
  - use the historical PM2.5 dataset to compute a stable regional baseline; or
  - mark the criterion unavailable at subzone level and exclude it from scoring.
- **Parks@SG is point data.** Green coverage requires polygons (NParks Parks and Nature Reserves) and a defined buffer/denominator.
- **Schools and hospitals require geocoding or a POI source.** MOH's published health-facility datasets are counts, not locations.

### 3.3 Freshness

"Updated within 24 hours when new data becomes available" is achievable, but the source cadences are very different:

- HDB resale: daily;
- PM2.5: hourly;
- UVI: every 30 minutes;
- 24-hour forecast: every 6 hours;
- parks polygons: monthly;
- cycling paths: every 6 months;
- park connectors: ad hoc;
- subzone boundaries: rarely.

Interpret the NFR as **"check for source updates at least daily and reload when the source `lastUpdatedAt` changes"**, not "every dataset changes daily". The skeleton has no metadata, scheduler or versioning to support this.

### 3.4 Missing derived indicators

Add a `SubzoneIndicators` value object (or columns on a precomputed dataset) with at least:

```text
nearestParkM, parkCount800m, greenCoveragePct500m
nearestSchoolM, primarySchoolCount1km, schoolCount2km
nearestHospitalM, acuteHospitalCount2km
nearestMallM, mallCount1km
nearestMrtM, mrtStationCount800m
parkConnectorLength1km, cyclingPathLength1km
medianResalePrice, medianPricePerSqm, transactionCount12m, priceTrend12m
pm25Baseline, pm25Live, uvi, forecastCode
commuteMinutes, commuteKm, transferCount
```

These are what the scoring strategy should consume. Computing them on every request with GeoPandas will not meet the 5-second NFR; precompute them during ingestion and ship a compact JSON/Parquet artefact.

---

## 4. Architecture and design issues

### 4.1 Persistence contradicts the stack

`container/profile_catalog.py` says it "persists them in the browser's IndexedDB" and exposes:

```python
saveToIndexedDB()
loadFromIndexedDB()
```

A Python backend cannot write to the browser's IndexedDB. With no PostgreSQL, you must choose:

- **Recommended:** profiles live in the browser via Dexie; the backend is stateless and receives the full profile in each ranking request. The Python `ProfileCatalog` then either disappears or becomes an in-request collection.
- **Alternative:** a server-side in-memory catalogue. This loses data on restart, is unsafe for concurrent users and stores personal addresses on the server, which conflicts with the privacy requirement.

Whichever you choose, remove the impossible `saveToIndexedDB`/`loadFromIndexedDB` methods from the Python class.

### 4.2 Shared mutable state

The current diagram puts `suitabilityScore` on the shared `Subzone` entity and has `RankingControl.selectProfile(profileId)` store "the selected profile". With multiple users, these are race conditions: one user's ranking overwrites another's score, and the "selected profile" is global.

**Fix:** keep the score in `RecommendationItem` (per profile/request), and pass `profileId` or the full profile in the request. Do not store per-user selection on a singleton or shared entity.

### 4.3 Scoring needs a specification before implementation

The diagram names `WeightedScoringStrategy` but does not define:

- the criterion list and direction (lower price/commute is better; more amenities is better);
- how each raw indicator is normalised to 0–100 (min–max across candidates vs fixed thresholds);
- whether weights are 0–10 or percentages and whether they are normalised to sum to 1;
- what happens when a criterion is missing (exclude and reweight, treat as zero, or block the ranking);
- how to treat valid zeros (no mall within 1 km) vs missing data (API failed);
- tie-breaking and rounding;
- whether the score is comparable across different candidate sets.

Without these rules, the "accuracy" and "consistent results" NFRs cannot be tested. Write them down and unit-test them with fixed fixtures.

### 4.4 Live data should not drive a neighbourhood ranking

The proposed liveability score gives 15% to weather and 15% to outdoor comfort. If those use the live UVI and 24-hour forecast:

- UVI is 0 at night, so every neighbourhood gets the same perfect score after sunset;
- the 24-hour forecast changes every 6 hours, so the same profile produces different rankings during the day;
- PM2.5 spikes are transient and regional.

**Fix:** separate **static neighbourhood profile** (green coverage, long-term PM2.5 baseline, park/connector access) from **live conditions** (current PM2.5, UVI, forecast). Rank on the static profile; show live conditions as informational cards with timestamps. This also makes results reproducible.

### 4.5 OneMap performance and consistency

OneMap routing requires a token obtained with email/password (`POST /api/auth/post/getToken`), valid for 3 days. Public-transport routing also requires `date`, `time` and `mode`; `numItineraries` is capped at 3; the API returns 429 when the quota is exceeded.

Ranking all 332 subzones by calling OneMap for each one:

- cannot meet the 5-second ranking target;
- will hit rate limits and produce 429s;
- produces different results at different departure times, violating consistency.

**Recommended design:**

1. Geocode the workplace once and cache it.
2. Compute non-commute indicators for all subzones (cheap, local).
3. Shortlist the top N (e.g., 30–50) by the non-commute score, or use a distance/transit proxy for the first pass.
4. Call OneMap only for the shortlist, in parallel with a bounded concurrency, and cache by `(workplace geohash, mode, departure window)`.
5. Fix a departure window (e.g., next weekday 08:30 SGT) and include it in the response so results are reproducible.
6. If OneMap fails or quota is exhausted, return the non-commute ranking with a clear warning and a "commute unavailable" flag.

Also note that `OneMapApiAdapter.getBasemapTile()` should not exist: React-Leaflet consumes a tile URL template directly. Server-side tile proxying adds load and licensing concerns.

### 4.6 Caching and freshness

`cachetools.TTLCache` is in-process and per-worker. That is acceptable for a single-worker school deployment, but:

- it is lost on restart;
- multiple uvicorn workers will have divergent caches;
- there is no version key, so stale data can be served after a dataset update.

Add a cache key that includes the dataset snapshot/version and `asOf` timestamp, and a startup/refresh job that checks `lastUpdatedAt` before reloading. Serve the last good snapshot if the source is down, and label it as stale.

### 4.7 PDF report

The skeleton has no template and no report data flow. `ReportControl.generatePdfReport(recommendationSet)` does not accept the `details` list required by the current diagram, and `PdfReport` stores bytes rather than a file path.

Practical issues:

- WeasyPrint is synchronous and CPU-heavy; run it in a threadpool and enforce a timeout.
- On Windows, WeasyPrint needs GTK/Pango native libraries. Plan for Docker/WSL or document the setup.
- Storing files on local disk breaks with multiple workers and creates cleanup/privacy issues. Prefer generating bytes and returning a `StreamingResponse` with a short-lived download token, or write to a temp file and delete after download.
- The report must include weights, per-criterion scores, source `asOf` dates, commute assumptions (mode, departure time), and caveats (town-level prices, regional environment) to satisfy "why".

### 4.8 Privacy

Workplace addresses and coordinates are personal data. The current design would send them to the backend for ranking and PDF generation. At minimum:

- do not log request bodies or addresses;
- do not persist profiles server-side (use Dexie);
- keep PDFs short-lived and unguessable;
- allow the user to delete a profile and its cached commute data;
- tell the user what is stored locally vs sent to OneMap/data.gov.sg.

### 4.9 Reliability and observability

The NFR asks for 99% availability. The app depends on two external APIs, so it must degrade gracefully:

- timeouts and retries with backoff on all outbound calls;
- circuit breaker for OneMap and data.gov.sg;
- `/health` and `/ready` endpoints (ready only after datasets load);
- structured logs with request IDs and timings;
- fallback to the last cached dataset snapshot;
- explicit warnings in the UI when data is stale or unavailable.

None of this exists in the skeleton.

---

## 5. Class-by-class conformance

Legend: **OK** = matches the current diagram; **Partial** = same idea but missing members/signature mismatch; **Wrong/Missing** = does not implement the current diagram.

### Boundary

| Diagram class | Skeleton | Status | Key gaps |
| --- | --- | --- | --- |
| `ProfileFormUI` | `boundary/profile_form_ui.py` | Partial | Diagram wants `currentProfileData`, `criteriaSliders`, `submitProfileData()`, `displayValidationError()`; skeleton has `profileControl`, `onSubmit()`. Must be a React component. |
| `ProfileSelectorUI` | `boundary/profile_selector_ui.py` | Partial | Missing `profileDropdownList`; `renderSelector`/`onSelectProfile` vs `renderDropdown`/`onProfileSelected`. |
| `ResultsListUI` | `boundary/results_list_ui.py` | Partial | Missing `displayedRecommendations`; must become React. |
| `NeighborhoodMapUI` | `boundary/neighborhood_map_ui.py` | Partial | Missing `choroplethLayers`, `mapCenterCoordinates`, `highlightSubzone()`; `renderCommuteLayer(list)` vs `renderCommuteOverlay(CommuteEstimate)`. |
| `FactSheetUI` | `boundary/fact_sheet_ui.py` | Partial | Missing `activeSubzoneId`; `displaySubzoneDetails(id)` vs `displayDetails(amenities, env, pricing, commute)`. |
| `ExportReportUI` | `boundary/export_report_ui.py` | Partial | Missing `reportFormat`, `triggerPdfExport()`, `displayDownloadLink()`; `openExportModal`/`onConfirmExport` instead. |
| `NotificationModalUI` | `boundary/notification_modal_ui.py` | Partial | Has `currentMessage`; diagram wants `modalTitle`/`modalMessage` and `showModal`/`closeModal`. |

### Control

| Diagram class | Skeleton | Status | Key gaps |
| --- | --- | --- | --- |
| `SystemStartupControl` | `control/system_startup_control.py` | Partial | Missing `launchUI()`; singleton constructor conflicts with `getInstance()`; `main(args)` is not a web entry point. |
| `ProfileControl` | `control/profile_control.py` | Partial | Missing `validator`, `deleteProfile()`; `createProfile` returns `bool` instead of `String`; no `ProfileDTO`. |
| `InputValidationControl` | `control/input_validation_control.py` | Partial | `validateProfileForm(dict)` vs `validateProfileData(ProfileDTO)`; `ValidationResult` has no fields or rules. |
| `RankingControl` | `control/ranking_control.py` | **Wrong** | Entirely a copy of `MapControl`; no `selectProfile`, `calculateScore`, `generateRankedRecommendations`, `profileCatalog` or `scoringStrategy`. |
| `MapControl` | `control/map_control.py` | Partial | `getSubzonePolygons()` vs `generateMapData(): List<Subzone>`; missing `fetchSubzoneBoundary()`; `oneMapAdapter` named `mapAdapter`. |
| `CommuteControl` | `control/commute_control.py` | Partial | `calculateTravelTime()` vs `retrieveCommute()`; `apiAdapter` vs `oneMapAdapter`; no geocoding/date-time. |
| `NeighborhoodDetailsControl` | `control/neighborhood_details_control.py` | Partial | Missing `commuteControl`, `profileId` parameter, `NeighborhoodDetailDTO`; `getFullFactSheet` vs `fetchNeighborhoodDetails`. |
| `RetrievalControl` | `control/retrieval_control.py` | Partial | Missing `notifier`, `handleMissingData()`; `fetchData` is not abstract (diagram says abstract); `parseResponse` is extra. |
| `AmenityRetrievalControl` | `control/amenity_retrieval_control.py` | Partial | `fetchAmenitiesForSubzone` vs `retrieveAmenityInfo`; no missing-data handling. |
| `EnvironmentRetrievalControl` | two files: `environment_retrieval_control.py`, `environmental_retrieval_control.py` | **Wrong** | Broken `sgpropfinder` import in one; duplicate class with conflicting API; wrong return types (`list[AmenityInfo]`). |
| `HousePricingRetrievalControl` | `control/house_pricing_retrieval_control.py` | Partial | `fetchPricingForSubzone` returns `list[AmenityInfo]`; should return `HousePricing` and be named `retrieveHousePricing`. |
| `ReportControl` | `control/report_control.py` | Partial | Missing `notifier`, `details` parameter; constructor requires a `PdfReport`; no template/download flow. |
| `DataAvailabilityNotifier` | `control/data_availability_notifier.py` | Partial | Missing `notificationUI`; `notifyMissingData(source, entityId)` vs `notifyDataUnavailable(datasetName)`. |

### Container

| Diagram class | Skeleton | Status | Key gaps |
| --- | --- | --- | --- |
| `ProfileCatalog` | `container/profile_catalog.py` | Partial | Missing `removeProfile()` (returns `Boolean`); `deleteProfile` returns `None`; `saveToIndexedDB`/`loadFromIndexedDB` are impossible in Python. |
| `SubzoneRegistry` | `container/subzone_registry.py` | Partial | Missing `registerSubzone()`; `loadSubzones` is an extra. |

### Adapter and strategy

| Diagram class | Skeleton | Status | Key gaps |
| --- | --- | --- | --- |
| `OneMapApiAdapter` | `adapter/one_map_api_adapter.py` | **Wrong** | Missing `apiKey`, `getRoutingData()`, `getBasemapTile()`; has `fetchDataset()` (a data.gov.sg responsibility); no token handling. |
| `DataGovSgAdapter` | `adapter/data_gov_sg_adapter.py` | **Wrong** | Missing `fetchDataset()`; has `fetchRoute()` and `fetchSubzonePolygons()` (OneMap/URA responsibilities); no poll-download support. |
| `ScoringStrategy` | `strategy/scoring_strategy.py` | Partial | `calculateScore(subzone, profile)` vs `computeSuitabilityScore(subzone, profile, commute)`. |
| `WeightedScoringStrategy` | `strategy/weighted_scoring_strategy.py` | Partial | Same signature mismatch; `weightsMap` is stored on the strategy instead of being read from the profile; no algorithm. |

### Entity

| Diagram class | Skeleton | Status | Key gaps |
| --- | --- | --- | --- |
| `PreferenceProfile` | `entity/preference_profile.py` | Partial | Missing `budgetMin`, `budgetMax`, `selectedFlatTypes`, `workplaceAddress`, `anchorCoordinates`, `creationTime`, `lastUpdatedTime`, `isActive`; missing `getProfileId`, `updateDetails`, `addCriterionWeight`, `getCriteriaWeights`. |
| `CriterionWeight` | `entity/criterion_weight.py` | Partial | Missing `setWeightValue()`. |
| `Subzone` | `entity/subzone.py` | **Wrong** | Missing `subzoneCode`, `subzoneName`, `boundaryPolygon`, `suitabilityScore`, accessors; uses `boundariesGeoJson: str` and embeds amenities/pricing/environment. |
| `RecommendationSet` | `entity/recommendation_set.py` | Partial | Missing `profileId`, `getItems()`, `sortByRank()`; uses `setId`/`generatedTimestamp`/`getSortedItems`. |
| `RecommendationItem` | `entity/recommendation_item.py` | **Wrong** | Missing `subzoneId`, `criterionScoreBreakdown`; stores a `Subzone` object instead. |
| `CommuteEstimate` | `entity/commute_estimate.py` | Partial | Missing `transferCount`, `getDistanceKm()`; `transitMode` vs `travelMode`; no departure time/route geometry. |
| `AmenityInfo` | `entity/amenity_info.py` | Partial | `name` vs `amenityName`; extra `amenityId`; no distance/link to subzone. |
| `HousePricing` | `entity/house_pricing.py` | **Wrong** | Fields do not match: `medianPrice`/`propertyType`/`pricePerSqFt` vs `averagePrice`/`medianPricePerSqm`/`priceTrend`; no flat-type breakdown or transaction count. |
| `EnvironmentInfo` | `entity/environment_info.py` | **Wrong** | `airQualityIndex`/`greenSpacePercentage`/`averageNoiseLevelDb` vs `weatherPattern`/`greenCoveragePercent`; no PM2.5/UVI/forecast; no dataset provenance. |
| `PdfReport` | `entity/pdf_report.py` | **Wrong** | `contentBytes`/`createdAt` vs `filePath`/`generatedTime`; missing `getReportId()`/`getFilePath()`. |

### Shared types

| Type | Status | Gap |
| --- | --- | --- |
| `Coordinates` | Empty | Needs `latitude`, `longitude`, validation and serialisation. Lat/lng order differs between OneMap (`lat,lng`) and GeoJSON (`lng,lat`). |
| `ProfileDTO` | Missing | Add all profile fields. |
| `NeighborhoodDetailDTO` | Missing | Add amenities, environment, pricing, commute and availability metadata. |
| `ValidationResult` | Empty | Needs `is_valid`, `field_errors`, `message`. |
| `RawResponse` | Empty | Needs status, body, headers, source and `fetched_at`. |
| `MapData` | Empty | Needs subzone GeoJSON, scores, legend and centre. |
| `RouteData` | Empty | Needs encoded geometry, distance, duration and mode. |
| `FactSheetData` | Empty | Needs all fact-sheet sections and warnings. |
| `TransitMode` | Empty | Make it an `Enum` with `PT`, `DRIVE`, `WALK`, `CYCLE`. |

---

## 6. Concrete code defects

1. `environment_retrieval_control.py` imports `sgpropfinder.*` and fails at import time.
2. `EnvironmentRetrievalControl` and `EnvironmentalRetrievalControl` duplicate each other.
3. `RankingControl` and `MapControl` are identical.
4. `DataGovSgAdapter` and `OneMapApiAdapter` have each other's responsibilities.
5. `ReportControl.__init__` requires a `PdfReport`, so the control cannot be constructed at startup.
6. `SystemStartupControl.getInstance()` cannot supply the constructor arguments required by `__init__`.
7. `NotificationModalUI.__init__` requires a message string before the modal exists.
8. Attributes are annotated as public class attributes while comments claim `# private`; no encapsulation or validation.
9. `RetrievalControl.fetchData` is not `@abstractmethod` despite being described as abstract.
10. `AmenityRetrievalControl`/`EnvironmentRetrievalControl`/`HousePricingRetrievalControl` copy-paste `-> list[AmenityInfo]` as the return type of `parseResponse`.
11. `ProfileCatalog` depends on browser IndexedDB from Python.
12. No `requirements.txt`, `pyproject.toml`, `.env.example`, `Dockerfile` or CI config.
13. No tests, fixtures or sample GeoJSON.
14. No API contract or Pydantic schemas.
15. `README.md` is the repository README, not a skeleton guide. `FILE_RESPONSIBILITIES.md` is already out of date relative to both the code and the current diagram.

---

## 7. Decisions needed before implementation

| # | Decision | Options / recommendation |
| --- | --- | --- |
| 1 | Unit of recommendation | 332 subzones (diagram) vs 55 planning areas / 26 HDB towns. **Recommend subzones for the map, but use town-level prices and regional environment, clearly labelled.** |
| 2 | Budget semantics | Hard filter vs affordability score. **Recommend hard filter on `budgetMax` plus a price score, using the selected flat types and a 12-month window.** |
| 3 | Weight scale | 0–10 sliders vs 0–100 percentages. **Recommend 0–10 in the UI, normalised to sum 1 server-side; reject all-zero.** |
| 4 | Missing data policy | Exclude + reweight vs treat as zero vs block. **Recommend exclude + reweight + warning; never silently treat missing as zero.** |
| 5 | Normalisation | Min–max across candidates vs fixed thresholds. **Recommend fixed domain thresholds so scores are comparable across runs.** |
| 6 | Environment scoring | Live vs long-term baseline. **Recommend long-term baseline for ranking; live values for display only.** |
| 7 | Commute mode/time | PT only vs multiple modes; departure time. **Recommend PT default, next weekday 08:30 SGT, user-selectable drive/cycle later.** |
| 8 | Persistence | Dexie only vs server-side. **Recommend Dexie only; backend stateless.** |
| 9 | PDF delivery | Stream vs file on disk. **Recommend streamed bytes or short-lived temp file.** |
| 10 | Comparison | Side-by-side table vs map overlay. **Recommend a comparison tray in the results list plus map highlight; add a `Comparison` endpoint/DTO.** |
| 11 | Extra datasets | Add HDB, subzone, MRT, schools, POIs. **Required to meet the FRs.** |
| 12 | Geocoding | OneMap Search vs manual coordinates. **Recommend OneMap Search with cached results; show the resolved address for confirmation.** |

---

## 8. Recommended implementation order

1. **Align the class model** with the current diagram; delete the duplicate environment class; fix adapter responsibilities.
2. **Scaffold FastAPI** (app factory, config, CORS, static assets, health/readiness, dependency injection).
3. **Define Pydantic DTOs and the criterion catalogue**; implement validation rules and tests.
4. **Build the ingestion pipeline**: download and cache subzone boundaries, HDB prices, parks, connectors, cycling paths, MRT exits, schools, hospitals and malls; precompute `SubzoneIndicators`; store a dataset snapshot version and `asOf` timestamps.
5. **Implement the scoring strategy and ranking control** with fixed fixtures and unit tests for weights, normalisation, missing data, budgets and ties.
6. **Implement the OneMap adapter**: token cache, geocoding, routing, timeout/retry/429 handling, commute cache, shortlist strategy.
7. **Implement detail, comparison and report endpoints**; stream the PDF with WeasyPrint.
8. **Build the React/TS UI**: profile form with sliders, results list, Leaflet choropleth, fact sheet, comparison, notifications, Dexie persistence, accessibility.
9. **Harden the NFRs**: timing metrics, fallback snapshots, stale-data warnings, load test, privacy review.

---

## Appendix — verified source details

| Item | Value |
| --- | --- |
| HDB resale prices | `d_8b84c4ee58e3cfc0ece0d773c8ca6abc`; town × flat type × month; daily; CSV ~22.6 MB. |
| URA subzone boundary | `d_8594ae9ff96d0c708bc2af633048edfb`; 332 subzones; GeoJSON ~3 MB; ad hoc updates. |
| URA planning area boundary | `d_4765db0e87b9c86336792efe8a1f7a66`; 55 areas; useful for town/region joins. |
| Parks@SG | `d_99b71f5d34cf57a3a592fbfdef1f42b6`; point data; last updated Jun 2024. |
| NParks Parks and Nature Reserves | `d_77d7ec97be83d44f61b85454f844382f`; polygons; monthly. |
| Park Connector Loop | `d_a69ef89737379f231d2ae93fd1c5707f`; lines; ad hoc. |
| NParks Tracks | `d_306cc1018cb733346681883ee6d73054`; lines; quarterly; ~24 MB. |
| Cycling Path Network | `d_8f468b25193f64be8a16fa7d8f60f553`; lines; every 6 months; ~4.7 MB. |
| PM2.5 live API | `https://api-open.data.gov.sg/v2/real-time/api/pm25`; hourly; 5 regions. |
| UVI live API | `https://api-open.data.gov.sg/v2/real-time/api/uv`; national. |
| 24-hour forecast API | `https://api-open.data.gov.sg/v2/real-time/api/twenty-four-hr-forecast`; 5 regions; every 6 h. |
| 2-hour forecast API | `https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast`; ~47 areas. |
| MOE schools | `d_688b934f82c1059ed0a6993d2a829089`; address/postal; geocode required. |
| MRT station exits | `d_b39d3a0871985372d7e1637193335da5`; points; every 6 months. |
| Static download flow | `GET https://api-open.data.gov.sg/v1/public/api/datasets/{datasetId}/poll-download`, then download the returned URL. |
| OneMap auth | `POST https://www.onemap.gov.sg/api/auth/post/getToken` with email/password; token valid 3 days. |
| OneMap routing | `GET https://www.onemap.gov.sg/api/public/routingsvc/route`; `Authorization` header; PT requires `date`, `time`, `mode`; `numItineraries` 1–3. |
| OneMap themes | `GET https://www.onemap.gov.sg/api/public/themesvc/retrieveTheme?queryName=...`; token required. |
| OneMap search | `GET https://www.onemap.gov.sg/api/common/elastic/search`; token required. |

Dataset IDs and URLs should live in one configuration module (not scattered through code), and every API response should include its source and `asOf` date.
