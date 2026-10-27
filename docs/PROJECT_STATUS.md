# SG Property Finder — Project Status

- **Last updated:** 26 October 2026
- **Repository:** `2006-SCMB-D2`
- **Application folder:** `SGPropertyFinder/`
- **Current branch:** `main`
- **Last commit:** `fe0a40a` (centralised documentation)
- **Working tree:** insufficient-data selection guard, verification updates and documentation changes pending commit

This document is intended as the handover/context file for a new conversation or a new developer joining the project.

---

## 1. What this web app is

**SG Property Finder** is a neighbourhood recommender for people planning to move to a new neighbourhood in Singapore. A user creates a preference plan containing:

- a housing budget,
- selected HDB flat types,
- a workplace/CBD anchor,
- a preferred commute mode,
- 1–10 importance ratings for affordability, commute, schools, greenery and amenities.

The backend ranks URA subzones with a deterministic 0–100 suitability score. The frontend lets the user inspect the ranked list, explore a choropleth map, open neighbourhood factsheets, compare two to four subzones, and export a PDF report with a shareable scenario URL.

### Target users

People choosing where to live in Singapore who want a data-driven comparison of:

- HDB resale affordability,
- commute time/distance to work or the CBD,
- school, healthcare, mall, park and MRT access,
- green coverage and environmental conditions.

### Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18 + TypeScript + Vite |
| Client storage | Dexie.js / IndexedDB |
| Mapping | Leaflet + React-Leaflet, OneMap basemap tiles |
| Backend | Python 3.14, FastAPI, Uvicorn |
| Spatial processing | Shapely (plus a pure-Python geometry fallback) |
| HTTP clients | `httpx` for async routing; standard-library `urllib` for some adapters |
| Caching | `cachetools`-compatible TTL cache |
| PDF | ReportLab (WeasyPrint removed) |
| Database | **No PostgreSQL.** Profiles live in browser IndexedDB; backend is stateless |

### External data

- **data.gov.sg**
  - URA Master Plan 2019 Subzone Boundary (No Sea): `d_8594ae9ff96d0c708bc2af633048edfb`
  - HDB Resale Flat Prices, Jan 2017 onwards: `d_8b84c4ee58e3cfc0ece0d773c8ca6abc`
  - Live PM2.5, UVI and weather forecast APIs
- **OneMap**
  - address search/geocoding,
  - public-transport/driving/walking routing,
  - basemap tiles.

---

## 2. Quick start

### Prerequisites

- Python 3.11+ (local verification used Python 3.14)
- Node.js 20+ and npm (local verification used Node 24)
- GNU Make (installed via winget package `ezwinports.make`, version 4.4.1)
- A `.env` file with OneMap credentials

### One command

```powershell
cd C:\Users\Lucas\Documents\GitHub\2006-SCMB-D2\SGPropertyFinder
make install
make dev
```

`make dev`:

- starts FastAPI on `http://127.0.0.1:8000`,
- starts Vite on `http://127.0.0.1:5173`,
- waits for both,
- opens the browser,
- stops both on Ctrl+C.

### Other Make targets

```powershell
make backend    # FastAPI only
make frontend   # Vite only
make test       # backend unittest suite (162 tests)
make test-frontend # frontend Vitest suite (39 tests)
make benchmark  # Phase 5 SLA benchmark
make build      # frontend type-check + production build
make clean      # remove dist and Python caches
make help
```

### Manual run

```powershell
# Terminal 1
cd SGPropertyFinder/backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# Terminal 2
cd SGPropertyFinder/frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` to `http://127.0.0.1:8000`.

### Health/freshness checks

```text
GET http://127.0.0.1:8000/api/v1/health
GET http://127.0.0.1:8000/api/v1/ready
GET http://127.0.0.1:8000/api/v1/data/status
```

### Important test-run note

Run backend tests with:

```powershell
cd SGPropertyFinder
make test
```

or directly from `backend/`:

```powershell
cd SGPropertyFinder/backend
python -m unittest discover -s tests -v
```

Do **not** run `python -m unittest discover -s backend/tests` from the SGPropertyFinder root: the tests import `tests.support` and expect `backend/` on `sys.path`.

---

## 3. Current status at a glance

