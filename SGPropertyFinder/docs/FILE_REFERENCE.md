# File Reference — Backend and Frontend

- **Version:** 1.0
- **Date:** 26 October 2026
- **Application:** SG Property Finder
- **Scope:** every source, test, data and configuration file in `SGPropertyFinder/backend` and `SGPropertyFinder/frontend`, plus the supporting `scripts/` and `docs/` folders.

This document explains what each file is responsible for, where it sits in the
ECB-style architecture, and which files to change for common tasks.

---

## 1. Architecture at a glance

```text
Browser
  main.tsx
    -> App.tsx (application state and orchestration)
       -> boundary/*.tsx (forms, map, results, factsheet, comparison, report)
       -> api/client.ts (fetch + IndexedDB cache)
       -> control/ProfileControl.ts (profile CRUD)
       -> container/ProfileCatalog.ts (Dexie/IndexedDB profiles)

HTTP /api/v1/*
  backend/main.py (FastAPI routes, headers, lifespan)
    -> app/api/handlers.py (transport-agnostic request/response logic)
       -> app/control/* (validation, retrieval, ranking, factsheet, report)
          -> app/adapter/* (OneMap, data.gov.sg)
          -> app/container/* (subzone registry, town mapping, report store)
          -> app/strategy/* (criterion catalogue, weighted scoring)
          -> app/entity/* (domain objects)
          -> app/schemas/* (DTOs and API envelope)
```

The backend is stateless. Profiles live in the browser's IndexedDB; the only
server-side state is the short-lived PDF report store.

---

## 2. Backend files

### 2.1 Entry point and configuration

| File | Purpose |
| --- | --- |
| `backend/main.py` | Creates the FastAPI app, registers every `/api/v1` route, adds CORS and cache headers, runs the stale-data refresh on startup, serves PDFs, and exposes `/health` for probes. |
| `backend/requirements.txt` | Python dependencies: FastAPI/Starlette, Uvicorn, HTTP clients, ReportLab, Shapely, PDF test reader. |
| `backend/app/bootstrap.py` | Builds `AppContext`, the dependency-injection graph that wires settings, adapters, controls, strategies, registry and report store; enriches every subzone with pricing, amenity and environment indicators at startup. |
| `backend/app/config.py` | `Settings` dataclass and `Settings.fromEnv()`; loads `.env`, keeps OneMap/data.gov.sg credentials out of source control and exposes timeouts/URLs. |
| `backend/app/__init__.py`, `backend/app/adapter/__init__.py`, `backend/app/api/__init__.py`, `backend/app/container/__init__.py`, `backend/app/control/__init__.py`, `backend/app/core/__init__.py`, `backend/app/entity/__init__.py`, `backend/app/schemas/__init__.py`, `backend/app/services/__init__.py`, `backend/app/strategy/__init__.py` | Package markers only; they contain no runtime logic. |

### 2.2 API layer

| File | Purpose |
| --- | --- |
| `backend/app/api/handlers.py` | Transport-agnostic handler functions used by FastAPI and tests: `validateProfile`, `recommendations`, `factsheet`, `comparison`, `searchAddress`, `commuteOverlay`, `generateReport`, `geometry`, `criteria`, `amenities`, `dataStatus`, `refreshData`, `reportPath`, `decodeShareLink`, `health`, `ready`. Enforces insufficient-data guards and defines `ok()`/`fail()` envelope helpers. |

### 2.3 Control layer

