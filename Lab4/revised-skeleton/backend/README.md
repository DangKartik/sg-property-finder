# Backend

## Run tests

From `Lab4/revised-skeleton/backend`:

```bash
python -m unittest discover -s tests -v
```

The tests use only the standard library and local fixtures; they do not call
OneMap or data.gov.sg.

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

`bootstrap.buildContext()` looks for these files in `backend/assets/data/`:

- `subzones.geojson`
- `planning_area_to_hdb_town.json`
- `amenities.json`
- `environment_baselines.json`
- `hdb_resale.csv`
- `commute_matrix.json`

The files in `tests/fixtures/` are small examples. If an asset is missing, the
app starts with an empty registry or falls back to the data.gov.sg adapter.

## Notes

- Geometry uses Shapely when installed and a dependency-free polygon fallback
  otherwise (`app/core/geometry.py`).
- WeasyPrint is used when its native Pango/GObject libraries are available;
  otherwise PDF generation falls back to ReportLab. On Windows, install the GTK3
  runtime, use the provided `Dockerfile`, or use a Linux environment with Pango.

```bash
docker build -t sgpropfinder-backend .
docker run --env-file .env -p 8000:8000 sgpropfinder-backend
```
- OneMap credentials are read from `.env` via `Settings.fromEnv()`. Token refresh
  is handled by `OneMapTokenManager` five minutes before expiry.
- `httpx` is used for parallel async routing when installed; otherwise the
  adapter falls back to a threadpool.