| Area | Status |
| --- | --- |
| Phase 1 — ECB skeleton, entities, documentation | **Completed** |
| Phase 2.1 — spatial engine, data assets, town mapping | **Completed** |
| Phase 2.2 — adapters, retrieval, caching | **Completed** |
| Phase 2.3 — commute strategy | **Completed** (matrix + hybrid shortlist + estimated fallback) |
| Phase 2.4 — MCDA scoring/ranking | **Completed** |
| Phase 2.5 - factsheets, PDF, share URLs | **Completed** (ReportLab) |
| Phase 2.6 — FastAPI endpoints | **Completed** |
| Phase 3 — frontend | **Completed** |
| Phase 4 — formal black-box/white-box testing | **Completed** — EP/BVA, state-transition, CFG/basis-path and data-flow documentation |
| Phase 5 - formal SLA benchmarking/E2E documentation | **Completed** - benchmark and 18-check E2E checklist |
| Makefile / one-command local run | **Completed** |
| Real amenities dataset | **Completed** — 1,200 effective points (1,172 base + 28 tertiary); `make amenities` rebuilds it |
| Amenity dataset pipeline | **Completed** (`scripts/build_amenities.py` + `tertiary_schools.json`) |
| Amenity map layers | **Completed** (markers shown only for selected subzone) |
| API-response caching in IndexedDB | **Completed** (`ApiCache`, ETag/TTL/stale fallback) |
| Data refresh UI + amenity rebuild | **Completed** |
| Hybrid commute shortlist | **Completed** (50 live + spatial heuristics) |
| 1–10 criterion importance | **Completed** (relative-normalised) |
| Hard amenity minimums | **Completed** (primary/secondary/tertiary schools, malls, hospitals) |
| Frontend tests | **Completed** (39 Vitest tests) |
| PDF generation | **Completed** (ReportLab only) |
| Production deployment/CI | **Not completed** |

---

## 4. Completed work

### 4.1 Phase 1 — Skeleton refactoring and specifications

- Reorganized classes into backend/frontend ECB-style packages:
  - backend: `control/`, `entity/`, `container/`, `adapter/`, `strategy/`, `schemas/`, `core/`, `services/`, `api/`;
  - frontend: `boundary/`, `control/`, `container/`, `types/`, `utils/`, `api/`.
- Created `entity/enums.py` with transit mode, environment granularity, warning severity and data-availability codes.
- Added `Subzone.townName`; removed the mutable `suitabilityScore` from `Subzone`.
- Added `CriterionScore`, `AddressMatch`, `DatasetMetadata`, `DataAvailabilityWarning`, `ComparisonResult`, `SubzoneIndicators`.
- Refactored `PdfReport` to browser-safe metadata (`downloadUrl`, `expiresAt`, `fileName`, `contentType`, `sizeBytes`).
- Added docstrings/JSDoc across the skeleton.
- Made `DataAvailabilityNotifier` stateless and removed `ReportControl.lastGeneratedReport`.
- Added `.env.example`, `.gitignore`, `Settings`, and environment documentation.
- Specifications live in:
  - `SPECIFICATIONS.md`
  - `OPEN_ISSUES.md`
  - `ENVIRONMENT.md`

### 4.2 Phase 2 — Backend

#### Spatial engine and data assets

- `SubzoneRegistry` loads the official URA 332-subzone GeoJSON.
- Shapely-backed polygon operations with a pure-Python fallback:
  - point-in-polygon,
  - centroid,
  - representative point,
  - bounds.
- `planning_area_to_hdb_town.json` populated.
- Buffer/count logic for schools (1.0 km), hospitals/polyclinics (2 km), parks (500 m), malls (1 km), MRT (800 m).
- Town-level HDB pricing proxy accepted and labelled `isTownProxy`.
- `amenities.json` generated by `scripts/build_amenities.py` (`make amenities`):
  - 1,200 effective points after merging the tertiary supplement: 182 primary
    schools, 144 secondary schools, **28 tertiary schools (JCs/universities)**,
    462 parks, 188 MRT stations, 22 polyclinics, 31 hospitals and 143 shopping malls.
  - The 28 tertiary points live in
    `backend/assets/data/tertiary_schools.json` and are merged at load time so an
    existing `amenities.json` does not need to be regenerated.
  - Counts use buffer-distance density from the subzone representative point:
    schools/tertiary schools/malls 1.0 km, MRT 800 m, parks 500 m,
    healthcare 2.0 km.
  - If the file is absent or unreadable, school/amenity criteria are excluded
    and weights renormalised.

#### External adapters

- `OneMapApiAdapter`:
  - token caching/refresh,
  - address search returning `AddressMatch` with `SequenceMatcher` confidence,
  - public transport/driving/walking routing,
  - async `httpx` routing with shared client,
  - theme data.
- `DataGovSgAdapter`:
  - metadata, poll-download, static dataset download,
  - real-time API fetch,
  - TTL caching,
  - JSON/GeoJSON/CSV/Parquet local fallback.
- `DatasetService`:
  - local snapshots for fast startup,
  - automatic data.gov.sg refresh when snapshots are older than `DATA_MAX_AGE_HOURS` (default 24),
  - writes refreshed snapshots back to `backend/assets/data/`,
  - `/api/v1/data/status` and `POST /api/v1/data/refresh`,
  - refresh also triggers the local amenity rebuild from the cached POI snapshot.
- Live refresh has been manually verified:
  - 332 subzones,
  - 243,176 HDB transactions,
  - ~5.2 seconds.

#### Retrieval engine

- `RetrievalControl` template-method base.
- `HousePricingRetrievalControl`:
  - 12-month rolling HDB window,
  - flat-type keyed `dict[str, HousePricing]`,
  - **always uses the HDB-town median proxy** (`isTownProxy=true`),
  - no subzone-level pricing or block-to-subzone mapping,
  - median price, median $/sqm and price trend,
  - indexed by town/flat type for startup performance.
