# Requirements Verification and Traceability

- **Version:** 1.1
- **Date:** 8 November 2026
- **Application:** SG Property Finder
- **Requirement source:** project brief supplied for the neighbourhood recommender
- **Scope:** functional requirements FR-01–FR-11 and non-functional requirements NFR-01–NFR-09
- **Requirement detail:** FR-01–FR-11 are high-level groups; the SRS and RTM trace the detailed `REQ-4.x.x-nn` requirements.
- **Use-case model:** 17 use cases, `UC1`–`UC17`; see `Use Case Diagram and Description.pdf`
- **Evidence baseline:** backend **168 tests**, frontend **43 tests**, build passing, SLA benchmark and 18-check E2E checklist completed

---

## 1. Purpose

This document makes each requirement **verifiable** and **traceable** by recording:

1. a unique requirement ID;
2. a testable acceptance criterion;
3. the verification method;
4. the design/implementation evidence;
5. the automated or manual evidence;
6. the current status and any gap.

A requirement is only marked **Verified** when the acceptance criterion is supported by executed evidence. Requirements whose core behaviour exists but whose full wording is not demonstrated are marked **Partially verified**. Requirements with no adequate evidence are marked **Not verified**.

---

## 2. Verification methods and status

| Code | Method | Meaning |
| --- | --- | --- |
| **T** | Automated test | Unit, integration or system test with assertions. |
| **D** | Demonstration | Manual browser/API walkthrough against the running application. |
| **I** | Inspection | Review of source, configuration, UI markup or data contract. |
| **M** | Measurement | Benchmark or timing measurement. |
| **A** | Analysis | Design/change-impact or source-to-screen reconciliation. |

| Status | Meaning |
| --- | --- |
| **Verified** | Acceptance criterion is met with executed evidence. |
| **Partially verified** | Core behaviour exists, but part of the requirement is not demonstrated or is implemented through an interpretation. |
| **Not verified** | No adequate evidence yet, or a known implementation gap prevents the stated criterion. |

---

## 3. Functional requirements traceability

