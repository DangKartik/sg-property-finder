# SG Property Finder — Project Status

**Last updated:** 21 October 2026  
**Repository:** `2006-SCMB-D2`  
**Application folder:** `Lab4/revised-skeleton/`  
**Current branch:** `main`  
**Last commit:** `8013311 Added a Makefile used to start backend and frontend`  
**Working tree:** amenity pipeline and generated snapshot added; not yet committed

This document is intended as the handover/context file for a new conversation or a new developer joining the project.

---

## 1. What this web app is

**SG Property Finder** is a neighbourhood recommender for people planning to move to a new neighbourhood in Singapore. A user creates a preference plan containing:

- a housing budget,
- selected HDB flat types,
- a workplace/CBD anchor,
- a preferred commute mode,
- importance weights for affordability, commute, schools, greenery and amenities.

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
| PDF | WeasyPrint when native Pango/GObject is available; ReportLab fallback |
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
cd C:\Users\Lucas\Documents\GitHub\2006-SCMB-D2\Lab4\revised-skeleton
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
make test       # backend unittest suite (72 tests)
make build      # frontend type-check + production build
make clean      # remove dist and Python caches
make help
```

### Manual run

```powershell
# Terminal 1
cd Lab4/revised-skeleton/backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

# Terminal 2
cd Lab4/revised-skeleton/frontend
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
cd Lab4/revised-skeleton
make test
```

or directly from `backend/`:

```powershell
cd Lab4/revised-skeleton/backend
python -m unittest discover -s tests -v
```

Do **not** run `python -m unittest discover -s backend/tests` from the revised-skeleton root: the tests import `tests.support` and expect `backend/` on `sys.path`.

---

## 3. Current status at a glance

| Area | Status |
| --- | --- |
| Phase 1 — ECB skeleton, entities, documentation | **Completed** |
| Phase 2.1 — spatial engine, data assets, town mapping | **Completed** |
| Phase 2.2 — adapters, retrieval, caching | **Completed** |
| Phase 2.3 — commute strategy | **Completed** with partial matrix coverage |
| Phase 2.4 — MCDA scoring/ranking | **Completed** |
| Phase 2.5 — factsheets, PDF, share URLs | **Completed** (ReportLab fallback on Windows) |
| Phase 2.6 — FastAPI endpoints | **Completed** |
| Phase 3 — frontend | **Completed** |
| Phase 4 — formal black-box/white-box testing | **Not completed** |
| Phase 5 — formal SLA benchmarking/E2E documentation | **Partially completed** (manual verification only) |
| Makefile / one-command local run | **Completed** |
| Real amenities dataset | **Completed** — 1,095 points; `make amenities` rebuilds it |
| Amenity dataset pipeline | **Completed** (`scripts/build_amenities.py`) |
| API-response caching in IndexedDB | **Not completed** (profiles are cached) |
| WeasyPrint native GTK setup | **Not completed** (ReportLab fallback works) |
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
  - `docs/SPECIFICATIONS.md`
  - `docs/OPEN_ISSUES.md`
  - `docs/ENVIRONMENT.md`

### 4.2 Phase 2 — Backend

#### Spatial engine and data assets

- `SubzoneRegistry` loads the official URA 332-subzone GeoJSON.
- Shapely-backed polygon operations with a pure-Python fallback:
  - point-in-polygon,
  - centroid,
  - representative point,
  - bounds,
  - polygon boundary distance.
- `planning_area_to_hdb_town.json` populated.
- Buffer/count logic for schools (1.0 km), hospitals/polyclinics (2 km), parks (500 m), malls (1 km), MRT (800 m).
- Town-level HDB pricing proxy accepted and labelled `isTownProxy`.
- `amenities.json` generated by `scripts/build_amenities.py` (`make amenities`):
  - 1,095 points: 182 primary schools, 144 secondary schools, 462 parks,
    188 MRT stations, 22 polyclinics, 31 hospitals and 66 shopping malls.
  - Sources: MOE school directory, NParks parks, LTA MRT exits, HPB/MOH
    polyclinics, OneMap hospitals and OneMap mall search.
  - Parks (polygons) are represented by `representative_point()`; MRT exits are
    grouped into one point per station; school postal codes are geocoded with
    OneMap Search.
  - Counts use buffer-distance density from the subzone representative point:
    schools/malls 1.0 km, MRT 800 m, parks 500 m, healthcare 2.0 km.
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
  - `/api/v1/data/status` and `POST /api/v1/data/refresh`.
- Live refresh has been manually verified:
  - 332 subzones,
  - 243,176 HDB transactions,
  - ~5.2 seconds.

#### Retrieval engine

- `RetrievalControl` template-method base.
- `HousePricingRetrievalControl`:
  - 12-month rolling HDB window,
  - flat-type keyed `dict[str, HousePricing]`,
  - minimum-5-transaction subzone rule,
  - HDB-town median fallback,
  - median price, median $/sqm and price trend,
  - indexed by town/flat type for startup performance.
- `EnvironmentRetrievalControl`:
  - regional `environment_baselines.json` + `DEFAULT` fallback,
  - static baseline values for scoring,
  - live PM2.5/UVI/forecast isolated as display-only.
- `AmenityRetrievalControl`:
  - school/healthcare/park/mall/MRT counts and nearest distances,
  - graceful missing-data warning when the dataset is absent.

#### Commute

- Precomputed CBD commute matrix keyed by actual URA subzone code.
- 319/332 subzones covered; 13 no-route errors recorded in matrix metadata.
- Next-weekday 08:30 SGT departure.
- Async parallel routing for custom workplaces over a top-50 shortlist.
- TTL cache for commute results.

#### Scoring and ranking

- Hard budget filter using the lowest selected-flat-type median price.
- **Fixed absolute normalisation** (per product decision):
  - price: 200k–1.5M,
  - commute: 0–90 minutes,
  - schools: 0–4,
  - green coverage: 0–100%,
  - amenities: 0–10.
- Missing data: exclude criterion, reweight available criteria to 1.0, attach warning.
- `RecommendationItem` contains 0–100 total score and `CriterionScore` rows.
- Tie-break: shortest commute, then median $/sqm, then subzone code.
- `RecommendationSet` preserves `dataSnapshotId`, `dataAsOf`, warnings and `profileSnapshot`.
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
  - WeasyPrint when native libraries available,
  - ReportLab fallback,
  - short-lived temp report store,
  - secure download metadata,
  - shareable scenario URL.
- FastAPI routes:
  - `POST /api/v1/address/search`
  - `POST /api/v1/profiles/validate`
  - `POST /api/v1/recommendations`
  - `POST /api/v1/commute/overlay`
  - `GET /api/v1/subzones/geometry`
  - `GET /api/v1/subzones/{code}/factsheet`
  - `POST /api/v1/comparison`
  - `POST /api/v1/reports/pdf`
  - `GET /api/v1/reports/download/{report_id}`
  - `GET /api/v1/criteria`
  - `GET /api/v1/health`
  - `GET /api/v1/ready`
  - `GET /api/v1/data/status`
  - `POST /api/v1/data/refresh`
- Unified `ApiEnvelope` (`success`, `data`, `warnings`, `error`).

### 4.3 Phase 3 — Frontend

- DTOs match backend:
  - `ProfileDTO`, `CriterionScoreDTO`, `AddressMatchDTO`, `NeighborhoodDetailDTO`,
    `DataAvailabilityWarningDTO`, `ReportResponseDTO`, `DatasetStatusDTO`.
- Dexie/IndexedDB `ProfileCatalog`:
  - `saveToLocalStorage()`
  - `loadFromLocalStorage()`
  - `deleteProfile()`
- `ProfileControl` performs authoritative backend validation before saving to Dexie.
- Form:
  - budget sliders,
  - flat-type checkboxes,
  - address search with selectable `AddressMatch` results,
  - commute mode,
  - auto-rescaling criteria sliders that always total 100%.
- Saved-plan selector with active badge, disabled delete with tooltip when only one plan exists, and delete confirmation.
- Map:
  - OneMap tiles,
  - subzone choropleth,
  - card-to-polygon and polygon-to-card synchronization,
  - transit/driving route overlay.
- Results:
  - ranked cards,
  - comparison checkboxes,
  - factsheet button,
  - warning count.
- Factsheet modal:
  - multi-flat pricing,
  - town-level proxy badge and note,
  - green coverage/weather/PM2.5/UVI,
  - school/hospital/mall/MRT/park counts,
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

- **72 backend tests pass** via `make test`.
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
  - weight auto-rescaling (40% + four × 15% = 100%).
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

`Lab4/revised-skeleton/Makefile`:

- `install`
- `dev`
- `backend`
- `frontend`
- `test`
- `build`
- `clean`
- `help`

Supporting scripts:

- `scripts/dev.py`
- `scripts/test_backend.py`
- `scripts/clean.py`

---

## 5. Not completed / known gaps

### 5.1 Highest priority

1. **Amenities dataset — resolved 21 October 2026.**
   - `backend/assets/data/amenities.json` is generated by `make amenities`.
   - Factsheets now show real school, park, MRT, polyclinic, hospital and mall counts.
   - The missing-data path is also fixed: absent amenity data excludes the
     school/amenity criteria and renormalises weights instead of scoring zero.
   - Remaining caveat: mall coverage comes from OneMap search results whose names
     contain “mall”/“shopping centre”; major malls with other naming styles may
     be absent.

2. **API-response caching in IndexedDB is not wired.**
   - Profiles are cached in Dexie.
   - The backend already exposes `X-Data-As-Of`, `ETag`, `X-Data-Source`, `X-Data-Stale`, `/api/v1/data/status` and `/api/v1/data/refresh` for a future API cache.
   - Criteria, geometry, factsheets and recommendation responses are currently fetched fresh on each page load/action.

3. **WeasyPrint native GTK libraries are not installed on Windows.**
   - The Python package is installed, but Pango/GObject native libraries are missing.
   - `ReportControl` detects this and uses ReportLab; PDFs work and are tested.
   - A `backend/Dockerfile` installs the native dependencies, but Docker was not run in this environment.

### 5.2 Data limitations

4. **HDB pricing is town-level.**
   - The real HDB dataset has no subzone code.
   - Every price is therefore labelled `isTownProxy=true` and displayed as “Town-Level Median Proxy”.
   - A true subzone median would require a block-to-subzone mapping/geocoding pipeline.

5. **Environment baselines are deterministic user-provided values.**
   - `environment_baselines.json` contains regional green/PM2.5 values.
   - These are **not** a verified 10-year NParks time series; they are the frozen values supplied for the project.
   - Live PM2.5/UVI/weather are display-only and do not affect scores.

6. **Commute matrix coverage is 319/332.**
   - 13 subzones returned OneMap HTTP 404/no route (mostly islands/out-of-bounds).
   - They are recorded in `commute_matrix.json.metadata.errors` and excluded from matrix-based ranking.

7. **`BUKIT TIMAH` and `OUT OF BOUNDS` mappings.**
   - These follow the supplied mapping but may not correspond to HDB town pricing data; such subzones can produce missing-price warnings.

### 5.3 Formal testing not completed

8. **Phase 4 black-box testing documentation**
   - No formal equivalence-class partitioning matrix.
   - No formal boundary-value analysis matrix.
   - No test-minimization document.
   - Some of these checks exist as `unittest` cases, but the required three-column expected/actual matrix has not been produced.

9. **Phase 4 white-box testing documentation**
   - No control-flow graphs.
   - No cyclomatic-complexity calculations.
   - No basis-path test-case table.
   - `RankingControl.generateRankedRecommendations` and `WeightedScoringStrategy.computeSuitabilityScore` were not formally analysed with CFG/`V(G)`.

10. **Frontend unit testing**
    - No Vitest/Jest setup.
    - No React component tests.
    - `npm run build` is the current frontend verification.

### 5.4 Phase 5 not completed

11. **Formal SLA benchmark**
    - The backend ranking calculation was measured at ~13 ms on the local snapshot, but there is no formal HTTP end-to-end benchmark report.
    - There is no formal cold-cache/OneMap routing benchmark (<10 s) with percentiles.

12. **Complete Dialog Map E2E test**
    - Manual browser walkthrough succeeded for the main path.
    - Not systematically covered: invalid form, address failure, delete confirmation, API outage, report expiry, all comparison edge cases, mobile layouts.

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

17. **OneMap “nearby transport” adapter is not implemented.**
    - `getNearbyTransport()` raises `NotImplementedError`.
    - The current app uses the precomputed commute matrix and routing endpoint instead.

18. **Noise-level environment data is not used.**
    - The skeleton originally included `averageNoiseLevelDb`, but no noise dataset is configured.
    - Current environment scoring uses green coverage and PM2.5 baseline.

19. **Cycling commute is intentionally excluded.**
    - `TransitMode` contains `PUBLIC_TRANSIT`, `DRIVING`, `WALKING`.
    - Cycling paths are still used for amenity/active-mobility indicators.

---

## 6. Frozen product decisions

| Decision | Choice |
| --- | --- |
| HDB price geography | HDB town-level median proxy, labelled `isTownProxy` |
| School radius | 1.0 km |
| Environment scoring | Deterministic regional baselines; live PM2.5/UVI/weather display-only |
| Normalisation | Fixed absolute domains, not candidate-relative min–max |
| Cycling commute | Excluded |
| Address confidence | `SequenceMatcher` ratio between query and formatted address |
| Profile creation | Online validation required |
| Data refresh | `DATA_MAX_AGE_HOURS=24`; local snapshots + live refresh |
| Comparison size | 2–4 subzones |
| PDF generation | WeasyPrint when native libs available; ReportLab fallback |
| Persistence | Profiles in browser IndexedDB; no server database |

---

## 7. Important implementation notes for the next conversation

- **Do not commit `.env`.** It contains OneMap credentials and is ignored by Git.
- **Do not regenerate the 24 MB HDB CSV unnecessarily.** It is already in `backend/assets/data/hdb_resale.csv`.
- **Amenities snapshot:** `make amenities` rebuilds `backend/assets/data/amenities.json` from data.gov.sg and OneMap. It needs the OneMap credentials in `.env`; it geocodes school postal codes and queries OneMap themes/search.
- **Start order matters:** backend first, then frontend. `make dev` handles both.
- **`make test`** is the reliable way to run backend tests from the revised-skeleton root.
- **Backend startup is ~4 seconds** because it loads 332 subzones, indexes 243k HDB rows and joins 1,095 amenity points.
- **Ranking uses local snapshots first.** `DatasetService.refreshIfStale()` refreshes from data.gov.sg after the configured age. Force a live refresh with:
  ```text
  POST /api/v1/data/refresh
  ```
- **Frontend API base:** Vite proxy `/api` → `http://127.0.0.1:8000`; set `VITE_API_BASE_URL` for non-proxied deployments.
- **OneMap tiles** use `https://www.onemap.gov.sg/maps/tiles/Default/{z}/{x}/{y}.png`.
- **WeasyPrint**: importing it without native GTK prints a library error; `ReportControl` checks for GObject before importing and falls back to ReportLab.
- **Data payloads can be large:** `/api/v1/subzones/geometry` returns the full 332-subzone FeatureCollection.
- **No commit was made for this update.** `PROJECT_STATUS.md`, `scripts/build_amenities.py` and `backend/assets/data/amenities.json` are new/modified in the working tree.

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
| `backend/app/control/amenity_retrieval_control.py` | Amenity counts/indicators |
| `backend/app/control/commute_control.py` | Matrix/live routing/cache |
| `backend/app/control/ranking_control.py` | Recommendation orchestration |
| `backend/app/strategy/weighted_scoring_strategy.py` | Fixed-domain MCDA |
| `backend/app/control/report_control.py` | PDF/share URL generation |
| `backend/app/api/handlers.py` | Transport-agnostic REST handlers |
| `scripts/build_amenities.py` | data.gov.sg + OneMap amenity snapshot builder |
| `backend/tests/` | 72 unit/integration tests |