- `EnvironmentRetrievalControl`:
  - regional `environment_baselines.json` + `DEFAULT` fallback,
  - static baseline values for scoring,
  - live PM2.5/UVI/forecast isolated as display-only.
- `AmenityRetrievalControl`:
  - school/healthcare/park/mall/MRT counts and nearest distances,
  - graceful missing-data warning when the dataset is absent,
  - local `rebuildFromLocalSources()` that recomputes subzone aggregates and
    updates registry indicators without network calls,
  - `status()` metadata exposed through `/api/v1/data/status`.

#### Commute

- Precomputed CBD commute matrix keyed by actual URA subzone code.
- Matrix is used **only for `PUBLIC_TRANSIT`**.
- Driving/walking and custom-workplace public transport use the hybrid shortlist
  strategy: the 50 nearest subzones receive live OneMap routing; the remainder
  receive spatial heuristic estimates with a 1.35× road factor for driving, a
  1.20× path factor for walking and a 1.00× factor for public transport.
- 319/332 subzones covered; the 13 no-route entries are marked
  `dataAvailable=false`, excluded from ranking/comparison, and blocked from
  factsheet selection on the map with an “insufficient data” bottom notification.
- Next-weekday 08:30 SGT departure.
- Async parallel routing for the live shortlist; failures and heuristic outliers
  carry `ESTIMATED_COMMUTE_FALLBACK` warnings.
- TTL cache for live commute results.

#### Scoring and ranking

- Hard budget filter using the lowest selected-flat-type median price.
- Hard amenity minimums (primary/secondary/tertiary schools, malls, hospitals)
  are applied before scoring; a subzone below any minimum is discarded.
- **Fixed absolute normalisation** (per product decision):
  - price: 200k–1.5M,
  - commute: 0–90 minutes,
  - schools: 0–4,
  - green coverage: 0–100%,
  - amenities: 0–10.
- User importance ratings are 1–10 and are relative-normalised to weights that
  sum to 1.0 before scoring.
- Missing data: exclude criterion, reweight available criteria to 1.0, attach warning.
- `RecommendationItem` contains 0–100 total score and `CriterionScore` rows.
- Tie-break: shortest commute, then median $/sqm, then subzone code.
- `RecommendationSet` preserves `dataSnapshotId`, `dataAsOf`, warnings and `profileSnapshot`.
- Ranking output is capped at the **top 20** items; the remaining scored
  subzones are discarded and their warnings are omitted.
- `ComparisonControl` caps comparisons at four subzones.

#### Factsheets, reports and endpoints

- `NeighborhoodDetailsControl` aggregates:
  - multi-flat pricing,
  - amenities,
  - environment,
  - commute,
  - warnings,
  - pricing town-proxy note.
- `ReportControl`:
  - ReportLab Platypus rendering only,
  - profile importance ratings and relative weights,
  - per-subzone criterion score tables,
  - data dates and explicit data-quality caveats,
  - short-lived temp report store,
  - secure download metadata,
  - shareable scenario URL.
- FastAPI routes:
  - `POST /api/v1/address/search`
  - `POST /api/v1/profiles/validate`
  - `POST /api/v1/share/decode`
  - `POST /api/v1/recommendations`
  - `POST /api/v1/commute/overlay`
  - `GET /api/v1/subzones/geometry`
  - `GET /api/v1/subzones/{code}/factsheet`
  - `POST /api/v1/comparison`
  - `POST /api/v1/reports/pdf`
  - `GET /api/v1/reports/download/{report_id}`
  - `GET /api/v1/criteria`
  - `GET /api/v1/amenities`
  - `GET /api/v1/health`
  - `GET /health` (alias for probes)
  - `GET /api/v1/ready`
  - `GET /api/v1/data/status`
  - `POST /api/v1/data/refresh`
- Unified `ApiEnvelope` (`success`, `data`, `warnings`, `error`).

### 4.3 Phase 3 — Frontend

- DTOs match backend:
  - `ProfileDTO`, `CriterionScoreDTO`, `AddressMatchDTO`, `NeighborhoodDetailDTO`,
    `DataAvailabilityWarningDTO`, `ReportResponseDTO`, `DatasetStatusDTO`,
    `AmenityPointDTO`, `ShareScenarioDTO`.
- Dexie/IndexedDB `ProfileCatalog`:
  - `saveToLocalStorage()`
  - `loadFromLocalStorage()`
  - `deleteProfile()`
- Dexie/IndexedDB `ApiCache`:
  - caches criteria, geometry, amenities, factsheets, recommendations,
    comparisons and route overlays,
  - stores ETag, storedAt and expiresAt,
  - revalidates cached GETs with `If-None-Match`,
  - serves a cached envelope with a `STALE_CACHE` warning when the backend is
    unreachable,
  - prunes entries older than 7 days.
- `ProfileControl` performs authoritative backend validation before saving to Dexie.
- Form:
  - budget sliders,
  - flat-type checkboxes,
  - address search with selectable `AddressMatch` results,
  - commute mode,
  - hard minimum inputs for primary, secondary and tertiary schools, malls and
    hospitals; subzones below any minimum are discarded before scoring,
  - 1–10 importance sliders per criterion; ratings are normalised by the backend.
