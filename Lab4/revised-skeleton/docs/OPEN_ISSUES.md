# Open Issues and Known Limitations

- **Last updated:** 25 October 2026
- **Status:** no open correctness or API-contract issues.
- **Scope:** this is a school project; production-only gaps are listed separately.

All original `OPEN-01`–`OPEN-25` decisions have been resolved and are frozen in
`docs/SPECIFICATIONS.md`. The implementation, tests and Phase 4/5 evidence are
summarized in `PROJECT_STATUS.md`.

## Accepted data limitations

1. **HDB pricing is town-level.**
   - The public HDB resale dataset has no subzone code.
   - Every price is the HDB-town median proxy and is labelled `isTownProxy=true`.

2. **Environment baselines are deterministic supplied values.**
   - `environment_baselines.json` is not a verified NParks time series.
   - Live PM2.5, UVI and weather are display-only and do not affect ranking.

3. **Commute matrix covers 319/332 subzones.**
   - The 13 missing entries are mainly islands/out-of-bounds.
   - They receive a straight-line estimate and an
     `ESTIMATED_COMMUTE_FALLBACK` warning.

4. **Fallback commute routes are not cached.**
   - Live route estimates are cached; straight-line fallbacks are recomputed.
   - This causes occasional tail latency in repeated rankings (documented in
     `docs/SLA_BENCHMARK.md`).

5. **`BUKIT TIMAH` and `OUT OF BOUNDS` mappings follow the supplied mapping.**
   - They may not correspond to HDB town pricing data and can produce
     missing-price warnings.

## Accepted functional limitations

6. **No authentication or multi-device sync.**
   - Profiles live in browser IndexedDB.
   - Clearing site data deletes plans.

7. **The report store is single-process.**
   - Generated PDFs are temporary files tracked in process memory.
   - Download links expire after 15 minutes.
   - Multi-worker deployment would need shared storage or sticky sessions.

8. **Noise-level environment data is unused.**
   - No noise dataset is configured; scoring uses green coverage and PM2.5.

9. **Cycling commute is intentionally excluded.**
   - `TransitMode` supports public transport, driving and walking only.

10. **Mobile layout was verified by a 390 px viewport iframe.**
    - No physical-device or screen-reader audit was performed.

11. **SLA measurements are single-client and localhost-only.**
    - No concurrent-load or representative-network benchmark was run.

## Production-only gaps (not required for submission)

- No CI/CD or production deployment configuration.
- CORS currently allows all origins for local development.
- No formal accessibility audit.
- No HTTPS/reverse-proxy configuration.

These are optional hardening items for a future deployment, not correctness
issues in the current application.
