# Neighbourhood Recommender — Backend + Frontend

Phase 1 skeleton plus Phase 2 backend implementation for the neighbourhood
recommender. This folder is separate from `Lab4/Skeleton Code`.

**Current state:** the backend controls, adapters, scoring, ranking, factsheet,
PDF and REST endpoints are implemented and covered by 70 `unittest` tests. The
React/TypeScript frontend is implemented with Dexie, Leaflet, forms, comparison
and PDF export.

## Structure

```text
revised-skeleton/
├── README.md
├── Makefile
├── .env.example
├── .gitignore
├── scripts/
│   ├── clean.py
│   ├── dev.py
│   └── test_backend.py
├── docs/
│   ├── ENVIRONMENT.md
│   ├── OPEN_ISSUES.md
│   └── SPECIFICATIONS.md
├── backend/
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   ├── README.md
│   ├── assets/data/README.md
│   ├── assets/data/planning_area_to_hdb_town.json
│   ├── tests/
│   │   ├── fixtures/
│   │   └── test_*.py
│   └── app/
│       ├── api/handlers.py
│       ├── bootstrap.py
│       ├── config.py
│       ├── core/
│       │   ├── cache.py
│       │   ├── geometry.py
│       │   ├── serialization.py
│       │   └── time.py
│       ├── services/profile_factory.py
│       ├── adapter/
│       │   ├── data_gov_sg_adapter.py
│       │   ├── one_map_api_adapter.py
│       │   └── one_map_token_manager.py
│       ├── container/
│       │   ├── subzone_registry.py
│       │   └── town_mapping.py
│       ├── control/
│       │   ├── amenity_retrieval_control.py
│       │   ├── commute_control.py
│       │   ├── comparison_control.py
│       │   ├── data_availability_notifier.py
│       │   ├── environment_retrieval_control.py
│       │   ├── house_pricing_retrieval_control.py
│       │   ├── input_validation_control.py
│       │   ├── map_control.py
│       │   ├── neighborhood_details_control.py
│       │   ├── ranking_control.py
│       │   ├── report_control.py
│       │   ├── retrieval_control.py
│       │   └── system_startup_control.py
│       ├── entity/
│       │   ├── address_match.py
│       │   ├── amenity_info.py
│       │   ├── comparison_result.py
│       │   ├── commute_estimate.py
│       │   ├── criterion_score.py
│       │   ├── criterion_weight.py
│       │   ├── data_availability_warning.py
│       │   ├── dataset_metadata.py
│       │   ├── enums.py
│       │   ├── environment_info.py
│       │   ├── house_pricing.py
│       │   ├── pdf_report.py
│       │   ├── preference_profile.py
│       │   ├── recommendation_item.py
│       │   ├── recommendation_set.py
│       │   ├── subzone.py
│       │   ├── subzone_indicators.py
│       │   └── types.py
│       ├── schemas/
│       │   ├── api_envelope.py
│       │   ├── neighborhood_detail_dto.py
│       │   └── profile_dto.py
│       └── strategy/
│           ├── criterion_catalog.py
│           ├── scoring_strategy.py
│           └── weighted_scoring_strategy.py
└── frontend/
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    └── src/
        ├── App.tsx
        ├── main.tsx
        ├── styles.css
        ├── api/
        │   ├── client.ts
        │   └── contracts.ts
        ├── boundary/
        │   ├── ComparisonUI.tsx
        │   ├── ExportReportUI.tsx
        │   ├── FactSheetUI.tsx
        │   ├── NeighborhoodMapUI.tsx
        │   ├── NotificationModalUI.tsx
        │   ├── ProfileFormUI.tsx
        │   ├── ProfileSelectorUI.tsx
        │   └── ResultsListUI.tsx
        ├── container/ProfileCatalog.ts
        ├── control/ProfileControl.ts
        ├── types/dto.ts
        └── utils/
            ├── format.ts
            ├── polyline.ts
            └── weights.ts
```

## Where the diagram classes live