### Frontend

| File | Purpose |
| --- | --- |
| `frontend/src/App.tsx` | Application state/orchestration |
| `frontend/src/boundary/ProfileFormUI.tsx` | Plan form, weights, address search |
| `frontend/src/boundary/ProfileSelectorUI.tsx` | Saved plans/delete guard |
| `frontend/src/boundary/ResultsListUI.tsx` | Ranked cards/comparison selection |
| `frontend/src/boundary/NeighborhoodMapUI.tsx` | Leaflet choropleth/route |
| `frontend/src/boundary/FactSheetUI.tsx` | Factsheet modal |
| `frontend/src/boundary/ComparisonUI.tsx` | Side-by-side matrix |
| `frontend/src/boundary/ExportReportUI.tsx` | PDF/share modal |
| `frontend/src/boundary/NotificationModalUI.tsx` | Reusable alerts |
| `frontend/src/container/ProfileCatalog.ts` | Dexie/IndexedDB profiles |
| `frontend/src/control/ProfileControl.ts` | Client profile CRUD |
| `frontend/src/api/client.ts` | Backend API client |
| `frontend/src/styles.css` | Responsive UI styles |

### Data assets

| File | Status |
| --- | --- |
| `backend/assets/data/subzones.geojson` | Real URA 332 subzones |
| `backend/assets/data/hdb_resale.csv` | Real HDB resale rows (~243k) |
| `backend/assets/data/planning_area_to_hdb_town.json` | Populated |
| `backend/assets/data/environment_baselines.json` | Deterministic regional baselines |
| `backend/assets/data/commute_matrix.json` | 319/332 subzones |
| `backend/assets/data/amenities.json` | **Present — 1,095 points generated by `make amenities`** |

