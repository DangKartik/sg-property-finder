# External API Data Reference

- **Version:** 1.0
- **Date:** 3 November 2026
- **Scope:** data returned by the external APIs used by SG Property Finder
- **Adapters:** `backend/app/adapter/data_gov_sg_adapter.py`, `backend/app/adapter/one_map_api_adapter.py`, `backend/app/adapter/one_map_token_manager.py`
- **Related documents:** `SPECIFICATIONS_AND_ARCHITECTURE.md`, `LIMITATIONS.md`, `BACKEND_CLASS_REFERENCE.md`

---

## 1. Purpose and boundary

The application consumes two external providers:

| Provider | Used for | Adapter |
| --- | --- | --- |
| data.gov.sg | URA subzones, HDB resale prices, live PM2.5, UVI and weather forecast | `DataGovSgAdapter` |
| OneMap | Address search/geocoding, public-transport/driving/walking routing, theme layers, basemap tiles | `OneMapApiAdapter` |

Adapters convert provider payloads into application entities. Raw provider JSON is
not sent directly to the browser; API responses use the project `ApiEnvelope<T>`
and domain DTOs.

### Caching and fallback behaviour

- **data.gov.sg metadata:** cached for 300 seconds.
- **data.gov.sg datasets:** cached by dataset ID for 300 seconds; on network or
  parse failure, a local asset can be loaded from `backend/assets/data/`.
- **data.gov.sg real-time:** cached for 300 seconds per path/params combination.
- **OneMap:** token cached until refreshed; route TTL cache is owned by
  `CommuteControl`, not the adapter.
- **OneMap failures:** raise `OneMapApiError`; commute control can fall back to a
  straight-line estimate and attach a warning.
- **OneMap token failures:** raise `OneMapAuthenticationError`.

---

## 2. data.gov.sg

### 2.1 Dataset metadata

**Endpoint**

```text
GET {DATA_GOV_SG_BASE_URL}/v2/public/api/datasets/{datasetId}/metadata
```

**Expected response shape**

```json
{
  "data": {
    "lastUpdatedAt": "2026-10-21T00:00:00+00:00",
    "coverageStart": "2017-01-01",
    "recordCount": 243176,
    "rowCount": 243176
  }
}
```

**Fields used**

| Field | Use |
| --- | --- |
| `lastUpdatedAt` or `coverageStart` | `DatasetMetadata.dataAsOf` |
| `recordCount` or `rowCount` | record count / snapshot metadata |
| dataset ID + timestamp | `dataSnapshotId` |

The adapter tolerates the metadata being under `data` or at the top level. If
metadata is absent, the current UTC time is used.

### 2.2 Poll-download URL

**Endpoint**

```text
GET {DATA_GOV_SG_DOWNLOAD_BASE_URL}/v1/public/api/datasets/{datasetId}/poll-download
```

**Expected response shapes**

```json
{
  "data": {
    "url": "https://.../dataset.csv"
  }
}
```

or:

```json
{
  "data": {
    "downloadUrl": "https://.../dataset.csv"
  }
}
```

The adapter also accepts `data` as a plain string. If no URL is returned it raises
`DataGovSgError`.

### 2.3 Static dataset payload

The adapter downloads the signed URL and converts the response to a dictionary:

| Content type | Parsed shape |
| --- | --- |
| JSON object | returned as-is |
| JSON array | `{"items": [...]}` |
| CSV | `{"rows": [ {column: value, ...}, ... ]}` |
| Parquet (local fallback only, if `pyarrow`) | `{"rows": [...]}` |
| GeoJSON | JSON object with `type` and `features` |

The parsed body is wrapped in `RawResponse`:

```python
RawResponse(
    statusCode=200,
    body={"rows": [...]},
    headers={"Content-Type": "text/csv", ...},
    fetchedAt=metadata.dataAsOf,
)
```

If the network/parse fails and a matching local asset exists, the adapter returns
the local payload with `X-Data-Source: local-fallback`.

### 2.4 Real-time PM2.5

**Endpoint**

```text
GET {DATA_GOV_SG_REALTIME_BASE_URL}/pm25
```