| ID | Requirement | Testable acceptance criterion | Verification | Implementation evidence | Test / evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| **FR-01** | Users can enter preferences: budget, workplace/CBD distance, public transport, schools, hospitals, green/recreational spaces and malls. | The form accepts budget, flat type, workplace/anchor, commute mode and importance for the five frozen criteria; green/parks, schools, healthcare, malls and MRT access influence scoring. | T, D, I | `ProfileFormUI.tsx`, `ProfileDTO`, `CriterionCatalog`, `ProfileControl`, `InputValidationControl`; public transport is represented by MRT/LRT count within `AMENITIES_DENSITY`; parks contribute to `GREEN_COVERAGE` and amenity counts. | `ProfileFormUI.test.tsx`, `test_black_box_validation.py` (BB-VAL-01–37), E2E-02/E2E-03 | **Partially verified** — public transport and recreation are not separate criteria; weather is display-only. |
| **FR-02** | Users can assign a weight/importance to each selected criterion. | Each active criterion has a 1–10 rating; ratings are normalised by the backend; invalid ratings are rejected. | T, D | `ProfileFormUI` sliders, `weights.ts`, `CriterionWeight`, `WeightedScoringStrategy`. | BB-VAL-19–22, BB-VAL-37; `test_relative_weights_are_normalised_from_one_to_ten_ratings`; E2E-02 | **Verified** |
| **FR-03** | Users see a ranking of neighbourhoods that fit their preferences. | Valid profile returns a sorted recommendation list capped at 20; ranking is deterministic. | T, D | `RankingControl`, `WeightedScoringStrategy`, `ResultsListUI`, `RecommendationSet`. | `test_ranking_control_returns_sorted_set`, `test_ranking_is_capped_at_twenty_items`, `test_insufficient_data_subzones_are_not_ranked`; E2E-03 | **Verified** |
| **FR-04** | Users can see details of a selected neighbourhood: prices, amenities, commute and other details. | An available subzone opens a factsheet containing pricing per flat type, environment, grouped amenities, commute and warnings. | T, D | `NeighborhoodDetailsControl`, `NeighborhoodDetailDTO`, `FactSheetUI`. | `test_factsheet`, `test_pdf_contains_weighting_scores_dates_and_caveats`; E2E-04 | **Verified** |
| **FR-05** | Users can modify preferences and regenerate recommendations. | Editing a saved plan persists changes and reruns ranking; reload restores the plan. | T, D | `ProfileControl`, `ProfileCatalog`, `ProfileFormUI`, `App.runRanking`, `handleSaved`. | `ProfileControl.test.ts` (create/update/delete/lifecycle); E2E-02, E2E-09, E2E-10 | **Verified** |
| **FR-06** | The system calculates estimated distance and/or travel time between workplace/CBD and neighbourhood. | Each ranked candidate receives a commute duration/distance; CBD public transport uses the matrix, other cases use live routing or a warned estimate. | T, M | `CommuteControl`, `CommuteEstimate`, `MapControl`, `getCommuteOverlay`. | `test_commute.py` (matrix/custom/live/fallback/cache), `test_extras.py` async shortlist, OneMap benchmark p95 518 ms | **Verified** |
| **FR-07** | The system calculates a 0–100 suitability score based on preferences. | Score is in `[0,100]`; fixed-domain normalisation; weights sum to 1 after renormalisation. | T, A | `WeightedScoringStrategy`, `CriterionScore`, `RecommendationItem`. | `test_scores_are_between_zero_and_hundred`, `test_fixed_domain_normalisation_is_candidate_independent`, `WB-SC-BP-01…06` | **Verified** |
| **FR-08** | The system informs users when data for a neighbourhood or criterion is unavailable. | Missing/stale/estimated data produces a warning; unavailable subzones cannot be selected or ranked; bottom notice explains insufficient data. | T, D | `DataAvailabilityWarning`, `DataAvailabilityNotifier`, `RetrievalResult`, `FactSheetUI`, `App` unavailable guard, `ResultsListUI`. | `test_missing_amenity_source_excludes_school_and_amenity_criteria`; `WB-SC-BP-04/05`; `test_commute.py` fallback tests; `test_black_box_state`; `subzones.test.ts` | **Verified** |
| **FR-09** | The system notifies users when inputs are invalid. | Invalid name, budget, flat type, address, rating, minimum, or commute mode returns field-level validation errors or parse rejection; UI blocks save. | T, D | `InputValidationControl`, `ProfileDTO` parsing, `ProfileValidationError`, `NotificationModalUI`, `ProfileFormUI`. | 37-method/68-case black-box suite; `test_invalid_profile_returns_validation_error`; E2E-12 | **Verified** |
| **FR-10** | The system accesses data.gov.sg and OneMap for housing, amenities and transport. | Adapters retrieve metadata/downloads/real-time data and OneMap search/routing/themes; failures fall back safely. | T, M, I | `DataGovSgAdapter`, `OneMapApiAdapter`, `OneMapTokenManager`, `DatasetService`, `LiveEnvironmentProvider`. | `test_adapters.py`, `test_token_manager.py`, `test_dataset_service.py`; payload shapes documented in `EXTERNAL_API_DATA.md` | **Verified** |
| **FR-11** | The system generates a PDF report explaining which neighbourhood meets requirements and why. | PDF contains profile weights, ranked items, criterion scores, data dates and caveats; download metadata expires safely. | T, D | `ReportControl`, `ReportStore`, `PdfReport`, `ExportReportUI`. | `test_report.py`, `test_report_generation`, E2E-08 | **Verified** |

---

## 4. Non-functional requirements traceability