---

## 9. Recommended next steps

1. **Wire API-response caching into IndexedDB** using the existing cache/status headers.
2. **Complete Phase 4 documentation**:
   - EP/BVA tables for `InputValidationControl`,
   - CFGs and cyclomatic complexity for ranking/scoring,
   - basis-path test cases,
   - frontend Vitest/Jest tests.
3. **Complete Phase 5**:
   - formal HTTP latency benchmark for `/recommendations`,
   - cold/warm OneMap routing benchmark,
   - full Dialog Map E2E checklist.
4. **Decide whether to install GTK for WeasyPrint or rely on ReportLab/Docker.**
5. **Add CI/CD, HTTPS/CORS production configuration, and a shared report store** if deploying beyond a single process.
6. **Improve mall coverage** by adding major malls whose names do not contain
   “mall” or “shopping centre” (VivoCity, ION Orchard, NEX, etc.) to the OneMap
   builder’s search seeds.
7. Consider a curated HDB block-to-subzone mapping if true subzone-level pricing is required.

---

## 10. Verification summary

| Check | Result |
| --- | --- |
| `make test` | **72 tests OK** |
| `make build` / `npm run build` | **Passed** |
| Live Uvicorn health/ready | **Passed**, 332 subzones |
| Browser main flow | **Passed** |
| Dexie reload persistence | **Passed** |
| Weight auto-rescale | **Passed** (40 + 4×15 = 100) |
| OneMap address search/routing | **Passed** |
| data.gov.sg live refresh | **Passed**, 332 subzones + 243,176 HDB rows in ~5.2s |
| Amenities snapshot | **Passed**, 1,095 points generated; sample counts nonzero |
| Amenities-missing fallback | **Passed**, school/amenity criteria excluded and reweighted |
| ReportLab PDF | **Passed** |
| WeasyPrint rendering on bare Windows | **Not available**; fallback used |
