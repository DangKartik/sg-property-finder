# Frontend

React 18 + TypeScript + Vite client for SG Property Finder.

## Run

```bash
cd Lab4/revised-skeleton/frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to the backend at
`http://127.0.0.1:8000`.

Start the backend first:

```bash
cd Lab4/revised-skeleton/backend
python -m uvicorn main:app --reload --port 8000
```

## Build

```bash
npm run build
```

The production build is emitted to `dist/`. If the frontend is served from a
different origin, set `VITE_API_BASE_URL` to the backend origin when building.

## Implemented

- Dexie/IndexedDB `ProfileCatalog` with `saveToLocalStorage()`,
  `loadFromLocalStorage()` and `deleteProfile()`.
- Dexie/IndexedDB `ApiCache` with TTLs, ETag revalidation and stale fallback.
- Profile form with budget sliders, flat-type checkboxes, address verification
  and 1–10 criterion importance sliders (backend relative normalisation).
- Saved-plan selector with active badge and guarded delete confirmation.
- OneMap/Leaflet basemap, URA subzone choropleth, card-to-polygon highlighting,
  transit/driving route overlays and selection-driven nearby amenity markers.
- Ranked recommendation sidebar with comparison selection.
- Factsheet modal with multi-flat-type pricing, town-proxy note, amenities,
  environment and data warnings.
- Comparison matrix with a two-subzone guard.
- PDF export (ReportLab) with weights, criterion scores, data dates, caveats,
  binary download and shareable scenario URL.
- Data panel refresh button that refreshes subzone/HDB snapshots, rebuilds
  amenities from the local POI snapshot, clears the API cache and reruns the
  active ranking.
- Vitest/jsdom/Testing Library suite with 21 tests.
- Reusable notification modal for validation and API errors.
- Profile plans persist in IndexedDB through Dexie. The backend exposes
  `X-Data-As-Of`/`ETag`/`/api/v1/data/status` for adding API-response caching to
  IndexedDB in a later iteration.