| ID | Requirement | Testable acceptance criterion | Verification | Implementation evidence | Test / evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| **NFR-01** | Usability: simple and easy for first-time users. | A first-time user can create a plan, rank, open a factsheet, compare, export and reload without training; controls have labels and clear errors. | D, I | Responsive layout, labelled form, modal help text, notifications. | Acceptance walkthrough 18/18 checks; `ProfileFormUI.test.tsx`, `ProfileSelectorUI.test.tsx` | **Partially verified** — walkthrough passed, but no formal usability study or participant metrics. |
| **NFR-02** | Performance: ranking within 5 s; OneMap commute within 10 s. | Cold ranking p95 <5 s and OneMap commute p95 <10 s on the benchmark environment. | M | `scripts/benchmark_api.py`, TTL cache/hybrid shortlist. | Cold ranking p95 **2.27 s**; warm p95 **0.28 s**; OneMap cold p95 **0.518 s**; all HTTP 200 | **Verified** for the recorded single-client localhost environment. |
| **NFR-03** | Accuracy: scores, travel distance and prices correspond with source data. | Formula outputs match spec; source snapshots are used; known proxies are labelled; warnings appear for missing data. | T, A | `SPECIFICATIONS_AND_ARCHITECTURE.md`, scoring tests, HDB pricing tests, commute tests, town-proxy labels, source snapshots. | `test_scoring_ranking.py`, `test_house_pricing.py`, `test_commute.py`, `test_amenities_environment.py` | **Partially verified** — formulas and fixtures are tested, but no independent reconciliation against a second source/ground truth. |
| **NFR-04** | Reliability: 99% availability excluding maintenance; consistent results. | Uptime is monitored over time; repeated identical requests produce the same recommendation output. | T, M | Deterministic scoring, cache, health/ready endpoints; no production deployment or uptime monitor. | `test_health_ready_and_criteria`, deterministic ranking tests; no uptime measurement | **Not verified** — no production deployment, monitoring or 99% uptime evidence. |
| **NFR-05** | Data freshness: neighbourhood information updated within 24 hours when new data is available. | Startup refreshes stale subzone/HDB snapshots when older than `DATA_MAX_AGE_HOURS`; status exposes freshness. | T, M, I | `DatasetService.refreshIfStale`, `DATA_MAX_AGE_HOURS=24`, `/api/v1/data/status`, `POST /data/refresh`. | `test_dataset_service.py`, `test_data_status_for_frontend_cache`; benchmark used local snapshots | **Partially verified** — subzone/HDB refresh is automatic; amenities rebuild from the local snapshot and source re-download is manual (`make amenities`). |
| **NFR-06** | Privacy: collect only information necessary for recommendations. | No account or server-side profile store; plans are in browser IndexedDB; only necessary query data is sent to external APIs. | I | `ProfileCatalog` (IndexedDB), stateless backend, no account system. | Code inspection; no server database; `.env` is ignored | **Verified by design/inspection** — OneMap receives the address query needed for geocoding. |
| **NFR-07** | Scalability: support increasing users and neighbourhood datasets concurrently. | Load test demonstrates acceptable latency under increasing concurrency; shared report storage is available for multi-worker deployment. | A, M | In-memory registry/cache, single-process `ReportStore`, no load test or shared storage. | No concurrency benchmark; `LIMITATIONS.md` production gaps | **Not verified** — no load/stress test; report store is single-process. |
| **NFR-08** | Maintainability: datasets and recommendation algorithms easy to update. | Layer boundaries and strategy/adapters allow change with low coupling; tests/docs cover change areas. | A, I | ECB packages, `ScoringStrategy`, adapters, `FILE_REFERENCE.md`, `BACKEND_CLASS_REFERENCE.md`, `FRONTEND_CLASS_REFERENCE.md`, test suites. | Code review; `test_scoring_ranking.py`; `test_adapters.py`; documentation | **Partially verified** — architecture is modular, but no formal change-cost metric. |
| **NFR-09** | Accessibility: usable across common devices and different technical levels. | Responsive layout works on mobile width; interactive controls have accessible names; screen-reader/keyboard audit completed. | D, I | Responsive CSS, labels, ARIA roles, keyboard handlers, E2E 390 px check. | E2E-18; `ProfileFormUI.test.tsx`, `ProfileSelectorUI.test.tsx`; no screen-reader audit | **Partially verified** — responsive/label evidence exists; formal accessibility audit is outstanding. |

---

## 5. Requirement-to-design traceability

| Requirement group | Design classes/components |
| --- | --- |
| Preferences and validation | `ProfileFormUI`, `ProfileDTO`, `InputValidationControl`, `ProfileControl`, `CriterionCatalog` |
| Weighting and scoring | `CriterionWeight`, `WeightedScoringStrategy`, `CriterionScore` |
| Ranking | `RankingControl`, `RecommendationSet`, `RecommendationItem`, `ResultsListUI` |
| Commute and map | `CommuteControl`, `MapControl`, `NeighborhoodMapUI`, `RouteData` |
| Factsheet and comparison | `NeighborhoodDetailsControl`, `NeighborhoodDetailDTO`, `FactSheetUI`, `ComparisonUI` |
| Warnings and unavailable data | `DataAvailabilityWarning`, `DataAvailabilityNotifier`, `Subzone.dataAvailable`, `ResultsListUI`, App bottom notice |
| API/data access | `DataGovSgAdapter`, `OneMapApiAdapter`, `DatasetService`, `LiveEnvironmentProvider` |
| Report and share | `ReportControl`, `ReportStore`, `PdfReport`, `ExportReportUI` |
| Persistence/cache | `ProfileCatalog`, `ApiCache`, `ProfileControl` |

