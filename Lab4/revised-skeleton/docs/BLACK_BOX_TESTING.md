# Formal Black-Box Testing — Profile Validation

- **Version:** 1.0
- **Date:** 24 October 2026
- **System under test:** SG Property Finder profile-validation boundary
- **Test suite:** `backend/tests/test_black_box_validation.py`
- **Execution:** `python -m unittest tests.test_black_box_validation -v`
- **Result:** **37 test methods / 68 logical cases — all passed**

---

## 1. Objective

Verify that profile payloads are accepted or rejected correctly before a plan
can be saved or ranked. The suite covers equivalence-class partitioning (EP),
boundary-value analysis (BVA), expected/actual recording, and test
minimisation.

## 2. System under test and boundary

The tests submit JSON-style profile payloads through:

```python
handlers.validateProfile(payload, context)
```

This is the same validation path used by:

```text
POST /api/v1/profiles/validate
```

The handler:

1. parses the payload into `ProfileDTO` via `profileDtoFromDict`;
2. calls `InputValidationControl.validateProfileData`;
3. returns an `ApiEnvelope`.

The tests inspect only the returned envelope and field-level messages. They do
not call validator internals.

Two rejection mechanisms exist and are tested separately:

| Mechanism | Envelope | Meaning |
| --- | --- | --- |
| Parse rejection | `success=false`, `error.code=INVALID_PROFILE` | Payload shape, type, enum or coercion failure |
| Validation rejection | `success=true`, `data.isValid=false` | Structurally parseable payload violates a business rule |

## 3. Test environment and data

| Item | Value |
| --- | --- |
| Language/runtime | Python 3.13 |
| Test framework | `unittest` |
| Baseline payload | `tests.support.profilePayload()` |
| Address adapter | `tests.support.FakeOneMap` |
| Outage adapter | Local `ExplodingOneMap` stub |
| External network | None |
| Address data | Simulated match, no match and adapter exception |
| Ranking/scoring | Not exercised by this suite |

The baseline payload is a valid plan with a `Raffles Place` workplace, anchor
coordinates, five 1–10 criterion ratings and all hard minimums set to zero.

## 4. Techniques

### 4.1 Equivalence-class partitioning

Each input domain was divided into valid and invalid classes. One representative
value per class was submitted while the rest of the payload stayed valid.

### 4.2 Boundary-value analysis

For numeric and range-based rules, values immediately below, at and above each
boundary were tested:

- `-1 / 0 / 1`
- `49 / 50 / 51`
- weights `0 / 1 / 10 / 11`
- budget bounds at `0`, equal values and `minimum + 1`

### 4.3 Expected/actual recording

Every case records the expected result and the observed result. The detailed
matrix is in section 7.

### 4.4 Test minimisation

- One baseline valid payload avoids repeating unrelated valid fields.
- One-factor-at-a-time variation isolates each rule.
- The five hard-minimum fields are covered with `subTest` loops rather than 25
  near-identical methods.
- No full cross-product was used because validation rules are independent and
  the pairwise interactions are not specified.

## 5. Equivalence classes

| Input domain | Valid class | Invalid classes | Test IDs |
| --- | --- | --- | --- |
| `profileName` | Non-empty, non-whitespace string | Empty string; whitespace-only | BB-VAL-01, 02, 03 |
| `budgetMin` | `>= 0` | `< 0` | BB-VAL-04, 23, 33 |
| `budgetMax` | `> 0` and `> budgetMin` | Zero; equal to `budgetMin`; below `budgetMin` | BB-VAL-05, 06, 24, 34 |
| `selectedFlatTypes` | At least one supported flat type | Empty list | BB-VAL-07, 17, 18 |
| Workplace/anchor | Address resolvable or anchor supplied | Neither supplied; address not found; address lookup error | BB-VAL-08, 09, 10, 11, 12 |
| `criteriaWeights` | At least one known criterion, rating in `[1, 10]` | Empty list; unknown criterion; rating `< 1`; rating `> 10` | BB-VAL-13, 14, 19, 20, 21, 22, 35, 37 |
| `preferredCommuteMode` | `PUBLIC_TRANSIT`, `DRIVING`, `WALKING`, or omitted | Unparseable value such as `CYCLING` | BB-VAL-15, 16, 36 |
| Hard minimum counts | Whole number in `[0, 50]` | Negative; non-integer; boolean; `> 50` | BB-VAL-25 to 32 |

## 6. Boundary values