| File | Purpose |
| --- | --- |
| `backend/app/control/amenity_retrieval_control.py` | Loads the amenity snapshot plus tertiary-school supplement; counts schools, hospitals, parks, malls and MRT within their buffer radii; returns per-subzone indicators, all map points, status metadata and a local rebuild. |
| `backend/app/control/commute_control.py` | Resolves commute estimates: CBD public-transport matrix, live OneMap routing for the nearest 50 candidates, spatial heuristics for the remainder, straight-line fallback and warnings. Exposes `insufficientDataSubzoneCodes` from matrix metadata and caches live results. |
| `backend/app/control/comparison_control.py` | Compares two to four subzones, enforces the 2–4 limit and returns comparison items plus full factsheet details. |
| `backend/app/control/data_availability_notifier.py` | Stateless factory for `DataAvailabilityWarning` objects (missing source data, stale cache, partial data, estimated fallback, valid zero). |
| `backend/app/control/environment_retrieval_control.py` | Reads deterministic regional green-coverage and PM2.5 baselines for scoring; attaches display-only live PM2.5/UVI/forecast values. |
| `backend/app/control/house_pricing_retrieval_control.py` | Parses HDB resale rows, builds a town/flat-type index, applies the 12-month rolling window, calculates median price, median $/sqm and trend, and labels every result as a town proxy. |
| `backend/app/control/input_validation_control.py` | Authoritative profile validation: name, budget, flat types, workplace/anchor, address lookup, criterion IDs/rating range, hard minimums and commute mode. Returns field-level errors. |
| `backend/app/control/map_control.py` | Builds `MapData` (GeoJSON, scores, centre), returns one subzone boundary and creates commute route overlays. |
| `backend/app/control/neighborhood_details_control.py` | Aggregates pricing, amenities, environment, commute, warnings and pricing notes into one `NeighborhoodDetailDTO` for the factsheet. |
| `backend/app/control/ranking_control.py` | Orchestrates commute retrieval, available-subzone filtering, scoring, top-20 limiting, warning filtering, snapshot metadata and deterministic ranking output. |
| `backend/app/control/report_control.py` | Generates ReportLab PDFs, stores them with a 15-minute expiry, exports copies, creates shareable base64 URLs and renders profile weights, criterion scores, dates, caveats and warnings. Supports an injected clock for tests. |
| `backend/app/control/retrieval_control.py` | Abstract template-method base for dataset retrieval: fetch, parse, missing-data handling and warning creation. |

### 2.4 Strategy layer

| File | Purpose |
| --- | --- |
| `backend/app/strategy/criterion_catalog.py` | Frozen `CriterionDefinition` metadata (ID, name, unit, direction, fixed domain, buffer radius, default importance) and the default catalogue used by scoring, the form, PDF and tests. |
| `backend/app/strategy/scoring_strategy.py` | Abstract `ScoringStrategy` interface (`computeSuitabilityScore`). |
| `backend/app/strategy/weighted_scoring_strategy.py` | Concrete MCDA scorer: hard budget/amenity filters, 1–10 relative weight normalisation, fixed-domain normalisation, missing-data renormalisation, criterion score rows, total score and tie-break ordering. |

### 2.5 Services

| File | Purpose |
| --- | --- |
| `backend/app/services/dataset_service.py` | Manages local subzone/HDB snapshots, refreshes them from data.gov.sg when older than `DATA_MAX_AGE_HOURS`, records `DatasetStatus` metadata and serves `/data/status` and `/data/refresh`. |
| `backend/app/services/live_environment.py` | Fetches display-only live PM2.5, UVI and weather forecast values with a short TTL cache. |
| `backend/app/services/profile_factory.py` | Converts transport dictionaries to `ProfileDTO`, parses/validates field types and coercion, and converts DTOs to domain `PreferenceProfile` objects. |

### 2.6 Adapters

| File | Purpose |
| --- | --- |
| `backend/app/adapter/data_gov_sg_adapter.py` | data.gov.sg REST client: dataset metadata, poll-download, dataset download, real-time API calls, TTL cache and local JSON/GeoJSON/CSV/Parquet fallback. |
| `backend/app/adapter/one_map_api_adapter.py` | OneMap client: token retrieval/refresh, address search with confidence scores, public-transport/driving/walking routing, theme layers and error handling. |
| `backend/app/adapter/one_map_token_manager.py` | Thread-safe OneMap token cache; refreshes lazily five minutes before expiry and supports invalidation after an auth failure. |

### 2.7 Containers