Full class/method references:

- `BACKEND_CLASS_REFERENCE.md`
- `FRONTEND_CLASS_REFERENCE.md`
- `FILE_REFERENCE.md`

## 5a. Use-case traceability (17-use-case model)

The current model has 17 use cases (`UC1`–`UC17`) and is defined in
the use case diagram (`docs/diagrams/use-case-diagram.png`). Refresh data is
a supporting system action (`FR-10`, `NFR-05`), not a separately named use case.

| Use case | Actor goal | Main flow | Requirements | Implementation | Evidence |
| --- | --- | --- | --- | --- | --- |
| **UC1 Create Preference Profile** | User creates a plan. | Open form → enter budget/flat types/workplace/weights → validate → geocode → save active plan. | FR-01, FR-02, FR-05, FR-09 | `ProfileFormUI`, `ProfileControl`, `ProfileCatalog`, `InputValidationControl` | `ProfileFormUI.test.tsx`, `ProfileControl.test.ts`, E2E-02 |
| **UC2 Edit Preference Profile** | User changes a saved plan. | Open saved plan → update fields/weights → validate → re-geocode if needed → persist. | FR-01, FR-02, FR-05, FR-09 | `ProfileFormUI`, `ProfileControl`, `ProfileCatalog` | `ProfileFormUI.test.tsx`, `ProfileControl.test.ts`, E2E-02 |
| **UC3 Delete Preference Profile** | User removes an unused plan. | Select plan → confirm delete → remove from IndexedDB → activate replacement if needed. | FR-05, NFR-06 | `ProfileSelectorUI`, `ProfileControl`, `ProfileCatalog` | `ProfileControl.test.ts`, `ProfileSelectorUI.test.tsx`, E2E-10 |
| **UC4 Notify Invalid Inputs** | User gets actionable correction. | Submit invalid form → field errors shown inline → save blocked until fixed. | FR-09 | `InputValidationControl`, `ProfileFormUI`, `NotificationModalUI` | BB-VAL-01…37, `ProfileFormUI.test.tsx` |
| **UC5 Set Criteria Weights** | User sets criterion importance. | Move 1–10 sliders → weights normalised to 100% → saved with plan. | FR-02, FR-09 | `ProfileFormUI`, `src/utils/weights.ts` | `weights.test.ts`, `ProfileFormUI.test.tsx` |
| **UC6 Select Preference Profile** | User switches the active plan. | Choose plan from selector → active flag persisted → ranking reloads. | FR-05 | `ProfileSelectorUI`, `ProfileControl`, `ProfileCatalog` | `ProfileControl.test.ts` (active-plan reload), `ProfileSelectorUI.test.tsx` |
| **UC7 Calculate Score** | System scores each candidate. | Load weights/data → normalise criteria → compute weighted total → mark partial data. | FR-03, FR-07, FR-08 | `WeightedScoringStrategy`, `CriterionScore`, `RecommendationItem` | `test_scoring_ranking.py`, WB-SC-BP-01…06 |
| **UC8 Generate Ranked Recommendations** | User sees best neighbourhoods. | Score candidates → sort → limit → retain warnings → show ranked list/map. | FR-03, FR-07, FR-08 | `RankingControl`, `ResultsListUI`, `NeighborhoodMapUI` | `test_scoring_ranking.py`, `test_api_handlers.py`, E2E-03 |
| **UC9 View Neighborhood Details** | User inspects one neighbourhood. | Select available subzone → open factsheet → show pricing, amenities, environment and commute. | FR-04, FR-08 | `FactSheetUI`, `NeighborhoodDetailsControl` | `test_factsheet`, `test_amenities_environment.py`, E2E-04 |
| **UC10 Generate Map** | System renders the interactive map. | Load OneMap tiles/boundaries → highlight subzone → overlay commute route. | FR-04, FR-06 | `NeighborhoodMapUI`, `MapControl` | map/route tests, E2E-03 |
| **UC11 Retrieve Commute Distance and Time** | System obtains route metrics. | Call OneMap routing → extract duration/distance/transfers → fall back to estimate on failure. | FR-06, FR-08 | `CommuteControl`, `OneMapApiAdapter` | `test_commute.py`, `test_adapters.py` |
| **UC12 Retrieve Environment Info** | System loads environmental data. | Fetch green coverage, PM2.5, UVI and weather → attach source/as-of metadata. | FR-04, FR-07 | `EnvironmentRetrievalControl`, `DataGovSgAdapter` | `test_amenities_environment.py` |
| **UC13 Retrieve Amenity Info** | System loads nearby amenities. | Fetch schools, malls, hospitals and MRT data → group by category and distance. | FR-04, FR-07 | `AmenityRetrievalControl`, `DataGovSgAdapter` | `test_amenities_environment.py` |
| **UC14 Retrieve House Pricing** | System loads resale pricing. | Resolve HDB town → compute median price/$psm/trend → label town proxy. | FR-04, FR-07 | `HousePricingRetrievalControl`, `TownMapping` | `test_house_pricing.py` |
| **UC15 Generate PDF Report** | User exports a report. | Select areas → generate PDF with scores/weights/caveats → download → show success notice. | FR-04, FR-11 | `ExportReportUI`, `ReportControl`, `ReportStore` | `test_report.py`, `ExportReportUI.test.tsx`, E2E-08 |
| **UC16 Notify Data Unavailable** | User is not shown misleading data. | Missing/stale/partial data → persistent notice/fallback text → rest of view still renders. | FR-08 | `DataAvailabilityNotifier`, `ResultsListUI`, `App` guard | WB-RR-08, `subzones.test.ts`, acceptance walkthrough |
| **UC17 Compare Neighborhoods** | User compares 2–4 areas. | Select 2–4 available areas → build matrix → mark best → close and retain selection. | FR-03, FR-04, FR-08 | `ComparisonUI`, `ComparisonControl` | comparison tests in `test_api_handlers.py`, acceptance walkthrough |

