# Phase 5 — Dialog Map E2E Checklist

- **Date:** 24 October 2026
- **Application:** SG Property Finder
- **Frontend:** `http://127.0.0.1:5173`
- **Backend:** `http://127.0.0.1:8000`
- **Browser:** Desktop browser tab driven through the OpenCode browser tools
- **Test plan:** `E2E Phase 5` (created and removed during the run)
- **Existing plan preserved:** `E2E Pasir Ris`

---

## 1. Scope

This checklist covers the main user journey and the edge/error flows requested
for Phase 5:

- initial load and data status;
- plan creation with address search and hard minimums;
- ranking and result rendering;
- factsheet grouping and title casing;
- map selection and nearby amenities;
- comparison limits and matrix;
- PDF generation and share URL;
- share-link import;
- persistence after reload;
- delete confirmation and delete guard;
- invalid form and address-search failure;
- data refresh;
- API outage handling;
- health endpoints;
- report expiry;
- mobile/responsive layout.

## 2. Method

- UI flows were executed in a live browser against the running frontend and
  backend.
- Accessibility snapshots and DOM inspection were used for assertions.
- The mobile layout was checked in an iframe with a **390 × 844** viewport.
- Health/report-expiry checks were executed at the HTTP boundary.
- The API-outage check was simulated by rejecting recommendation requests in
  the browser's `fetch` wrapper, leaving the rest of the app functional.

## 3. Results summary

| ID | Check | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| E2E-01 | Initial load and data panel | App loads; 332 subzones, HDB and amenity counts shown | 332 subzones, 243,500 HDB transactions, 1,200 amenities | Pass |
| E2E-02 | Create plan with hard minimums and address | Plan saves; address resolves; ranking starts | `E2E Phase 5` saved; `PASIR RIS MRT STATION (EW1)` selected; minima all `1`; commute weight `10` | Pass |
| E2E-03 | Ranked results | Result cards render; cap respected | Results rendered; 17 cards under the hard filters; top entries were Pasir Ris/Tampines subzones | Pass |
| E2E-04 | Factsheet grouped amenities | Title-cased category sections with counts | Primary Schools 12, Secondary Schools 10, Tertiary Schools 2, Polyclinics 2, Hospitals 2, Parks 15, Malls 8, MRTs / LRTs 5 | Pass |
| E2E-05 | Map selection and amenities | Selected subzone reflected; nearby amenities shown | `Selected: TAMPINES EAST`; `Nearby amenities` section present | Pass |
| E2E-06 | Compare two subzones | Comparison matrix opens with metrics | Overall score, commute, pricing, environment, schools, hospitals, malls and MRT rows rendered; best = TAMPINES EAST | Pass |
| E2E-07 | Compare more than four | Fifth selection rejected with notification | `Comparison limit reached — Select at most four neighbourhoods.` | Pass |
| E2E-08 | PDF export | PDF generated with expiry and share URL | `SGPropFinder_Report_2015438c.pdf`, 6.9 KB, expiry shown, share URL populated | Pass |
| E2E-09 | Share URL import | Active plan restored; comparison selection filled | `E2E Phase 5` active; `Compare (2)` filled from shared codes | Pass |
| E2E-10 | Reload persistence | Saved plan and ranking survive reload | `E2E Pasir Ris` still active after reload; results rendered | Pass |
| E2E-11 | Delete confirmation and guard | Cancel keeps plan; confirm deletes; last plan protected | Cancel kept `E2E Phase 5`; confirm removed it; one-plan guard disabled delete | Pass |
| E2E-12 | Invalid form | Missing workplace blocked with message | `Search for and select a workplace address before saving.` | Pass |
| E2E-13 | Address search failure | Invalid query shows failure notification | `Address search failed — Address not Found. Enter a valid postal code or building name.` | Pass |
| E2E-14 | Data refresh | Refresh updates sources, rebuilds amenities and reranks | `Data refreshed`; source changed to `Live data.gov.sg`; 332/243,500/1,200; ranking reran | Pass |
| E2E-15 | API outage | Failure notification; no blank/crashed UI | `Ranking failed — Cannot reach the backend. Is FastAPI running on port 8000?`; previous results remained visible | Pass |
| E2E-16 | Health endpoints | Both health paths return 200 | `/health` 200; `/api/v1/health` 200 | Pass |
| E2E-17 | Report expiry | Expired/missing report returns 404 | `GET /api/v1/reports/download/does-not-exist` → 404 | Pass |
| E2E-18 | Mobile layout | Single-column layout at 390 px width | `innerWidth=390`; `matchMedia(980px)` and `matchMedia(620px)` true; `.app-grid` one column (354.7 px); header stacked | Pass |