**Expected response shape**

```json
{
  "data": {
    "items": [
      {
        "timestamp": "2026-11-03T08:00:00+08:00",
        "readings": {
          "pm25_one_hourly": {
            "national": 17,
            "central": 16,
            "north": 18,
            "south": 15,
            "east": 19,
            "west": 17
          }
        }
      }
    ]
  }
}
```

**Field used:** `data.items[0].readings.pm25_one_hourly.national`, falling back to
`central`. This is display-only and is cached under one shared key, so it is the
same value across subzones.

### 2.5 Real-time UVI

**Endpoint**

```text
GET {DATA_GOV_SG_REALTIME_BASE_URL}/uv
```

**Expected response shape**

```json
{
  "data": {
    "records": [
      {
        "timestamp": "2026-11-03T08:00:00+08:00",
        "index": [
          {"value": 7, "hour": "08:00"}
        ]
      }
    ]
  }
}
```

**Field used:** `data.records[0].index[0].value`.

### 2.6 Real-time 24-hour forecast

**Endpoint**

```text
GET {DATA_GOV_SG_REALTIME_BASE_URL}/twenty-four-hr-forecast
```

**Expected response shape**

```json
{
  "data": {
    "records": [
      {
        "general": {
          "forecast": {
            "code": "TL",
            "text": "Thundery Showers"
          }
        }
      }
    ]
  }
}
```

**Field used:** `data.records[0].general.forecast.code`.

> Live PM2.5/UVI/forecast are display-only. They do not affect the suitability
> score; deterministic regional baselines are used for scoring.

---

## 3. OneMap

### 3.1 Authentication token

**Endpoint**

```text
POST {ONEMAP_BASE_URL}/api/auth/post/getToken
```

**Request**