---

## 6. Verification status summary

| Status | Functional | Non-functional | Total |
| --- | ---: | ---: | ---: |
| Verified | 10 | 2 | **12** |
| Partially verified | 1 | 5 | **6** |
| Not verified | 0 | 2 | **2** |
| **Total** | **11** | **9** | **20** |

### Requirement-level open gaps

1. **FR-01 interpretation:** public transport and recreation are represented inside amenity/green criteria rather than separate weighted criteria. If the brief requires them separately, add dedicated criteria and form sliders.
2. **NFR-01 usability:** need a task-based usability study or participant feedback.
3. **NFR-03 accuracy:** need independent reconciliation against source datasets or a second implementation.
4. **NFR-04 reliability:** need production deployment, uptime monitoring and an availability record.
5. **NFR-05 freshness:** decide whether amenity source re-download must also be automatic; currently rebuild uses the local snapshot.
6. **NFR-07 scalability:** need concurrency/load tests and shared report storage before multi-worker deployment.
7. **NFR-08 maintainability:** architecture supports change, but no objective measurement or change-cost record.
8. **NFR-09 accessibility:** complete keyboard/screen-reader audit and physical-device checks.

---

## 7. How to reproduce the evidence

### Automated tests

```powershell
make test
make test-frontend
```

Current verified result:

```text
Backend: 168 tests OK
Frontend: 43 tests OK
```

### Build

```powershell
make build
```

### Performance

```powershell
make benchmark
```

See the benchmark results summarised in NFR-02 above. The script writes fresh
results when re-run.

### Manual E2E/acceptance

Run the current use cases UC1–UC17 against the running app:

```powershell
make dev
```

Open <http://localhost:5173>.

### Acceptance walkthrough summary

The recorded browser/API walkthrough passed **18/18 checks**: initial load,
plan creation with hard minima/address search, ranked results, factsheet,
map selection/nearby amenities, comparison and four-item limit, PDF/share,
share import, reload persistence, delete confirmation/guard, invalid form,
address failure, refresh, simulated API outage, health endpoints, report expiry
and 390 px responsive layout.

---

## 8. Related evidence documents

- `SPECIFICATIONS_AND_ARCHITECTURE.md` — frozen rules, architecture and API contract.
- `BLACK_BOX_TESTING.md` — EP/BVA/state testing and detailed expected/actual matrix.
- `WHITE_BOX_TESTING.md` — basis paths, data flow and coverage.
- `LIMITATIONS.md` — current data, functional and production limitations.
- `EXTERNAL_API_DATA.md` — external payload shapes and transformations.
- `BACKEND_CLASS_REFERENCE.md` and `FRONTEND_CLASS_REFERENCE.md` — class/method traceability.
- `FILE_REFERENCE.md` — file/folder responsibilities.