## 4. Evidence notes

### E2E-01 — Initial load

The data panel showed:

```text
332 subzones loaded
HDB: 243,500 transactions
Amenities snapshot: 1,200 points
```

### E2E-02 — Plan creation

The address search returned OneMap matches including:

```text
PASIR RIS MRT STATION (EW1) 519634 · 65% match
```

The selected anchor was stored and the plan was saved as `E2E Phase 5`.

### E2E-03 — Ranking

With hard minima all set to `1`, the initial result set contained **17**
subzones. The top entries were Pasir Ris/Tampines subzones.

### E2E-04 — Factsheet

The factsheet `TAMPINES EAST` showed the grouped amenity headers:

```text
Primary Schools 12
Secondary Schools 10
Tertiary Schools (JC/University) 2
Polyclinics 2
Hospitals 2
Parks 15
Malls 8
MRTs / LRTs 5
```

Each group contained its associated amenity chips with distances.

### E2E-06 — Comparison

The matrix rendered:

- overall score;
- commute duration/distance;
- 4-room town-proxy pricing;
- green coverage and PM2.5;
- school, hospital, mall and MRT counts;
- best-subzone badge and summary.

### E2E-08 — PDF and share link

The export modal reported:

```text
SGPropFinder_Report_2015438c.pdf
6.9 KB · expires 24/10/2026, 11:42:42 pm
```

The share URL opened successfully in a second tab, restored the profile and
filled the comparison selection with the shared subzone codes.

### E2E-11 — Delete confirmation

The confirmation dialog read:

```text
Delete “E2E Phase 5”?
This removes the plan from this browser's IndexedDB. It cannot be undone.
```

`Cancel` preserved the plan; `Delete plan` removed it. With only one plan left,
the delete button remained disabled with the one-plan guard message.

### E2E-14 — Data refresh

The refresh completed with:

```text
Data refreshed
Subzone and HDB snapshots have been refreshed from data.gov.sg.
```

The header changed from `Data.gov.sg snapshot` to `Live data.gov.sg` and
the active `E2E Pasir Ris` ranking reran automatically with 20 result cards.

### E2E-15 — Simulated outage

`window.fetch` was temporarily wrapped to reject requests to
`/api/v1/recommendations`. The UI displayed the expected failure notification
and retained the previous result cards instead of crashing or clearing the page.

### E2E-18 — Mobile layout

The app was loaded inside a **390 × 844** iframe. The responsive breakpoint was
active and the computed layout was single-column:

```text
window.innerWidth = 390
matchMedia('(max-width: 980px)') = true
matchMedia('(max-width: 620px)') = true
.app-grid grid-template-columns = 354.667px
.app-header flex-direction = column
```

## 5. Limitations

- The browser was a desktop Chromium instance; mobile was verified by iframe
  viewport rather than a physical device or browser device emulation.
- Report expiry was verified at the API boundary; waiting 15 minutes in the UI
  was not practical.
- The API-outage test used a browser-side fetch rejection; it did not stop the
  backend process.
- OneMap is a live external dependency, so address results and routing timings
  can vary between runs.
- The temporary `E2E Phase 5` plan was deleted after the run; `E2E Pasir Ris`
  was left intact.

## 6. Sign-off

All 18 checks passed in the tested environment. Phase 5 is complete; the SLA
benchmark is in `docs/SLA_BENCHMARK.md`.