| File | Purpose |
| --- | --- |
| `backend/app/container/subzone_registry.py` | In-memory URA subzone registry: load GeoJSON, lookup by code, point-in-polygon search, register subzones and export a scored FeatureCollection with `dataAvailable` flags for Leaflet. |
| `backend/app/container/town_mapping.py` | Loads `planning_area_to_hdb_town.json` and resolves a URA planning area to an HDB town for pricing. |
| `backend/app/container/report_store.py` | Maps report IDs to temporary PDF paths and expiry timestamps; removes expired entries and files; accepts an injectable clock for deterministic expiry tests. |

### 2.8 Core utilities

| File | Purpose |
| --- | --- |
| `backend/app/core/cache.py` | Small generic `TTLCache` used by adapters and services. |
| `backend/app/core/geometry.py` | Shapely-backed polygon geometry with a dependency-free fallback: representative point, centroid, bounds, point-in-polygon and distance helpers. |
| `backend/app/core/polyline.py` | Decodes Google/OneMap encoded polylines and merges multi-leg routes for map overlays. |
| `backend/app/core/serialization.py` | Converts dataclasses, enums, datetimes, dates and nested containers to JSON-safe values for API envelopes and PDF snapshots. |
| `backend/app/core/time.py` | CBD constants, Singapore time handling and next-weekday 08:30 departure calculation. |

### 2.9 Entities

| File | Purpose |
| --- | --- |
| `backend/app/entity/address_match.py` | `AddressMatch`: formatted address, postal code, coordinates and confidence. |
| `backend/app/entity/amenity_info.py` | `AmenityInfo`: name, category, coordinates and optional distance. |
| `backend/app/entity/commute_estimate.py` | `CommuteEstimate`: duration, distance, transfers, mode, departure time and route geometry. |
| `backend/app/entity/comparison_result.py` | `ComparisonResult`: compared items plus full factsheet details. |
| `backend/app/entity/criterion_score.py` | `CriterionScore`: raw value, normalised score, weight, weighted score, missing flag and data source. |
| `backend/app/entity/criterion_weight.py` | `CriterionWeight`: one criterion ID and its 1–10 importance rating. |
| `backend/app/entity/data_availability_warning.py` | `DataAvailabilityWarning`: scope, dataset, code, severity, retry/stale flags, source, message and timestamp. |
| `backend/app/entity/dataset_metadata.py` | `DatasetMetadata`: snapshot ID, as-of timestamp, source URL and record count. |
| `backend/app/entity/enums.py` | Shared enums: transit mode, environment granularity, warning severity and data-availability codes. |
| `backend/app/entity/environment_info.py` | `EnvironmentInfo`: weather, green coverage, PM2.5, UVI, forecast code and as-of timestamp. |
| `backend/app/entity/house_pricing.py` | `HousePricing`: median price, price per sqm, trend, flat type, transaction count, town-proxy flag and as-of date. |
| `backend/app/entity/pdf_report.py` | `PdfReport`: browser-safe report metadata (`reportId`, download URL, expiry, filename, content type, size). |
| `backend/app/entity/preference_profile.py` | `PreferenceProfile`: full saved plan and lookup of a criterion importance rating. |
| `backend/app/entity/recommendation_item.py` | `RecommendationItem`: subzone identity, rank, total score and criterion score rows. |
| `backend/app/entity/recommendation_set.py` | `RecommendationSet`: profile snapshot, snapshot metadata, items and warnings; provides add/get/sort helpers. |
| `backend/app/entity/subzone.py` | `Subzone`: code, name, planning area, HDB town, geometry, representative point, optional indicators and `dataAvailable` flag. |
| `backend/app/entity/subzone_indicators.py` | Numeric features consumed by scoring: amenity counts, distances, green coverage, PM2.5, pricing and timestamps. |
| `backend/app/entity/types.py` | Shared value objects: `Coordinates`, `ValidationError`, `ValidationResult`, `RetrievalResult`, `MapData`, `RouteData` and `RawResponse`. |

### 2.10 Schemas / DTOs

| File | Purpose |
| --- | --- |
| `backend/app/schemas/api_envelope.py` | Standard `ApiEnvelope<T>` (`success`, `data`, `warnings`, `error`) and `ApiError`. |
| `backend/app/schemas/neighborhood_detail_dto.py` | Factsheet transport model: pricing keyed by flat type, amenities, environment, commute, warnings and pricing note. |
| `backend/app/schemas/profile_dto.py` | Transport model for profile input, including all five hard-minimum fields. |