```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

**Expected response shape**

```json
{
  "access_token": "token-value",
  "expiry_timestamp": 1790000000
}
```

**Fields used:** `access_token`, `expiry_timestamp`. The adapter accepts seconds
or millisecond timestamps and refreshes the token five minutes before expiry.
Missing credentials, network failure or a bad response raise
`OneMapAuthenticationError`.

### 3.2 Address/place search

**Endpoint**

```text
GET {ONEMAP_BASE_URL}/api/common/elastic/search
```

**Query parameters**

```text
searchVal={query}
returnGeom=Y
getAddrDetails=Y
pageNum={page}
```

**Expected response shape**

```json
{
  "found": 2,
  "totalNumPages": 1,
  "pageNum": 1,
  "results": [
    {
      "SEARCHVAL": "PASIR RIS MRT STATION (EW1)",
      "ADDRESS": "10 PASIR RIS CENTRAL",
      "POSTAL": "519634",
      "LATITUDE": "1.3733",
      "LONGITUDE": "103.9494",
      "BUILDING": "PASIR RIS MRT STATION"
    }
  ]
}
```

**Fields used**

| OneMap field | Converted to |
| --- | --- |
| `SEARCHVAL` or `ADDRESS` | `AddressMatch.formattedAddress` |
| `POSTAL` | `AddressMatch.postalCode` |
| `LATITUDE`, `LONGITUDE` | `Coordinates` |
| query vs formatted address | `SequenceMatcher` confidence `0.0–1.0` |

### 3.3 Routing

**Endpoint**

```text
GET {ONEMAP_BASE_URL}/api/public/routingsvc/route
```

**Query parameters**

| Parameter | Meaning |
| --- | --- |
| `start` | `"lat,lng"` origin |
| `end` | `"lat,lng"` destination |
| `routeType` | `pt`, `drive` or `walk` |
| `date`, `time` | Public-transport departure (SGT) |
| `mode` | `TRANSIT` for public transport |
| `maxWalkDistance` | `1000` metres |
| `numItineraries` | `3` |

**Response shape A — route summary (driving/walking)**

```json
{
  "route_summary": {
    "total_time": 1200,
    "total_distance": 8000
  },
  "route_geometry": "encoded-polyline",
  "route_instructions": []
}
```

**Response shape B — public-transport plan**

```json
{
  "plan": {
    "itineraries": [
      {
        "duration": 1800,
        "legs": [
          {
            "distance": 400,
            "legGeometry": {
              "points": "encoded-polyline"
            }
          }
        ]
      }
    ]
  }
}
```

**Conversion**

| OneMap field | Application value |
| --- | --- |
| `total_time` / itinerary `duration` | `CommuteEstimate.durationMinutes` (ceil seconds / 60) |
| `total_distance` / sum of leg `distance` | `CommuteEstimate.distanceKm` |
| `legGeometry.points` | decoded/merged route geometry |
| `routeType` | `TransitMode` |

If OneMap returns no usable summary/itineraries, `MapControl` raises `ValueError`;
`CommuteControl` may replace the failure with a straight-line estimate and an
`ESTIMATED_COMMUTE_FALLBACK` warning.

### 3.4 Theme layers

**Endpoint**

```text
GET {ONEMAP_BASE_URL}/api/public/themesvc/retrieveTheme
```

**Query parameters**

```text
queryName={theme name}
extents={minLat,minLng,maxLat,maxLng}   # optional
```

**Expected response shape**

```json
{
  "SrchResults": [
    {
      "NAME": "Singapore General Hospital",
      "LatLng": "1.2790,103.8350"
    }
  ]
}
```

The amenity builder uses this for OneMap hospital/theme layers and expects
`SrchResults`, `NAME` and `LatLng` (or equivalent coordinates). The rest of the
payload is passed through as raw JSON.

---

## 4. Mapping to application data

| External data | Application entity |
| --- | --- |
| data.gov.sg metadata | `DatasetMetadata` (`dataSnapshotId`, `dataAsOf`, `sourceUrl`, `recordCount`) |
| downloaded dataset | `RawResponse` (`statusCode`, `body`, `headers`, `fetchedAt`) |
| OneMap search result | `AddressMatch` (address, postal code, coordinates, confidence) |
| OneMap route summary/plan | `CommuteEstimate` (duration, distance, transfers, mode, geometry) |
| OneMap theme rows | amenity points (`name`, `category`, coordinates) |
| live PM2.5/UVI/forecast | `EnvironmentInfo` display fields |

The public API never returns raw provider payloads. For example, a factsheet
returns `NeighborhoodDetailDTO`, and a ranking request returns
`RecommendationSet`.

---

## 5. Failure and fallback matrix

| Provider operation | Failure | Application behaviour |
| --- | --- | --- |
| data.gov.sg metadata/download | Network, HTTP or parse error | Try local asset; otherwise raise `DataGovSgError`. |
| data.gov.sg dataset | Failure with local asset present | Return local payload; `X-Data-Source` is local. |
| data.gov.sg real-time | Failure | Omit live PM2.5/UVI/forecast or attach display warning. |
| OneMap token | Missing credentials/network | `OneMapAuthenticationError`; address/routing request fails gracefully. |
| OneMap search | No results | `ADDRESS_NOT_FOUND` API error. |
| OneMap routing | No route/HTTP error | Commute control may use straight-line fallback and warning. |
| OneMap theme | Failure | Builder logs/skips that source; other amenities remain. |

---

## 6. External data limitations

- HDB resale data is keyed by HDB town, not URA subzone; the app uses a town-level
  median proxy labelled `isTownProxy=true`.
- The commute matrix has 319/332 subzone entries. The 13 missing entries are marked
  `dataAvailable=false` and excluded from ranking/factsheet selection.
- Live PM2.5 is a national/central reading; regional PM2.5 baselines are stored
  separately and used for deterministic scoring/display.
- data.gov.sg/OneMap schemas are external contracts; adapter parsing handles known
  shapes but no provider-side schema validation is available.

---

## 7. Security and configuration

- OneMap credentials are read from `.env` via `Settings.fromEnv()`
  and are never logged or returned to the browser.
- `DATA_GOV_SG_API_KEY` is optional and only raises rate limits.
- `.env` is ignored by Git.
- OneMap tile URLs are used directly by Leaflet in the browser; they do not contain
  credentials.

See `ENVIRONMENT.md` for variable names and setup.
