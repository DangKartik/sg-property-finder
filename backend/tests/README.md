# Backend tests

Run from `Lab4/revised-skeleton/backend`:

```bash
python -m unittest discover -s tests -v
```

The suite uses local fixtures only; it never calls OneMap or data.gov.sg.

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
| `test_white_box.py` | CFG/basis-path suite for scoring and ranking (9 tests) |
| `test_polyline.py` | encoded-polyline decoding and multi-leg route merging |
| `test_report.py` | PDF bytes, secure metadata, export, share URL |
| `test_api_handlers.py` | address, recommendations, factsheet, comparison, report, geometry, criteria |
| `test_extras.py` | TTL cache, map payload/overlay, top-50 async commute, live environment, profile factory |
| `test_dataset_service.py` | Live-first/snapshot selection, refresh, fallback and status |
| `test_fastapi_endpoints.py` | Live FastAPI route registration and envelope responses |

The FastAPI route layer in `main.py` requires `starlette` and `pydantic`; those are
listed in `requirements.txt`. The suite includes live FastAPI route tests when
those dependencies and `httpx` are installed.