### 2.11 Data assets

| File | Purpose |
| --- | --- |
| `backend/assets/data/subzones.geojson` | URA Master Plan 2019 subzone boundaries (332 subzones) used by the registry and map. |
| `backend/assets/data/hdb_resale.csv` | HDB resale transactions (about 243k rows) used for town-level median pricing. |
| `backend/assets/data/planning_area_to_hdb_town.json` | Mapping from URA planning areas to HDB towns. |
| `backend/assets/data/environment_baselines.json` | Deterministic regional green-coverage and PM2.5 baselines for scoring. |
| `backend/assets/data/commute_matrix.json` | Precomputed CBD public-transport commute times for 319/332 subzones, including an error list. |
| `backend/assets/data/amenities.json` | Generated amenity snapshot (1,172 base points) with metadata, item list and optional subzone aggregates. |
| `backend/assets/data/tertiary_schools.json` | 28-point JC/university supplement merged into amenities at load time. |

### 2.12 Backend tests

| File | Purpose |
| --- | --- |
| `backend/tests/__init__.py` | Makes `tests` an importable package (`tests.support`). |
| `backend/tests/support.py` | Shared fixtures: `FakeOneMap`, `FakeTokenManager`, fixture registry/control loaders, indicator attachment, profile builders and JSON profile payload. |
| `backend/tests/test_adapters.py` | data.gov.sg metadata/poll/download/real-time/fallback and OneMap search/routing with in-memory HTTP stubs. |
| `backend/tests/test_amenities_environment.py` | Amenity counts/radii, sorting, missing source, local rebuild, tertiary supplement and environment baselines/live display. |
| `backend/tests/test_api_handlers.py` | Transport-agnostic handler paths: address, validation, recommendations, factsheet, comparison, report, geometry, criteria. |
| `backend/tests/test_black_box_state.py` | **New:** black-box state-transition tests for report generation, download, export, expiry, regeneration and the cascading lifecycle. |
| `backend/tests/test_black_box_validation.py` | Formal EP/BVA profile-validation suite (37 methods, 68 logical cases). |
| `backend/tests/test_commute.py` | CBD matrix gating, custom routing, cache, next-weekday peak and fallback behaviour. |
| `backend/tests/test_dataset_service.py` | Live-first/snapshot selection, forced refresh, fallback and status metadata. |
| `backend/tests/test_extras.py` | TTL cache, map payload/overlay, async top-50 commute, live environment provider and profile factory parsing. |
| `backend/tests/test_fastapi_endpoints.py` | FastAPI route smoke tests, response envelopes, headers, address/recommendation/comparison/share/factsheet/report download. |
| `backend/tests/test_house_pricing.py` | 12-month window, flat-type keys, town proxy, median/trend and missing data. |
| `backend/tests/test_polyline.py` | Encoded-polyline decoding and multi-leg merging. |
| `backend/tests/test_registry.py` | GeoJSON loading, town mapping, representative points and point-in-polygon. |
| `backend/tests/test_report.py` | PDF bytes, secure metadata, export, share URL and PDF content. |
| `backend/tests/test_scoring_ranking.py` | Budget filter, normalisation, missing-data renormalisation, tie-break, ranking cap and comparison outside top 20. |
| `backend/tests/test_token_manager.py` | OneMap token caching, expiry and refresh-after-invalid-token. |
| `backend/tests/test_validation.py` | Direct validator unit tests for flat types, address lookup, weight bounds and minimum counts. |
| `backend/tests/test_white_box.py` | **Updated:** CFG/basis-path tests plus data-flow tests for scoring and ranking (17 tests). |
| `backend/tests/fixtures/subzones.geojson` | Three-subzone fixture used by every backend test. |
| `backend/tests/fixtures/amenities.json` | 16-point amenity fixture covering every category. |
| `backend/tests/fixtures/hdb_resale.csv` | Small HDB resale fixture with town/flat-type rows. |
| `backend/tests/fixtures/commute_matrix.json` | Small CBD commute matrix fixture. |
| `backend/tests/fixtures/environment_baselines.json` | Small regional environment baseline fixture. |
| `backend/tests/fixtures/planning_area_to_hdb_town.json` | Planning-area fixture mapping. |