| Diagram class | Location | Note |
| --- | --- | --- |
| `ProfileFormUI` | `frontend/src/boundary/ProfileFormUI.tsx` | React component; includes workplace address search. |
| `ProfileSelectorUI` | `frontend/src/boundary/ProfileSelectorUI.tsx` | React component. |
| `ResultsListUI` | `frontend/src/boundary/ResultsListUI.tsx` | React component. |
| `NeighborhoodMapUI` | `frontend/src/boundary/NeighborhoodMapUI.tsx` | React + Leaflet. |
| `FactSheetUI` | `frontend/src/boundary/FactSheetUI.tsx` | Pricing is keyed by flat type. |
| `ExportReportUI` | `frontend/src/boundary/ExportReportUI.tsx` | Uses a secure download URL, not a server path. |
| `NotificationModalUI` | `frontend/src/boundary/NotificationModalUI.tsx` | React component. |
| `ProfileCatalog` | `frontend/src/container/ProfileCatalog.ts` | Dexie/IndexedDB-backed; async API. |
| `ProfileControl` | `frontend/src/control/ProfileControl.ts` | Client-side CRUD over Dexie + backend validation. |
| `SystemStartupControl` | `backend/app/control/system_startup_control.py` | Loads the subzone registry/cache. |
| `InputValidationControl` | `backend/app/control/input_validation_control.py` | Authoritative validation. |
| `RankingControl` | `backend/app/control/ranking_control.py` | Stateless; receives a `PreferenceProfile`. |
| `MapControl` | `backend/app/control/map_control.py` | Returns serialisable `MapData`. |
| `CommuteControl` | `backend/app/control/commute_control.py` | OneMap routing. |
| `NeighborhoodDetailsControl` | `backend/app/control/neighborhood_details_control.py` | Aggregates amenity/env/pricing/commute data. |
| `RetrievalControl` | `backend/app/control/retrieval_control.py` | Abstract template-method base; returns warnings. |
| `AmenityRetrievalControl` | `backend/app/control/amenity_retrieval_control.py` | Returns `RetrievalResult[list[AmenityInfo]]`. |
| `EnvironmentRetrievalControl` | `backend/app/control/environment_retrieval_control.py` | Returns `RetrievalResult[EnvironmentInfo]`. |
| `HousePricingRetrievalControl` | `backend/app/control/house_pricing_retrieval_control.py` | Returns `RetrievalResult[dict[str, HousePricing]]`. |
| `ReportControl` | `backend/app/control/report_control.py` | Stateless PDF generation. |
| `DataAvailabilityNotifier` | `backend/app/control/data_availability_notifier.py` | Stateless warning factory; no UI dependency. |
| `SubzoneRegistry` | `backend/app/container/subzone_registry.py` | In-memory registry. |
| `TownMapping` | `backend/app/container/town_mapping.py` | Planning area → HDB town mapping. |
| `OneMapApiAdapter` | `backend/app/adapter/one_map_api_adapter.py` | Token auth, routing, detailed address search, themes. |
| `DataGovSgAdapter` | `backend/app/adapter/data_gov_sg_adapter.py` | Metadata, poll-download, real-time APIs. |
| `ScoringStrategy` | `backend/app/strategy/scoring_strategy.py` | Returns rich `CriterionScore` rows. |
| `WeightedScoringStrategy` | `backend/app/strategy/weighted_scoring_strategy.py` | Concrete strategy using the criterion catalogue. |
| `PreferenceProfile` | `backend/app/entity/preference_profile.py` | Full profile entity. |
| `CriterionWeight` | `backend/app/entity/criterion_weight.py` | Uses a catalogue `criterionId`. |
| `Subzone` | `backend/app/entity/subzone.py` | Includes planning area + HDB `townName`; immutable score. |
| `RecommendationSet` | `backend/app/entity/recommendation_set.py` | Snapshot metadata + warnings. |
| `RecommendationItem` | `backend/app/entity/recommendation_item.py` | Rich `criterionScores` list. |
| `CommuteEstimate` | `backend/app/entity/commute_estimate.py` | Typed travel mode, departure time and route geometry. |
| `AmenityInfo` | `backend/app/entity/amenity_info.py` | Includes optional distance. |
| `HousePricing` | `backend/app/entity/house_pricing.py` | Flat type, trend %, town-proxy flag, `asOf`. |
| `EnvironmentInfo` | `backend/app/entity/environment_info.py` | PM2.5/UVI/forecast + typed granularity. |
| `PdfReport` | `backend/app/entity/pdf_report.py` | Browser-safe download metadata only. |

