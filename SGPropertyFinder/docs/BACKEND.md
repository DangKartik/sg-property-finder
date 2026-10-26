# Backend

## Run tests

From `SGPropertyFinder/backend`:

```bash
python -m unittest discover -s tests -v
```

The tests use only the standard library and local fixtures; they do not call
OneMap or data.gov.sg.

## Test inventory

| Test file | What it covers |
| --- | --- |
| `test_adapters.py` | data.gov.sg metadata/poll/download/realtime, local fallback, cache, OneMap search/routing |
| `test_token_manager.py` | OneMap token caching and refresh-after-expiry |
| `test_registry.py` | GeoJSON loading, town mapping, representative points, point-in-polygon |
| `test_house_pricing.py` | 12-month window, flat-type keys, town fallback, missing data |
| `test_amenities_environment.py` | school/health/park/mall/MRT counts, static vs live environment |
| `test_commute.py` | CBD matrix, custom routing, cache, next weekday peak |
| `test_scoring_ranking.py` | budget filter, min-max, missing-data renormalisation, tie-break, ranking |
| `test_validation.py` | flat types, address lookup, weight boundaries |
| `test_black_box_validation.py` | formal EP/BVA profile-validation suite (37 methods, 68 logical cases) |
| `test_black_box_state.py` | report-lifecycle state-transition suite (8 tests, independent + cascading) |
| `test_white_box.py` | CFG/basis-path plus data-flow suite for scoring and ranking (16 tests) |
| `test_polyline.py` | encoded-polyline decoding and multi-leg route merging |
| `test_report.py` | PDF bytes, secure metadata, export, share URL |
| `test_api_handlers.py` | address, recommendations, factsheet, comparison, report, geometry, criteria |
| `test_extras.py` | TTL cache, map payload/overlay, top-50 async commute, live environment, profile factory |
| `test_dataset_service.py` | Live-first/snapshot selection, refresh, fallback and status |
| `test_fastapi_endpoints.py` | Live FastAPI route registration and envelope responses |

The FastAPI route layer in `main.py` requires `starlette` and `pydantic`; those are
listed in `requirements.txt`. The suite includes live FastAPI route tests when
those dependencies and `httpx` are installed.

## Run the API

```bash
python -m pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The suite includes live FastAPI route smoke tests when `fastapi`, `starlette`,
`pydantic` and `httpx` are installed. The transport-agnostic handlers in
`app/api/handlers.py` are also covered directly.

## Data assets

`DatasetService` uses the API-first refresh path: local snapshots provide fast
startup, and the service refreshes subzone/HDB data from data.gov.sg when the
snapshots are older than 24 hours. `/api/v1/data/status` exposes source, snapshot,
`dataAsOf`, record count and staleness for the frontend IndexedDB cache layer.
`POST /api/v1/data/refresh` forces a live refresh.

`bootstrap.buildContext()` looks for these files in `backend/assets/data/`
(see `DATA_ASSETS.md` for provenance and formats):

- `subzones.geojson`
- `planning_area_to_hdb_town.json`
- `amenities.json`
- `tertiary_schools.json`
- `environment_baselines.json`
- `hdb_resale.csv`
- `commute_matrix.json`

The files in `tests/fixtures/` are small examples. If an asset is missing, the
app starts with an empty registry or falls back to the data.gov.sg adapter.

## Notes

- Geometry uses Shapely when installed and a dependency-free polygon fallback
  otherwise (`app/core/geometry.py`).
- PDF generation uses ReportLab Platypus exclusively. WeasyPrint and its native
  Pango/GObject dependencies are not required.
- OneMap credentials are read from `.env` via `Settings.fromEnv()`. Token refresh
  is handled by `OneMapTokenManager` five minutes before expiry.
- `httpx` is used for parallel async routing when installed; otherwise the
  adapter falls back to a threadpool.