---

## 3. Frontend files

### 3.1 Root and configuration

| File | Purpose |
| --- | --- |
| `frontend/index.html` | HTML shell; provides the `#root` element and loads `src/main.tsx`. |
| `frontend/package.json` | npm scripts (`dev`, `build`, `preview`, `test`, `test:watch`) and runtime/dev dependencies. |
| `frontend/package-lock.json` | npm lockfile; generated, commit it but do not hand-edit. |
| `frontend/tsconfig.json` | Strict TypeScript configuration for the React/Vite source. |
| `frontend/vite.config.ts` | Vite dev server, `/api` proxy to port 8000, and Vitest/jsdom/setup configuration. |

### 3.2 Application shell

| File | Purpose |
| --- | --- |
| `frontend/src/main.tsx` | React entry point: imports Leaflet CSS and global styles, mounts `<App />` in StrictMode. |
| `frontend/src/App.tsx` | Application state and orchestration: loads criteria/map/amenities/status, restores profiles from IndexedDB, handles share-link import, ranking, profile create/edit/delete, map/result/factsheet/comparison/report state, insufficient-data bottom notices, data refresh and notifications. |
| `frontend/src/styles.css` | Responsive layout, panels, modal, map, form, results and notification styles. |
| `frontend/src/vite-env.d.ts` | Vite client type declarations. |

### 3.3 API layer

| File | Purpose |
| --- | --- |
| `frontend/src/api/contracts.ts` | TypeScript interfaces for every backend capability (criteria, address, validation, ranking, amenities, map, factsheet, report, share, data status, comparison). |
| `frontend/src/api/client.ts` | Fetch wrapper: base URL, envelopes, typed errors, IndexedDB cache, TTLs, ETag revalidation, stale fallback, cache pruning and binary PDF download. |
| `frontend/src/api/client.test.ts` | Tests cache reuse, stale fallback and request/error behaviour of the API client. |

### 3.4 Boundary components

| File | Purpose |
| --- | --- |
| `frontend/src/boundary/ProfileFormUI.tsx` | Create/edit plan modal: budget, flat types, address search/selection, commute mode, 1–10 importance sliders, five hard-minimum inputs and save/validation handling. |
| `frontend/src/boundary/ProfileSelectorUI.tsx` | Top-right plan picker with active plan, per-row Edit/Delete, delete confirmation, one-plan guard and portal-based modal. |
| `frontend/src/boundary/ResultsListUI.tsx` | Ranked recommendation cards, comparison checkboxes, factsheet action (replaced by an “Insufficient data” label for unavailable codes), warning counts and PDF export button. |
| `frontend/src/boundary/NeighborhoodMapUI.tsx` | Leaflet/React-Leaflet map: OneMap tiles, subzone choropleth, selected/highlighted polygons, unavailable-data styling/tooltips, route overlay, refresh control and selection-driven nearby amenity markers. |
| `frontend/src/boundary/FactSheetUI.tsx` | Factsheet modal: multi-flat pricing, town-proxy badge, environment values, grouped amenities with distances, commute details and warnings. |
| `frontend/src/boundary/ComparisonUI.tsx` | Side-by-side comparison matrix for two to four subzones. |
| `frontend/src/boundary/ExportReportUI.tsx` | PDF export modal: generate report, binary download, expiry display and share URL copy. |
| `frontend/src/boundary/NotificationModalUI.tsx` | Reusable accessible modal for validation, data and API notices. |
| `frontend/src/boundary/ProfileFormUI.test.tsx` | Tests hard-minimum rendering/submission in the plan form. |
| `frontend/src/boundary/ProfileSelectorUI.test.tsx` | Tests plan menu, Edit/Delete actions, delete confirmation and one-plan guard. |
| `frontend/src/boundary/ResultsListUI.test.tsx` | Tests ranked card rendering, comparison controls, warnings and top-20 display. |

