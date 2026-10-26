# Phase 5 — Formal SLA Benchmark

- **Date:** 24 October 2026
- **Scope:** HTTP API latency and live OneMap commute routing
- **Benchmark script:** `scripts/benchmark_api.py`
- **Raw results:** `sla_benchmark_results.json`

---

## 1. Objective

Measure the end-to-end latency of the FastAPI application under a controlled,
single-user load and compare it with the project's 5-second cold-ranking target.
The benchmark covers:

- cold and warm `POST /api/v1/recommendations` requests;
- supporting GET/POST endpoints;
- live OneMap public-transport routing, cold and warm;
- failure/fallback frequency and response sizes.

## 2. Test environment

| Item | Value |
| --- | --- |
| Host OS | Windows 11 (10.0.26200) |
| CPU | AMD64 Family 25 Model 97, 12 logical processors |
| RAM | ~16 GB |
| Python | 3.13.5 |
| Backend | FastAPI + Uvicorn, dedicated process on `127.0.0.1:8011` |
| Frontend | Not involved in the HTTP measurements |
| Data refresh | Disabled for the run (`DATA_MAX_AGE_HOURS=99999`) |
| External services | Live OneMap routing and token exchange |
| Load | One sequential client, no concurrency |

### Data snapshot

| Dataset | Snapshot | Records |
| --- | --- | --- |
| Subzones | `LOCAL:1792831021318340700` | 332 |
| HDB resale | `LOCAL:1792831025271468900` | 243,500 |
| Amenities | `LOCAL:1792831025740852600` | 1,200 |

## 3. Workload

The profile used for all recommendation calls:

```text
Budget:            SGD 0 – 2,000,000
Flat type:         4 ROOM
Commute mode:      PUBLIC_TRANSIT
Importance:        PRICE=1, COMMUTE_TIME=10, SCHOOL=1, GREEN=1, AMENITIES=1
Hard minimums:     all 0
```

### Cold recommendations

Five unique non-CBD anchors were used once each:

- Pasir Ris
- Jurong East
- Punggol
- Woodlands
- Serangoon

Each anchor produces a cache miss for every commute destination, exercising the
live public-transport shortlist.

### Warm recommendations

The Pasir Ris payload was repeated **50 times** after one warm-up call. Repeated
calls should use the in-process commute cache.

### OneMap commute micro-benchmark

`CommuteControl.retrieveCommute()` was called for **10 unique destinations** from
Pasir Ris (cold), then for the same 10 destinations again (warm). The control
uses the normal 7-day TTL cache. Two cold calls fell back to the straight-line
estimate because OneMap returned no usable route.

### Percentiles

Percentiles use linear interpolation over the sorted samples. Cold `n=5`, warm
`n=50`; the cold p99 is therefore an extrapolation and should be treated as
indicative rather than statistically stable.

## 4. HTTP results

All timings are milliseconds.

| Endpoint | n | mean | p50 | p95 | p99 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `GET /api/v1/health` | 50 | 0.86 | 0.84 | 1.12 | 1.18 | 1.18 |
| `GET /api/v1/criteria` | 50 | 0.95 | 0.92 | 1.08 | 1.33 | 1.43 |
| `GET /api/v1/subzones/geometry` | 50 | 333.67 | 334.44 | 382.96 | 386.03 | 386.40 |
| `GET /api/v1/amenities` | 50 | 12.94 | 11.54 | 13.36 | 45.81 | 76.73 |
| `POST /api/v1/recommendations` — cold | 5 | 1,485.38 | 1,250.24 | 2,267.09 | 2,434.53 | 2,476.39 |
| `POST /api/v1/recommendations` — warm | 50 | 194.37 | 188.91 | 281.32 | 334.94 | 341.39 |
| `POST /api/v1/comparison` | 25 | 216.73 | 207.04 | 242.03 | 478.48 | 552.98 |
| `GET /api/v1/subzones/{code}/factsheet` | 25 | 62.17 | 61.59 | 72.47 | 74.85 | 75.26 |
| `POST /api/v1/reports/pdf` | 5 | 263.38 | 224.19 | 411.42 | 441.11 | 448.53 |