| Variable | Below boundary | At boundary | Above boundary | Test IDs |
| --- | --- | --- | --- | --- |
| `budgetMin` | `-1` → invalid | `0` → valid; `1` → valid | — | BB-VAL-04, 23, 33 |
| `budgetMax` with `budgetMin=500000` | `0` → invalid | `500000` → invalid (equal) | `500001` → valid | BB-VAL-05, 06, 24 |
| `budgetMax` with `budgetMin=0` | — | `1` → valid | — | BB-VAL-34 |
| Importance rating | `0` → invalid | `1` and `10` → valid | `11` → invalid | BB-VAL-19, 20, 21, 22 |
| Minimum count | `-1` → parse-invalid | `0`, `1`, `49`, `50` → valid | `51` → validation-invalid | BB-VAL-25, 26, 27, 28, 32 |
| Minimum value type | `1.5`, `true`, `-1` → parse-invalid | Integer `0` → valid | Numeric string `"5"` → valid | BB-VAL-28, 29, 30, 31 |
| Flat types | `0` → invalid | `1` → valid | `3` → valid | BB-VAL-07, 17 |
| Criteria list | `0` → invalid | `1` → valid | `5` → valid; unknown ID → invalid | BB-VAL-13, 14, 35 |
| Commute mode | Omitted → defaults to `PUBLIC_TRANSIT` | All three modes → valid | `CYCLING` → parse-invalid | BB-VAL-15, 16, 36 |

## 7. Expected/actual matrix

| ID | Test case | Input | Expected | Actual | Status |
| --- | --- | --- | --- | --- | --- |
| BB-VAL-01 | Baseline valid profile | Valid payload | Accepted, no errors | Accepted, no errors | Pass |
| BB-VAL-02 | Empty profile name | `profileName=""` | Rejected: `Enter a profile name.` on `profileName` | Same | Pass |
| BB-VAL-03 | Whitespace profile name | `profileName="   "` | Rejected: `Enter a profile name.` | Same | Pass |
| BB-VAL-04 | Negative budget minimum | `budgetMin=-1` | Rejected: `Budget minimum cannot be negative.` | Same | Pass |
| BB-VAL-05 | Zero budget maximum | `budgetMax=0` | Rejected: `Budget maximum must be greater than zero.` | Same | Pass |
| BB-VAL-06 | Equal budget bounds | `budgetMin=budgetMax=500000` | Rejected: `Budget maximum must be greater than the minimum.` | Same | Pass |
| BB-VAL-07 | Empty flat-type list | `selectedFlatTypes=[]` | Rejected: `Select at least one flat type to continue.` | Same | Pass |
| BB-VAL-08 | No workplace and no anchor | Both set to `null` | Rejected: `Enter a workplace address or select a map anchor.` | Same | Pass |
| BB-VAL-09 | Anchor only | `workplaceAddress=null` | Accepted | Accepted | Pass |
| BB-VAL-10 | Address only | `anchorCoordinates=null` | Accepted when address resolves | Accepted | Pass |
| BB-VAL-11 | Unresolvable address | Fake adapter returns no matches | Rejected: `Address not Found. Enter a valid postal code or building name.` | Same | Pass |
| BB-VAL-12 | Address lookup outage | Adapter raises exception | Rejected: `Unable to verify the address. Try again.` | Same | Pass |
| BB-VAL-13 | Empty criteria list | `criteriaWeights=[]` | Rejected: `Rate at least one criterion.` | Same | Pass |
| BB-VAL-14 | Unknown criterion | `criterionId="NOT_A_CRITERION"` | Rejected: `Unknown criterion: NOT_A_CRITERION.` | Same | Pass |
| BB-VAL-15 | Missing commute mode | Field removed | Accepted; defaults to `PUBLIC_TRANSIT` | Accepted | Pass |
| BB-VAL-16 | Invalid commute mode | `preferredCommuteMode="CYCLING"` | Parse rejection: `INVALID_PROFILE` | Same | Pass |
| BB-VAL-17 | Multiple flat types | `3 ROOM`, `4 ROOM`, `EXECUTIVE` | Accepted | Accepted | Pass |
| BB-VAL-18 | Lowercase flat type | `"4 room"` | Accepted and normalised to uppercase | Accepted | Pass |
| BB-VAL-19 | Rating below range | Weight `0` | Rejected: `Importance for PRICE must be between 1 and 10.` | Same | Pass |
| BB-VAL-20 | Rating at lower bound | All weights `1` | Accepted | Accepted | Pass |
| BB-VAL-21 | Rating at upper bound | All weights `10` | Accepted | Accepted | Pass |
| BB-VAL-22 | Rating above range | Weight `11` | Rejected: `Importance for PRICE must be between 1 and 10.` | Same | Pass |
| BB-VAL-23 | Budget minimum at zero | `budgetMin=0` | Accepted | Accepted | Pass |
| BB-VAL-24 | Budget maximum one above minimum | `500000 / 500001` | Accepted | Accepted | Pass |
| BB-VAL-25 | All minimums at zero | All five fields `0` | Accepted | Accepted | Pass |
| BB-VAL-26 | Minimum at upper bound | Each field `50` | Accepted (5/5 fields) | 5/5 accepted | Pass |
| BB-VAL-27 | Minimum above upper bound | Each field `51` | Rejected with `<Label> minimum must be between 0 and 50.` (5/5) | 5/5 rejected as expected | Pass |
| BB-VAL-28 | Negative minimum | Each field `-1` | Parse rejection `INVALID_PROFILE` (5/5) | 5/5 parse-rejected | Pass |
| BB-VAL-29 | Non-integer minimum | Each field `1.5` | Parse rejection `INVALID_PROFILE` (5/5) | 5/5 parse-rejected | Pass |
| BB-VAL-30 | Boolean minimum | Each field `true` | Parse rejection `INVALID_PROFILE` (5/5) | 5/5 parse-rejected | Pass |
| BB-VAL-31 | Numeric-string minimum | `minimumMalls="5"` | Accepted | Accepted | Pass |
| BB-VAL-32 | Minimum interior values | Each field `1` and `49` | Accepted (10/10) | 10/10 accepted | Pass |
| BB-VAL-33 | Budget minimum at one | `budgetMin=1` | Accepted | Accepted | Pass |
| BB-VAL-34 | Budget maximum at one | `budgetMin=0`, `budgetMax=1` | Accepted | Accepted | Pass |
| BB-VAL-35 | Single criterion | One criterion weight | Accepted | Accepted | Pass |
| BB-VAL-36 | All commute modes | `PUBLIC_TRANSIT`, `DRIVING`, `WALKING` | Accepted (3/3) | 3/3 accepted | Pass |
| BB-VAL-37 | Fractional rating within range | Weight `1.5` | Accepted | Accepted | Pass |