### 3.5 Container (browser persistence)

| File | Purpose |
| --- | --- |
| `frontend/src/container/ProfileCatalog.ts` | Dexie/IndexedDB repository for profiles: save, load, delete, add, get and list; normalises legacy weights on read/write. |
| `frontend/src/container/ApiCache.ts` | Dexie/IndexedDB cache for API envelopes with ETag, stored/expiry timestamps, delete, clear and 7-day pruning; failures are non-fatal. |
| `frontend/src/container/ApiCache.test.ts` | Tests cache persistence, deletion and pruning. |

### 3.6 Control

| File | Purpose |
| --- | --- |
| `frontend/src/control/ProfileControl.ts` | Client profile CRUD controller: validates through the backend contract before saving, generates IDs/timestamps, and raises `ProfileValidationError` with field errors. |
| `frontend/src/control/ProfileControl.test.ts` | **New:** black-box state-transition tests for the profile lifecycle (`EMPTY`, `SAVED`, `UPDATED`, `DELETED`), including independent transitions, guard rejection and a cascading CRUD test. |

### 3.7 Types and utilities

| File | Purpose |
| --- | --- |
| `frontend/src/types/dto.ts` | Browser-facing transport types and enums mirroring backend envelopes, profiles, recommendations, factsheets, reports, share links, amenities and status. |
| `frontend/src/utils/amenities.ts` | Amenity category groups, colours, nearby filtering (2 km) and grouping for the map/factsheet. |
| `frontend/src/utils/format.ts` | Price/number/date formatting and score-to-colour mapping. |
| `frontend/src/utils/polyline.ts` | Client-side encoded-polyline decoding for route overlays. |
| `frontend/src/utils/subzones.ts` | Reads `dataAvailable` flags from map GeoJSON and returns unavailable subzone codes. |
| `frontend/src/utils/weights.ts` | 1–10 importance clamping/defaults, legacy 0–100 migration and profile weight normalisation. |
| `frontend/src/utils/amenities.test.ts` | Tests category grouping, nearby filtering and colours. |
| `frontend/src/utils/format.test.ts` | Tests price, number, date and score formatting. |
| `frontend/src/utils/polyline.test.ts` | Tests polyline decoding. |
| `frontend/src/utils/subzones.test.ts` | Tests extraction of unavailable subzone codes from map GeoJSON. |
| `frontend/src/utils/weights.test.ts` | Tests clamping, defaults and legacy weight migration. |
| `frontend/src/test/setup.ts` | Vitest setup: `jest-dom` matchers and `fake-indexeddb` for Dexie tests. |

---

## 4. Supporting scripts

| File | Purpose |
| --- | --- |
| `scripts/dev.py` | Starts FastAPI and Vite together, waits for both, opens the browser and stops both on Ctrl+C. |
| `scripts/test_backend.py` | Runs the backend `unittest` discovery from the correct working directory. |
| `scripts/benchmark_api.py` | Phase 5 SLA benchmark: spawns the API, measures cold/warm HTTP and OneMap latency and writes results. |
| `scripts/build_amenities.py` | Rebuilds `amenities.json` from data.gov.sg datasets and OneMap themes; geocodes schools, groups MRT exits, merges the tertiary supplement and writes metadata. |
| `scripts/clean.py` | Removes `frontend/dist` and Python cache directories. |

## 5. Documentation

All application documentation is kept in `SGPropertyFinder/docs/`.