### Added classes

| Class | Location | Why |
| --- | --- | --- |
| `ComparisonUI` | `frontend/src/boundary/ComparisonUI.tsx` | FR12: compare neighbourhoods. |
| `ComparisonControl` | `backend/app/control/comparison_control.py` | Builds a comparison result. |
| `ComparisonResult` | `backend/app/entity/comparison_result.py` | Comparison items + full factsheet details. |
| `CriterionScore` | `backend/app/entity/criterion_score.py` | Raw value, normalised score, weight and source per criterion. |
| `CriterionCatalog` / `CriterionDefinition` | `backend/app/strategy/criterion_catalog.py` | Frozen criterion metadata for sliders and scoring. |
| `AddressMatch` | `backend/app/entity/address_match.py` | Address confirmation for workplace search. |
| `DatasetMetadata` | `backend/app/entity/dataset_metadata.py` | Snapshot/version metadata and fallback manifest. |
| `OneMapTokenManager` | `backend/app/adapter/one_map_token_manager.py` | Caches the OneMap token and refreshes it automatically before expiry. |
| `RetrievalResult<T>` | `backend/app/entity/types.py` | Request-scoped data + warnings. |
| `ApiEnvelope<T>` / `ApiError` | `backend/app/schemas/api_envelope.py` | Standard API response envelope. |
| `SubzoneIndicators` | `backend/app/entity/subzone_indicators.py` | Numeric features consumed by scoring. |
| `ProfileDTO` | `backend/app/schemas/profile_dto.py` | Transport/input model. |
| `NeighborhoodDetailDTO` | `backend/app/schemas/neighborhood_detail_dto.py` | Fact-sheet response with pricing per flat type. |
| `DataAvailabilityWarning` | `backend/app/entity/data_availability_warning.py` | Missing/stale/valid-zero reporting. |
| Frontend DTOs | `frontend/src/types/dto.ts` | API payloads, envelopes and enums. |
| API contracts | `frontend/src/api/contracts.ts` | Cross-tier calls replacing direct object associations. |

## Deliberate changes from the old skeleton

1. **Boundary classes are TypeScript/React, not Python.** The backend has no `boundary/` package.
2. **`ProfileCatalog` and `ProfileControl` are frontend classes.** Profiles live in Dexie/IndexedDB; a Python class cannot write browser storage. The backend is stateless.
3. **`RankingControl` is stateless.** It takes a `PreferenceProfile` directly; there is no server-side `selectProfile` or `profileCatalog`.
4. **`Subzone` no longer stores a mutable suitability score.** Scores live only in `RecommendationItem`.
5. **`DataAvailabilityNotifier` is a stateless warning factory.** Retrieval controls return `RetrievalResult` objects; `NotificationModalUI` displays the warnings.
6. **Adapter responsibilities are corrected.** `OneMapApiAdapter` handles OneMap tokens/routing/address search/themes; `DataGovSgAdapter` handles data.gov.sg metadata/poll-download/real-time APIs.
7. **`MapControl` returns `MapData` (GeoJSON + scores), not raw Shapely polygons.** Shapely `Polygon` remains internal to `Subzone`.
8. **Basemap tiles are a frontend concern.** `getBasemapTile` is removed from the backend adapter; React-Leaflet consumes a tile URL template.
9. **Comparison is present.** `ComparisonUI`, `ComparisonControl`, and `ComparisonResult` cover FR12.
10. **Derived indicators are explicit.** `SubzoneIndicators` holds the numeric features the scoring strategy needs, with explicit radii.
11. **Pricing is keyed by flat type.** `NeighborhoodDetailDTO.pricing` is a map, matching `selectedFlatTypes`.
12. **Reports use safe download metadata.** `PdfReport` returns `downloadUrl`/`expiresAt`, never a server file path.
13. **Desktop-only methods are removed.** `launchUI()` is gone; the React app bootstraps itself. `main()` remains only as an optional data-loading CLI hook.
14. **Phase 2 backend is implemented.** REST handlers, adapters, retrieval, scoring, ranking, factsheets, PDF reports and tests are present. The React/Vite entrypoint is the next layer.