## 8. Coverage summary

The suite exercises every branch in `InputValidationControl.validateProfileData`
and every profile-field parse branch in `profileDtoFromDict`:

- profile name presence;
- budget minimum sign;
- budget maximum positivity and ordering;
- flat-type presence and normalisation;
- workplace/anchor alternatives;
- address match success, no-match and adapter failure;
- criteria presence, known IDs and rating range;
- commute-mode parsing and defaulting;
- all five hard-minimum fields at below/at/above boundaries and invalid types.

## 9. Observations and defects

**No validation defects were found in this pass.** All 68 logical cases produced
the expected result.

Documented behaviours:

1. **Parse rejection vs validation rejection.** Negative, non-integer and
   boolean minimum counts are rejected before business validation and therefore
   return `success=false` with `INVALID_PROFILE` rather than a field-level
   `isValid=false` result. Clients must handle both forms.
2. **Numeric-string coercion.** A minimum supplied as `"5"` is accepted and
   converted to integer `5`. The UI sends numbers, so this only affects direct
   API clients.
3. **Fractional importance ratings.** A rating of `1.5` is accepted because the
   contract defines the rating as a range `[1, 10]`, not an integer. The UI
   slider still emits whole numbers.
4. **Invalid commute modes are parse errors.** `CYCLING` is not an unknown
   business rule; it fails enum parsing and returns `INVALID_PROFILE`.

## 10. Reproduction

```powershell
cd Lab4/revised-skeleton/backend
python -m unittest tests.test_black_box_validation -v
```

Observed summary:

```text
Ran 37 tests in 0.002s

OK
```

Full backend regression suite:

```powershell
cd Lab4/revised-skeleton
make test
```

Observed summary at the time of writing:

```text
Ran 136 tests
OK
```

## 11. Limitations and next steps

- This suite validates profile input, not ranking quality or scoring maths.
- HTTP transport is covered by a smoke test in `test_fastapi_endpoints.py`; this
  suite uses the transport-agnostic handler boundary for the full EP/BVA matrix.
- Live OneMap behaviour is simulated; network timing belongs to the Phase 5 SLA
  benchmark.
- White-box CFG/cyclomatic-complexity documentation remains a separate Phase 4
  deliverable.
- A future extension could add property-based/fuzz testing for malformed JSON
  shapes and very large numeric values.
