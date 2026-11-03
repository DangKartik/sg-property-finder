# Current Limitations

- **Last updated:** 3 November 2026
- **Status:** no known unresolved correctness or API-contract defects.
- **Scope:** current product, data and production limitations.

These are limitations of the current implementation. They are not pending bug
fixes, and several are deliberate scope decisions.

## Data limitations

1. **HDB pricing is town-level.**
   - The public HDB resale dataset has no subzone code.
   - Every price is the HDB-town median proxy and is labelled `isTownProxy=true`.

2. **Environment baselines are deterministic supplied values.**
   - `environment_baselines.json` is not a verified NParks time series.
   - Live PM2.5, UVI and weather are display-only and do not affect ranking.
   - The live PM2.5 display uses the national/central reading, so it can be the
     same across subzones; regional PM2.5 baselines are stored separately.

3. **Commute matrix covers 319/332 subzones.**
   - The 13 missing entries are mainly islands/out-of-bounds.
   - They are marked `dataAvailable=false`, excluded from rankings/comparisons and
     cannot open a factsheet. Clicking them on the map shows a bottom notification
     saying that insufficient data is available.

4. **Fallback commute routes are not cached.**
   - Live route estimates are cached; straight-line fallbacks are recomputed.
   - This causes occasional tail latency in repeated rankings.

5. **`BUKIT TIMAH` and `OUT OF BOUNDS` mappings follow the supplied mapping.**
   - They may not correspond to HDB town pricing data and can produce
     missing-price warnings.

6. **Amenity source refresh is manual.**
   - Subzone and HDB snapshots refresh automatically after 24 hours.
   - `POST /api/v1/data/refresh` rebuilds amenity aggregates from the local point
     snapshot; re-downloading the source amenity data requires `make amenities`.

7. **No independent accuracy reconciliation.**
   - Scoring and pricing formulas are tested, and source snapshots are used, but
     there is no second-source ground-truth audit.

## Functional limitations

8. **No authentication or multi-device sync.**
   - Profiles live in browser IndexedDB.
   - Clearing site data deletes plans.

9. **The report store is single-process.**
   - Generated PDFs are temporary files tracked in process memory.
   - Download links expire after 15 minutes.
   - Multi-worker deployment would need shared storage or sticky sessions.

10. **Noise-level environment data is not used.**
    - A suitable subzone-level noise dataset could not be found in the available
      data sources.
    - Noise is therefore not included in scoring, API contracts or the UI;
      scoring uses green coverage and PM2.5.

11. **Cycling commute is intentionally excluded.**
    - `TransitMode` supports public transport, driving and walking only.

12. **Mobile and accessibility verification is limited.**
    - The layout was checked in a 390 px viewport iframe.
    - No physical-device testing or formal screen-reader audit was performed.

13. **Performance and scalability evidence is limited.**
    - SLA measurements are single-client and localhost-only.
    - No concurrent-load test has been run.