- Top-right plan dropdown showing the current plan; every row has its own Edit and Delete actions, plus delete confirmation and a one-plan guard.
- Plan creation/editing opens in a centered modal with internal scrolling.
- Right sidebar is reserved for recommendations; the map occupies the main left column.
- Map:
  - OneMap tiles,
  - subzone choropleth,
  - card-to-polygon and polygon-to-card synchronization,
  - transit/driving route overlay,
  - amenity markers appear only after a subzone is selected, showing nearby
    primary/secondary/tertiary schools, healthcare, parks, MRT/LRT and malls
    within 2 km with category colours, counts and tooltips.
- Results:
  - top-20 ranked cards,
  - comparison checkboxes,
  - factsheet button,
  - warning count,
  - Export Recommendations to PDF button inside the recommendations panel.
- Share import:
  - reads `?share=`, decodes via `/api/v1/share/decode`,
  - saves the profile to Dexie, activates it and reruns ranking,
  - highlights shared subzone polygons and fills comparison selection.
- Map refresh button:
  - the “Refresh” button at the bottom-left of the map calls `POST /api/v1/data/refresh`,
  - refreshes subzone/HDB snapshots and rebuilds amenities from the cached
    local POI layer,
  - clears the IndexedDB API cache on success,
  - reloads amenity points, updates the header freshness display and reruns the
    active ranking.
- Factsheet modal:
  - multi-flat pricing,
  - town-level proxy badge and note,
  - green coverage/weather/PM2.5/UVI,
  - school/hospital/mall/MRT/park counts,
  - nearby amenities grouped by category (primary/secondary/tertiary schools,
    polyclinics, hospitals, parks, malls, MRT) with counts and distance,
  - commute details,
  - missing-data badges.
- Comparison matrix for 2–4 subzones.
- PDF export:
  - generate report,
  - binary download,
  - share URL.
- Notification modal for validation/API errors.
- Responsive layout and accessible labels.

### 4.4 Testing and verification

- **162 backend tests pass** via `make test`.
- **39 frontend Vitest tests pass** via `npm test`.
- Frontend tests cover format/polyline helpers, weight migration, nearby amenity
  filtering/colours, `ApiCache` persistence/pruning, client cache reuse/stale
  fallback, refresh cache invalidation, hard-minimum form submission, top-20
  result rendering, unavailable-subzone extraction and the profile lifecycle
  state machine.
- Frontend `npm run build` passes (`tsc --noEmit` + Vite production build).
- Live FastAPI server verified:
  - health true,
  - ready true,
  - 332 subzones.
- Browser walkthrough verified:
  - create plan,
  - OneMap address search,
  - select address,
  - save/rank,
  - results,
  - choropleth,
  - factsheet,
  - comparison,
  - PDF modal,
  - plan persistence after reload,
  - 1–10 importance ratings normalised to weights summing to 1.0,
  - share-link import and shared-subzone highlighting,
  - amenity markers hidden until a subzone is selected, then nearby points only,
  - IndexedDB cache reuse on reload (only `/data/status` refetched).
- `/api/v1/data/refresh` handler test:
  - 1,200 effective amenity items,
  - 332 subzone aggregates,
  - amenity status returned as `local-amenity-snapshot`.
- OneMap live checks:
  - token endpoint,
  - address search (10 results),
  - walking route.
- data.gov.sg live checks:
  - metadata,
  - poll-download,
  - PM2.5 real-time,
  - full DatasetService refresh.

### 4.5 Makefile

`SGPropertyFinder/Makefile`:

- `install`
- `dev`
- `backend`
- `frontend`
- `test`
- `test-frontend`
- `benchmark`
- `amenities`
- `build`
- `clean`
- `help`

Supporting scripts:

- `scripts/dev.py`
- `scripts/test_backend.py`
- `scripts/benchmark_api.py`
- `scripts/build_amenities.py`
- `scripts/clean.py`

### 4.6 P0 correctness fixes

- **Commute matrix mode gating:** `CommuteControl` only consults
  `commute_matrix.json` for `PUBLIC_TRANSIT` near the CBD. `DRIVING`, `WALKING`
  and custom-workplace public transport use the hybrid shortlist: 50 nearest
  subzones live, remainder spatial heuristic with 1.35× driving / 1.20× walking
  / 1.00× PT multipliers.
- **Insufficient-data exclusion:** the 13 subzones without a matrix entry are
  marked `dataAvailable=false` from `commute_matrix.json.metadata.errors`, removed
  from the ranking cohort, blocked from comparison/factsheet endpoints, and shown
  on the map with a bottom notification instead of opening a factsheet.
- **No silent candidate dropping:** `RankingControl` scores every otherwise
  available candidate; candidates with live or heuristic commute estimates still
  receive the commute criterion, so values are weighted consistently for ranked
  subzones.