### Cold recommendation samples

| Anchor | Latency (ms) | HTTP | Items | Warnings |
| --- | ---: | ---: | ---: | ---: |
| Pasir Ris | 1,119.79 | 200 | 20 | 7 |
| Jurong East | 2,476.39 | 200 | 20 | 17 |
| Punggol | 1,150.62 | 200 | 20 | 15 |
| Woodlands | 1,250.24 | 200 | 20 | 17 |
| Serangoon | 1,429.88 | 200 | 20 | 19 |

All cold requests succeeded and returned the expected top 20 items.

## 5. OneMap commute results

| Path | n | mean | p50 | p95 | p99 | max | Fallbacks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Cold live PT | 10 | 177.80 | 100.68 | 517.71 | 736.31 | 790.96 | 2 |
| Warm cache PT | 10 | 19.69 | 0.01 | 99.24 | 105.50 | 107.06 | — |

- Cold live routing had a median of ~101 ms but a long tail up to ~791 ms.
- Two of ten cold calls fell back to the straight-line estimate.
- Warm cache hits are effectively instant (~0.01 ms); the warm p95 of ~99 ms is
  caused by the two fallback destinations, which are not cached by design.

## 6. Interpretation

### Against the SLA target

The project target is a cold ranking below **5 seconds**. The observed cold
p50 was **1.25 s** and the cold p95 was **2.27 s**, so the target was met on this
machine and network. However, the cold p95 leaves less than half of the 5-second
budget for slower client networks, OneMap latency spikes or CPU contention.

Warm ranking is comfortably below 0.35 s at p99.

### Main latency drivers

1. **Live OneMap routing** dominates cold ranking. With 50 shortlisted
   destinations, a few slow routes raise the whole request.
2. **Static geometry** takes ~334 ms per call because the full 332-feature
   GeoJSON is serialised every time.
3. **PDF generation** is ~224 ms at p50 and ~449 ms at max for two subzones.
4. **Factsheets** are consistently ~62 ms.
5. **Health and criteria** are sub-millisecond to low-millisecond.

### Tail behaviour

The warm recommendation tail (p99 ~335 ms) is not caused by the primary cache
path; it is consistent with occasional recomputation or fallback handling. The
cold sample of only five requests makes cold p99 indicative only.

## 7. Findings and recommendations

1. **No failures were observed**: all five cold recommendation samples returned
   HTTP 200 with success envelopes, and no benchmark request raised an exception
   or produced an error envelope.
2. **The 5-second cold SLA is met**, but cold p95 is the metric to watch.
3. **Cache hits are highly effective**: warm p50 is ~15% of cold p50.
4. **Fallback routes are not cached.** This is intentional because fallback is a
   degraded estimate, but it means repeated requests can pay the live-routing
   cost again for those destinations.
5. **Geometry serialisation is the largest non-routing cost.** Consider caching
   the serialised geometry response or using a conditional HTTP response if the
   map payload grows.
6. **Re-run under concurrency** before production: this benchmark is
   single-client and does not measure contention between simultaneous rankings.

## 8. Reproduce

```powershell
cd SGPropertyFinder
python scripts/benchmark_api.py --spawn-server --warm-samples 50 `
  --output docs/sla_benchmark_results.json
```

The script starts a dedicated Uvicorn instance, waits for `/api/v1/health`,
runs the HTTP and OneMap measurements, writes the JSON result and stops the
server. The data refresh is disabled for the spawned server so the snapshot is
stable during the run.

## 9. Limitations

- Single host, localhost, sequential requests; no network emulation.
- Cold sample is only five requests; p95/p99 are indicative.
- OneMap results depend on live external network and routing service load.
- The benchmark measures the API process, not browser rendering, IndexedDB
  caching or frontend latency.
- PDF download transfer time is excluded; only generation is measured.
- No sustained-load or memory-growth test.
