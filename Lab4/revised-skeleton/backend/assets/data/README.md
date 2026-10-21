# Data snapshots and fallbacks

Place the last known-good static datasets here, for example:

```text
backend/assets/data/
├── subzones.geojson
├── parks_and_nature_reserves.geojson
├── park_connectors.geojson
├── cycling_paths.geojson
├── mrt_station_exits.geojson
├── hdb_resale_12m.parquet
├── schools.geojson
├── hospitals.geojson
├── malls.geojson
└── manifest.json
```

`manifest.json` should contain `DatasetMetadata` entries:

```json
{
  "hdb_resale": {
    "dataSnapshotId": "SNAPSHOT_2026_Q4",
    "dataAsOf": "2026-10-01T00:00:00Z",
    "sourceUrl": "https://data.gov.sg/...",
    "recordCount": 123456
  }
}
```

When a live API call fails, load the relevant asset and attach a
`DataAvailabilityWarning` with `isStale=true` and `code=STALE_CACHE`.