- **Share URL import:** new `POST /api/v1/share/decode` endpoint. On startup,
  `App.tsx` reads `?share=`, decodes the scenario, saves the profile to Dexie,
  activates it, reruns ranking, selects the first shared subzone, fills the
  comparison selection and highlights all shared subzone polygons.

### 4.7 Frontend cache, map layers and tests

- **IndexedDB API cache:** `ApiCache` stores criteria, geometry, amenities,
  factsheets, recommendations, comparisons and route overlays. GETs revalidate
  with `If-None-Match`; TTLs are 1 h for geometry/amenities, 24 h for criteria,
  10 min for factsheets, 5 min for rankings/comparisons and 30 min for route
  overlays. Expired entries are
  used with a `STALE_CACHE` warning if the backend is unreachable.
- **Amenity map layers:** `GET /api/v1/amenities` returns all 1,200 effective points.
  `NeighborhoodMapUI` hides them until a subzone is selected, then shows only
  amenities within 2 km of that subzone with category colours, counts and
  tooltips.
- **Insufficient-data map guard:** the 13 unavailable subzones are rendered
  muted/dashed. Clicking one does not select it or open the factsheet bar;
  `App.tsx` shows a bottom toast explaining that insufficient data is available.
  If an unavailable card is ever present in stale data, its factsheet button is
  replaced with an “Insufficient data” label and its Compare checkbox is disabled.
- **Mall coverage:** the amenity builder adds LTA Carpark Rates major-mall names
  and a named supplement, taking the snapshot from 66 to 143 malls.
- **Comparison outside top 20:** `RankingControl.generateRankedRecommendations`
  accepts an optional `limit`; the comparison endpoint passes `limit=None` so
  subzones outside the displayed top 20 still receive score items.
- **Frontend tests:** Vitest/jsdom/Testing Library with 39 tests covering format
  helpers, polyline decoding, weight migration, nearby amenity filtering/colours,
  `ApiCache`, client cache reuse/stale fallback, hard-minimum form submission,
  refresh cache invalidation, top-20 `ResultsListUI` rendering, unavailable-subzone
  extraction and the `ProfileControl` CRUD state machine.
- **Data refresh UI:** the map’s bottom-left “Refresh” button calls
  `POST /api/v1/data/refresh`, refreshes subzone/HDB data, rebuilds amenities
  from the local POI snapshot, clears `ApiCache`, reloads amenity points,
  updates the header status and reruns the active ranking.
- **PDF generation:** ReportLab Platypus only; WeasyPrint, its requirement and
  native Pango/GObject dependencies were removed. The report includes profile
  importance weights, per-subzone criterion scores, data dates and caveats.

---

## 5. Remaining gaps, accepted limitations and resolved items

### 5.1 Recently resolved

1. **Amenities dataset — resolved 21 October 2026.**
   - `backend/assets/data/amenities.json` is generated by `make amenities`.
   - Factsheets now show real school, park, MRT, polyclinic, hospital and mall counts.
   - The missing-data path is also fixed: absent amenity data excludes the
     school/amenity criteria and renormalises weights instead of scoring zero.
   - Mall coverage is now 143 points, including LTA major-mall names and a
     named supplement; newer malls not present in those sources may still be
     absent.

2. **API-response caching in IndexedDB — resolved 22 October 2026.**
   - `ApiCache` persists criteria, geometry, amenities, factsheets,
     recommendations, comparisons and route overlays.
   - It revalidates GETs with `If-None-Match`, applies TTLs and serves a
     `STALE_CACHE` warning when the backend is unreachable.
   - Profiles remain in the separate `ProfileCatalog` Dexie database.

3. **WeasyPrint — removed 22 October 2026.**
   - `ReportControl` now renders exclusively with ReportLab Platypus.
   - WeasyPrint and its native Pango/GObject dependencies were removed from
     `requirements.txt`.

### 5.2 Data limitations

4. **HDB pricing is town-level — accepted decision (22 October 2026).**
   - The real HDB dataset has no subzone code.
   - Every price is labelled `isTownProxy=true` and displayed as “Town-Level Median Proxy”.
   - No block-to-subzone mapping will be built; town-level pricing is the frozen product choice.

5. **Environment baselines are deterministic user-provided values.**
   - `environment_baselines.json` contains regional green/PM2.5 values.
   - These are **not** a verified 10-year NParks time series; they are the frozen values supplied for the project.
   - Live PM2.5/UVI/weather are display-only and do not affect scores.

6. **Commute matrix coverage is 319/332.**
   - 13 subzones returned OneMap HTTP 404/no route (mostly islands/out-of-bounds).
   - They are recorded in `commute_matrix.json.metadata.errors`, marked
     `dataAvailable=false`, and excluded from ranking, comparison and factsheet
     selection. The map shows them in a muted style and a bottom notification
     explains that insufficient data is available.
   - Driving/walking and custom-workplace public transport use the hybrid
     shortlist (50 live + spatial estimates); CBD public transport retains the
     matrix path for available subzones.

7. **`BUKIT TIMAH` and `OUT OF BOUNDS` mappings.**
   - These follow the supplied mapping but may not correspond to HDB town pricing data; such subzones can produce missing-price warnings.