Method names keep the diagram's camelCase to make traceability easy. Convert to PEP 8 snake_case later if desired.

## Specification documents

- `docs/SPECIFICATIONS.md` — frozen scoring, budget, environment, geography, commute, snapshot and API rules.
- `docs/OPEN_ISSUES.md` — contradictions and data limitations that still need a decision before implementation.
- `docs/ENVIRONMENT.md` — `.env` setup and variable reference.

## Environment setup

```bash
cd Lab4/revised-skeleton
cp .env.example .env
```

## Run the application

### One command (recommended)

GNU Make is installed locally via winget (`ezwinports.make`).

```powershell
cd Lab4/revised-skeleton
make install
make dev
```

`make dev` starts FastAPI on port 8000 and Vite on port 5173, waits for both,
and opens the browser. Press **Ctrl+C** to stop both.

Other targets:

```powershell
make backend    # FastAPI only
make frontend   # Vite only
make test       # backend unittest suite
make build      # frontend type-check + production build
make clean
make help
```

### Manual commands

Terminal 1 — backend:

```powershell
cd Lab4/revised-skeleton/backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Terminal 2 — frontend:

```powershell
cd Lab4/revised-skeleton/frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` to `http://127.0.0.1:8000`.
Verify the backend at **http://127.0.0.1:8000/api/v1/health**.

Run backend tests with:

```bash
cd Lab4/revised-skeleton/backend
python -m unittest discover -s tests -v
```

Build the frontend with:

```bash
cd Lab4/revised-skeleton/frontend
npm run build
```

`.env` is ignored by Git. `backend/app/config.py` loads it through
`Settings.fromEnv()`. OneMap currently uses email/password token authentication;
`ONEMAP_EMAIL` and `ONEMAP_PASSWORD` are therefore required in addition to the
requested `ONEMAP_API_KEY` placeholder.

## Handover

See `PROJECT_STATUS.md` for the full completed/not-completed task list, context,
run instructions, known gaps and recommended next steps.

## Implementation status

- **Phase 1:** complete (ECB package layout, entity/enum refactor, docstrings,
  stateless controls, environment setup, specifications).
- **Phase 2:** backend implemented and unit-tested (adapters, retrieval engine,
  commute service, MCDA scoring, factsheet aggregation, PDF/share URLs and REST
  handlers).
- **Frontend:** implemented (React 18 + TypeScript + Vite, Leaflet/React-Leaflet,
  Dexie/IndexedDB, responsive UI, comparison matrix and PDF export).
- **Data assets:** URA subzones, HDB resale prices, town mapping, regional
  environment baselines, the CBD commute matrix and a 1,095-point amenities
  snapshot are populated. `DatasetService` refreshes subzone/HDB snapshots from
  data.gov.sg when older than 24 hours; live PM2.5/UVI/forecast already come
  from real-time APIs. `/api/v1/data/status` and cache headers provide the
  contract for the future IndexedDB cache layer. Amenities are generated from
  data.gov.sg school/park/MRT/polyclinic datasets plus OneMap hospital/mall
  layers; run `make amenities` to rebuild the snapshot.

Run the backend tests from `Lab4/revised-skeleton/backend`:

```bash
python -m unittest discover -s tests -v
```