| File | Purpose |
| --- | --- |
| `docs/README.md` | Documentation index plus the full application overview, structure, commands and implementation status. |
| `docs/BACKEND.md` | Backend run instructions, test inventory and implementation notes. |
| `docs/FRONTEND.md` | Frontend run/build instructions and implemented features. |
| `docs/DATA_ASSETS.md` | Data sources, snapshot formats, categories and regeneration rules. |
| `docs/PROJECT_STATUS.md` | Handover document: completed work, frozen decisions, known gaps and verification summary. |
| `docs/SPECIFICATIONS.md` | Frozen scoring, budget, environment, geography, commute, snapshot and API rules. |
| `docs/BLACK_BOX_TESTING.md` | **Updated:** EP, BVA and state-transition testing with Name/Location/Input/Oracle/Log, test levels, coverage and execution order. |
| `docs/WHITE_BOX_TESTING.md` | **Updated:** CFGs, cyclomatic complexity, basis paths and data-flow (DU) testing for scoring/ranking. |
| `docs/FILE_REFERENCE.md` | This file: responsibilities of every backend/frontend/support file. |
| `docs/ENVIRONMENT.md` | `.env` setup and environment-variable reference. |
| `docs/OPEN_ISSUES.md` | Accepted data/functional limitations and production-only gaps. |
| `docs/SLA_BENCHMARK.md` | Phase 5 latency benchmark method and results. |
| `docs/sla_benchmark_results.json` | Raw benchmark samples (generated evidence, not Markdown). |
| `docs/PHASE5_E2E_CHECKLIST.md` | 18-check live browser/API end-to-end checklist. |

## 6. Root files

| File | Purpose |
| --- | --- |
| `SGPropertyFinder/Makefile` | One-command install, dev, test, benchmark, amenities, build and clean targets. |
| `SGPropertyFinder/.env.example` | Template for `.env`; documents OneMap/data.gov.sg settings. |
| `SGPropertyFinder/.env` | Local secrets; ignored by Git, never commit or document values. |
| `SGPropertyFinder/.gitignore` | Ignores `.env`, `node_modules`, `dist`, Python caches and generated report files. |

---

## 7. Which file should I change?

| Task | Files |
| --- | --- |
| Add or change a scoring rule | `backend/app/strategy/weighted_scoring_strategy.py`, `backend/app/strategy/criterion_catalog.py`, `docs/SPECIFICATIONS.md`, scoring tests |
| Add a new API endpoint | `backend/app/api/handlers.py`, `backend/main.py`, `frontend/src/api/contracts.ts`, `frontend/src/api/client.ts`, endpoint tests |
| Change profile validation | `backend/app/control/input_validation_control.py`, `backend/app/services/profile_factory.py`, `frontend/src/boundary/ProfileFormUI.tsx`, `frontend/src/control/ProfileControl.ts`, validation tests |
| Change profile storage/CRUD | `frontend/src/container/ProfileCatalog.ts`, `frontend/src/control/ProfileControl.ts`, `frontend/src/App.tsx`, `ProfileControl.test.ts` |
| Change the map or amenity layers | `frontend/src/boundary/NeighborhoodMapUI.tsx`, `frontend/src/utils/amenities.ts`, `backend/app/control/amenity_retrieval_control.py` |
| Change factsheet contents | `backend/app/control/neighborhood_details_control.py`, `backend/app/schemas/neighborhood_detail_dto.py`, `frontend/src/boundary/FactSheetUI.tsx` |
| Change comparison behaviour | `backend/app/control/comparison_control.py`, `frontend/src/boundary/ComparisonUI.tsx` |
| Change PDF or share links | `backend/app/control/report_control.py`, `frontend/src/boundary/ExportReportUI.tsx`, `frontend/src/api/client.ts` |
| Refresh external data | `backend/app/services/dataset_service.py`, `backend/app/adapter/data_gov_sg_adapter.py`, `scripts/build_amenities.py` |
| Change tests or add a technique | `backend/tests/test_black_box_validation.py`, `test_black_box_state.py`, `test_white_box.py`, `frontend/src/control/ProfileControl.test.ts`, the matching docs |

## 8. Notes for maintainers

- `backend/assets/data/hdb_resale.csv` is a 24 MB real snapshot; do not regenerate or commit replacements unnecessarily.
- `package-lock.json` and `docs/sla_benchmark_results.json` are generated artifacts; update them through their tools/scripts.
- The backend never stores user profiles; `ProfileCatalog` (Dexie) is the source of truth in the browser.
- `.env` contains credentials and is intentionally untracked.
- Tests use local fixtures and never call OneMap or data.gov.sg; live checks belong to the E2E/SLA documents.