### 5.3 Formal testing documentation

8. **Phase 4 black-box testing documentation — revised 26 October 2026.**
   - Equivalence-class partitioning, boundary-value analysis and state-transition
     testing are documented in `BLACK_BOX_TESTING.md`.
   - `backend/tests/test_black_box_validation.py`: 37 test methods / 68 logical
     cases for profile validation.
   - `backend/tests/test_black_box_state.py`: 8 state-transition tests for the
     report lifecycle (generate, read, export, expire, regenerate, cascade).
   - `frontend/src/control/ProfileControl.test.ts`: 7 state-transition tests for
     the browser profile lifecycle (create, read, update, delete, guard, cascade).
   - Total: 52 test methods / 83 logical cases, all passing. Every case now
     records Name, Location, Input, Oracle and Log, plus its execution order
     (independent or cascading).

9. **Phase 4 white-box testing documentation — revised 26 October 2026.**
   - CFGs, cyclomatic complexity, basis paths and definition-use tables are in
     `WHITE_BOX_TESTING.md`.
   - `backend/tests/test_white_box.py`: 22 tests covering the two complex methods
     `WeightedScoringStrategy.scoreCandidates` (`V(G)=6`) and
     `RankingControl.generateRankedRecommendations` (`V(G)=5`), plus the
     supporting `computeSuitabilityScore` wrapper (`V(G)=2`) and data-flow pairs.
   - All feasible nodes, predicate outcomes, basis paths and listed DU pairs are
     exercised. Data-flow analysis found and removed one dead store in
     `scoreCandidates` (DF-ANOM-01).

10. **Frontend unit testing — expanded 26 October 2026.**
    - Vitest + jsdom + Testing Library are configured.
    - 39 tests cover format/polyline helpers, weight migration, nearby amenity
      filtering, `ApiCache`, client cache reuse/stale fallback, hard-minimum
      form submission, `ResultsListUI` rendering and the `ProfileControl`
      black-box profile lifecycle.
    - `npm run build` remains the production build check.

### 5.4 Phase 5 — completed 24 October 2026

11. **Formal SLA benchmark — completed.**
    - Script: `scripts/benchmark_api.py`.
    - Results: `sla_benchmark_results.json`.
    - Report: `SLA_BENCHMARK.md`.
    - Cold recommendation p50 1.25 s / p95 2.27 s; warm p50 0.19 s /
      p95 0.28 s; all requests HTTP 200.
    - OneMap cold p50 101 ms / p95 518 ms; 2/10 fallbacks; warm cache hits
      effectively instant.

12. **Dialog Map E2E checklist — completed.**
    - Report: `PHASE5_E2E_CHECKLIST.md`.
    - 18/18 checks passed, covering plan creation, hard minima, ranking,
      grouped factsheet, comparison, PDF/share, persistence, delete guard,
      invalid form, address failure, refresh, simulated outage, health,
      report expiry and 390 px responsive layout.

### 5.5 Production/operational gaps

13. **No authentication or multi-device sync.**
    - Profiles are browser-local.
    - Clearing site data deletes plans.
    - There is no account system.

14. **No CI/CD or production deployment.**
    - No GitHub Actions.
    - No production reverse proxy/HTTPS/host configuration.
    - CORS currently allows all origins for local development.

15. **In-memory report store is single-process.**
    - `ReportStore` holds report paths in process memory.
    - A multi-worker deployment would need shared storage or sticky sessions.
    - Download URLs expire after 15 minutes.

16. **No formal accessibility audit.**
    - Forms have labels, buttons have accessible names, and the map has a text/list alternative via results.
    - No screen-reader or keyboard-only audit has been documented.

17. **Noise-level environment data is not used.**
    - The skeleton originally included `averageNoiseLevelDb`, but no noise dataset is configured.
    - Current environment scoring uses green coverage and PM2.5 baseline.

18. **Cycling commute is intentionally excluded.**
    - `TransitMode` contains `PUBLIC_TRANSIT`, `DRIVING`, `WALKING`.
    - No cycling-mode commute data is collected or scored.

---

## 6. Frozen product decisions

| Decision | Choice |
| --- | --- |
| HDB price geography | HDB town-level median proxy, labelled `isTownProxy` |
| School radius | 1.0 km |
| Environment scoring | Deterministic regional baselines; live PM2.5/UVI/weather display-only |
| Normalisation | Fixed absolute domains, not candidate-relative min-max |
| Criterion importance | 1–10 ratings, relative-normalised to weights summing to 1.0 |
| Cycling commute | Excluded |
| Address confidence | `SequenceMatcher` ratio between query and formatted address |
| Profile creation | Online validation required |
| Data refresh | `DATA_MAX_AGE_HOURS=24`; local snapshots + live refresh; amenities rebuilt from local POI snapshot |
| Commute matrix | `PUBLIC_TRANSIT` near the CBD only; other modes/origins use the hybrid shortlist |
| Hybrid shortlist | Top 50 live; remainder uses 1.35× driving / 1.20× walking / 1.00× PT heuristic |
| Missing commute entry | `dataAvailable=false`; excluded from ranking/comparison/factsheet; map shows insufficient-data notification |
| Hard amenity minimums | Primary/secondary/tertiary schools 1 km; malls 1 km; hospitals 2 km; 0 means disabled |
| Tertiary schools | JCs, Millennia Institute, mixed-level JC/IB schools and autonomous universities; 28-point local supplement |
| Ranking result size | Top 20 items; remaining results discarded |
| Comparison size | 2–4 subzones |
| PDF generation | ReportLab Platypus only |
| Persistence | Profiles in browser IndexedDB; no server database |
| API caching | IndexedDB (`ApiCache`), TTL + ETag revalidation + stale fallback |
| Map amenities | Hidden until a subzone is selected; nearby points only |

---

## 7. Important implementation notes for the next conversation

- **Do not commit `.env`.** It contains OneMap credentials and is ignored by Git.
- **Do not regenerate the 24 MB HDB CSV unnecessarily.** It is already in `backend/assets/data/hdb_resale.csv`.
- **Amenities snapshot:** `make amenities` rebuilds `backend/assets/data/amenities.json` from data.gov.sg and OneMap. It needs the OneMap credentials in `.env`; it geocodes school postal codes and queries OneMap themes/search. `POST /api/v1/data/refresh` instead rebuilds from the cached local point snapshot, adds subzone `aggregates`, and requires no network call.
- **Tertiary-school supplement:** `backend/assets/data/tertiary_schools.json` holds 28 JC/university points and is merged into `amenities.json` at load time. Editing it changes tertiary counts without regenerating the full snapshot. `make amenities` also merges it into the generated file.
- **Start order matters:** backend first, then frontend. `make dev` handles both.
- **`make test`** is the reliable way to run backend tests from the SGPropertyFinder root.
- **Backend startup is ~4 seconds** because it loads 332 subzones, indexes 243k HDB rows and joins 1,200 amenity points.
- **Ranking uses local snapshots first.** `DatasetService.refreshIfStale()` refreshes from data.gov.sg after the configured age. Force a live refresh with:
  ```text
  POST /api/v1/data/refresh
  ```
- **Frontend API base:** Vite proxy `/api` → `http://127.0.0.1:8000`; set `VITE_API_BASE_URL` for non-proxied deployments.
- **Share links:** `POST /api/v1/share/decode` decodes `?share=`. The frontend imports the profile into Dexie, activates it, reruns ranking and highlights the shared subzones. The `share` query parameter is removed after import.
- **API cache:** `ApiCache` uses the separate IndexedDB database `sgpropfinder-api-cache`. Clear it from DevTools if you need to force fresh criteria/geometry/amenities after changing data outside the normal TTL.
- **Amenity layers:** markers are hidden until a subzone is selected. The “Nearby amenities” panel then shows amenities within 2 km and can hide categories.
- **OneMap tiles** use `https://www.onemap.gov.sg/maps/tiles/Default/{z}/{x}/{y}.png`.
- **PDF generation**: `ReportControl` uses ReportLab Platypus directly; WeasyPrint is no longer imported or installed.
- **Data payloads can be large:** `/api/v1/subzones/geometry` returns the full 332-subzone FeatureCollection.
- **Code is committed at `6ba23a2`** (cleanup of unused code). The documentation cleanup and remaining dead-code removals are pending commit.

---

## 8. Key files

### Backend

| File | Purpose |
| --- | --- |
| `backend/main.py` | FastAPI app, routes, cache headers, lifespan data refresh |
| `backend/app/bootstrap.py` | Dependency wiring and registry enrichment |
| `backend/app/services/dataset_service.py` | Live data.gov.sg/snapshot service |
| `backend/app/services/live_environment.py` | Live PM2.5/UVI/forecast provider |
| `backend/app/adapter/one_map_api_adapter.py` | OneMap auth/search/routing/themes |
| `backend/app/adapter/data_gov_sg_adapter.py` | data.gov.sg API/fallback adapter |
| `backend/app/control/house_pricing_retrieval_control.py` | HDB pricing/window/town proxy |
| `backend/app/control/environment_retrieval_control.py` | Regional baselines + live display data |
| `backend/app/control/amenity_retrieval_control.py` | Amenity counts/indicators, local rebuild and snapshot status |
| `backend/app/control/commute_control.py` | Matrix/live routing/cache |
| `backend/app/control/ranking_control.py` | Recommendation orchestration |
| `backend/app/strategy/weighted_scoring_strategy.py` | Fixed-domain MCDA |
| `backend/app/control/report_control.py` | PDF/share URL generation |
| `backend/app/api/handlers.py` | Transport-agnostic REST handlers |
| `scripts/build_amenities.py` | data.gov.sg + OneMap amenity snapshot builder |
| `backend/tests/` | 162 unit/integration tests; black-box EP/BVA + state and white-box CFG + data-flow suites |

### Frontend

| File | Purpose |
| --- | --- |
| `frontend/src/App.tsx` | Application state/orchestration |
| `frontend/src/boundary/ProfileFormUI.tsx` | Plan creation/edit modal content, 1-10 importance ratings, address search |
| `frontend/src/boundary/ProfileSelectorUI.tsx` | Top-right plan dropdown with per-row Edit/Delete |
| `frontend/src/boundary/ResultsListUI.tsx` | Ranked cards/comparison selection |
| `frontend/src/boundary/NeighborhoodMapUI.tsx` | Leaflet choropleth, route and selected-subzone amenity markers |
| `frontend/src/boundary/FactSheetUI.tsx` | Factsheet modal |
| `frontend/src/boundary/ComparisonUI.tsx` | Side-by-side matrix |
| `frontend/src/boundary/ExportReportUI.tsx` | PDF/share modal |
| `frontend/src/boundary/NotificationModalUI.tsx` | Reusable alerts |
| `frontend/src/container/ProfileCatalog.ts` | Dexie/IndexedDB profiles |
| `frontend/src/container/ApiCache.ts` | Dexie/IndexedDB API response cache |
| `frontend/src/utils/amenities.ts` | Amenity layer groups, nearby filtering and colours |
| `frontend/src/utils/weights.ts` | 1–10 importance clamping, legacy migration and persistence |
| `frontend/src/control/ProfileControl.ts` | Client profile CRUD |
| `frontend/src/api/client.ts` | Backend API client with cache/revalidation |
| `frontend/src/styles.css` | Responsive UI and map-layer styles |

### Data assets

| File | Status |
| --- | --- |
| `backend/assets/data/subzones.geojson` | Real URA 332 subzones |
| `backend/assets/data/hdb_resale.csv` | Real HDB resale rows (~243k) |
| `backend/assets/data/planning_area_to_hdb_town.json` | Populated |
| `backend/assets/data/environment_baselines.json` | Deterministic regional baselines |
| `backend/assets/data/commute_matrix.json` | 319/332 subzones |
| `backend/assets/data/amenities.json` | **Present - 1,172 raw points from `make amenities`; `/data/refresh` adds subzone aggregates** |
| `backend/assets/data/tertiary_schools.json` | **Present - 28 JC/university points, merged at load time** |

---

## 9. Recommended next steps

1. **Add CI/CD, HTTPS/CORS production configuration, and a shared report store** if deploying beyond a single process.
2. Optionally extend frontend tests to the App/share-import and map-layer flows.
3. Re-run the SLA benchmark under concurrent load and on representative client networks before production.

---

## 10. Verification summary

| Check | Result |
| --- | --- |
| `make test` | **162 tests OK** |
| `npm test` | **39 frontend tests OK** |
| Black-box suites | **52 methods / 83 logical cases OK** — EP/BVA + report/profile state transitions; see `BLACK_BOX_TESTING.md` |
| White-box suite | **22 tests / 13 basis paths / DU coverage OK** — see `WHITE_BOX_TESTING.md` |
| SLA benchmark | **Passed** — cold recommendations p95 2.27 s; warm p95 0.28 s; see `SLA_BENCHMARK.md` |
| Dialog Map E2E | **18/18 checks passed** — see `PHASE5_E2E_CHECKLIST.md` |
| `make build` / `npm run build` | **Passed** |
| Live Uvicorn health/ready | **Passed**, 332 subzones |
| Browser main flow | **Passed** |
| Dexie reload persistence | **Passed** |
| Weight normalisation | **Passed** (1–10 ratings normalised to 1.0) |
| OneMap address search/routing | **Passed** |
| data.gov.sg live refresh | **Passed**, 332 subzones + 243,176 HDB rows in ~5.2s |
| Amenities snapshot | **Passed**, 1,200 effective points (1,172 base + 28 tertiary); sample counts nonzero |
| HDB town proxy | **Passed**, all 300 current pricing rows use `isTownProxy=true` |
| Amenities-missing fallback | **Passed**, school/amenity criteria excluded and reweighted |
| Commute mode gating | **Passed**, driving/walking no longer read the PT matrix |
| Hybrid commute shortlist | **Passed**, 50 live calls + heuristic remainder with road/path factors |
| Insufficient-data exclusion | **Passed**, 13 subzones removed from ranking/factsheet; map shows bottom notification |
| Share decode + import | **Passed**, endpoint returns profile/codes; frontend build succeeds |
| Ranking result cap | **Passed**, response returns exactly the top 20 items |
| Comparison outside top 20 | **Passed**, comparison requests the full internal ranking |
| API cache | **Passed**, repeated GETs use IndexedDB; stale fallback works |
| Data refresh UI | **Passed**, calls `/data/refresh`, rebuilds amenities, clears cache and reranks |
| Amenity rebuild | **Passed**, local rebuild writes `aggregates` and updates indicators |
| ReportLab-only PDF | **Passed**, includes weights, criterion scores, dates and caveats |
| Amenity map layers | **Passed**, markers hidden until selection; nearby points only |
| Mall coverage | **Passed**, 143 mall points including major-mall supplements |
| Hard amenity minimums | **Passed**, budget-eligible subzones below any minimum are discarded before scoring |
| Tertiary-school counts | **Passed**, 28 JC/university points merged and counted within 1 km |
