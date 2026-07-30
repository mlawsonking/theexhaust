# Hospital/Care Distress — index workbook (v1)

**Status: FROZEN.** Every constant on this page is committed *before* the runner exists and before
any staffing value is compared to any citation. `retrocast/hospital_care/spec.py` holds these same
constants in code and `retrocast/tests/test_hospital_care_freeze.py` fails the suite if the two ever
disagree. Changing a number here after results are seen is a **v2 pre-registration**, not an edit.

Companion documents: [PRE-REGISTRATION-v1.md](../../retrocast/hospital-care/PRE-REGISTRATION-v1.md)
(the design and the pass/fail bars) · [prior-art-scan.md](../../retrocast/hospital-care/prior-art-scan.md)
(this join is not novel and the registration says so).

---

## 1. Corpora — archived vintages only

Both sides are read from **hash-pinned objects in the R2 archive**, never from a live endpoint
(constitution: government-continuity / stale-data posture). The runner imports no HTTP client.

| Side | Collector | Unit archived |
|---|---|---|
| Signal | `cms-pbj` | one CSV **per quarter**, retained by CMS, archived under `raw/cms-pbj/<QUARTER>/…` |
| Ground truth | `cms-deficiencies` | one CSV that CMS **overwrites in place**, archived per collection day |

## 2. The join key

`PROVNUM` (PBJ) == `CMS Certification Number (CCN)` (deficiencies). Both are 6-character strings,
zero-padded, compared **as strings** — never as integers, which would destroy the leading zero that
encodes the state. Measured overlap, 2026Q1 PBJ against the archived deficiency vintage:

| | count |
|---|---|
| PBJ CCNs | 14,487 |
| Deficiency CCNs | 14,632 |
| Intersection | **14,431 (99.6% of PBJ)** |
| PBJ-only | 56 |
| Deficiency-only | 201 |

No semantic matching, no LLM, no fuzzy join anywhere in this index.

## 3. CCN identity, reuse and closure (frozen handling)

The hazard named in the work order is that a CCN can be retired or reassigned. Measured across the
seven consecutive archived quarter-transitions 2024Q2→2026Q1:

| transition | shared | dropped | new | PROVNAME changed | STATE changed |
|---|---|---|---|---|---|
| 2024Q2→Q3 | 14,419 | 145 | 129 | 198 | **0** |
| 2024Q3→Q4 | 14,453 | 95 | 120 | 182 | **0** |
| 2024Q4→2025Q1 | 14,461 | 112 | 90 | 192 | **0** |
| 2025Q1→Q2 | 14,445 | 106 | 92 | 424 | **0** |
| 2025Q2→Q3 | 14,409 | 128 | 78 | 352 | **0** |
| 2025Q3→Q4 | 14,253 | 234 | 109 | 370 | **0** |
| 2025Q4→2026Q1 | 14,260 | 102 | 227 | 343 | **0** |

**Frozen rules, and the counts that force them:**

- **R1 — A PROVNAME change does not break the cell.** 182–424 CCNs per quarter change provider
  name (1.3–2.9%), which is ordinary ownership and rebranding churn in this sector. **STATE changed
  for 0 CCNs in 7 of 7 transitions**, which is the observable tell for geographic reassignment; its
  complete absence over the study window is why a name change is treated as the same facility, as
  CMS's own Five-Star system does. A **sensitivity re-run excluding every facility with a PROVNAME
  change inside the study window is mandatory** and its metrics are published beside the headline.
- **R2 — A STATE change breaks the cell.** If a CCN's STATE ever differs between two quarters used
  by a cell, that CCN is dropped from the run entirely and counted in the report. Expected count is
  zero; if it is not zero, the assumption behind R1 has failed and that must be visible.
- **R3 — Closure is censoring, not a negative.** A cell is scored only if its facility appears in
  the PBJ release covering the **end** of its label horizon. A facility that stops reporting cannot
  be surveyed, so counting its silence as "no harm found" would manufacture true negatives. The
  dropped-cell count is published.

## 4. Harm — the label definition (frozen)

CMS scope/severity letters. **Harm** is the label; **immediate jeopardy** is reported separately as
a severity check, never as a second bar.

    HARM_SEVERITY        = {"G", "H", "I", "J", "K", "L"}   # actual harm + immediate jeopardy
    IMMEDIATE_JEOPARDY   = {"J", "K", "L"}                  # reported, not graded

A **survey event** is a distinct `(CCN, Survey Date)` pair — *not* a CSV row. The archived vintage
holds 418,479 rows but only **90,760 distinct survey events**; grading rows would count a single
inspection up to dozens of times. (This is the W-006 lesson applied before the first run, not after.)

A survey event is **positive** iff any of its rows carries a scope/severity code in `HARM_SEVERITY`.

## 5. Ground-truth coverage — what history actually exists (measured 2026-07-29)

The archived vintage is `NH_HealthCitations_Jun2026.csv`, one Processing Date (2026-06-01), survey
dates spanning **2017-03-23 → 2026-05-20**. That span is *not* usable history. CMS retains roughly
the **three most recent inspection cycles per facility**, so the file is censored at both ends, and
the left censoring is **not random**.

**Left censoring.** Distinct cited survey events per year, and mean surveys per cited facility:

| year | cited surveys | with harm (G+) | harm share | surveys/facility |
|---|---|---|---|---|
| 2017 | 40 | 3 | 0.075 | 1.00 |
| 2018 | 495 | 39 | 0.079 | 1.01 |
| 2019 | 2,009 | 201 | 0.100 | 1.00 |
| 2020 | 733 | 72 | 0.098 | 1.00 |
| 2021 | 2,028 | 236 | 0.116 | 1.00 |
| 2022 | 4,180 | 626 | 0.150 | 1.00 |
| 2023 | 18,541 | 3,374 | 0.182 | 1.72 |
| 2024 | 27,898 | 5,387 | 0.193 | 2.29 |
| 2025 | 26,059 | 5,031 | 0.193 | 2.18 |
| 2026 (to 05-20) | 8,777 | 1,459 | 0.166 | 1.37 |

Before 2023 the file holds ~1 survey per facility per year across a small minority of facilities —
the residue of the three-cycle window, not the survey record. **A frequently-surveyed facility has a
*shorter* observed history**, because three cycles cover less calendar time; frequently-surveyed
facilities are also the troubled ones. Using pre-2024 labels would therefore under-label exactly the
facilities the index is about, and would have manufactured a failure for a reason that has nothing to
do with staffing.

Share of the 14,632 CCNs already inside their own observed window:

| as of | covered |
|---|---|
| 2022-01-01 | 29.8% |
| 2023-01-01 | 49.5% |
| 2023-07-01 | 72.3% |
| **2024-01-01** | **92.4%** |
| 2024-07-01 | 97.4% |
| 2025-01-01 | 98.8% |

**Right censoring.** Distinct cited surveys per survey-month, most recent: 2026-01 → 2,185 ·
2026-02 → 2,070 · 2026-03 → 2,352 · 2026-04 → 2,120 · **2026-05 → 50**. The normal band is
~2,000–2,600/month, so **2026-05 is 2% reported** and April is close to but not certainly complete.
Observed survey→processing lag rises to a p90 of 116 days for surveys three months before the cut.

**Frozen consequence — the label window is `2024-01-01 .. 2026-03-31`.** The start is where global
facility coverage reaches 92.4%; the end drops the visibly truncated month and the one before it.
Two survey months that look anomalous inside the window (2025-10 → 848, 2025-11 → 1,852) are kept:
they coincide with the federal appropriations lapse the constitution already tracks, and are a real
depression of survey activity rather than a reporting artifact. This is noted in the report.

**Per-facility left truncation (in addition to the global window).** A cell is scored only if its
facility's **earliest observed citation is at least 182 days before the cell's week start**, so that
every facility scored has a real (if short) observed history behind its prior-harm features. Cells
failing this are dropped and counted.

## 6. Signal — PBJ features (frozen)

PBJ columns, verified against the archived 2026Q1 bytes (33 columns). Nursing-hour columns used:

    NURSE_HOURS = ["Hrs_RNDON", "Hrs_RNadmin", "Hrs_RN",
                   "Hrs_LPNadmin", "Hrs_LPN",
                   "Hrs_CNA", "Hrs_NAtrn", "Hrs_MedAide"]
    RN_HOURS    = ["Hrs_RNDON", "Hrs_RNadmin", "Hrs_RN"]
    CONTRACT    = every "<col>_ctr" companion of the above

Per `(CCN, quarter)`, aggregated over the quarter's daily rows (**sum of numerators over sum of
denominators**, so a single zero-census day cannot divide by zero or dominate):

| # | feature | definition |
|---|---|---|
| 1 | `hprd_total` | Σ all nursing hours ÷ Σ `MDScensus` |
| 2 | `hprd_rn` | Σ RN hours ÷ Σ `MDScensus` |
| 3 | `rn_share` | `hprd_rn / hprd_total` (0 if `hprd_total` = 0) |
| 4 | `contract_frac` | Σ contractor hours ÷ Σ all nursing hours |
| 5 | `weekend_gap` | `1 − (mean Sat/Sun daily HPRD ÷ mean Mon–Fri daily HPRD)` |
| 6 | `hprd_cv` | stdev ÷ mean of the quarter's daily HPRD series |
| 7 | `hprd_trend` | `hprd_total(Q) ÷ mean(hprd_total over Q−1…Q−4) − 1` |
| 8 | `low_days_frac` | share of the quarter's days with daily HPRD < **3.48** |
| 9 | `census` | mean `MDScensus` (size control) |

**3.48 is not a tuned number.** It is the total nurse-staffing minimum in the CMS 2024 minimum
staffing final rule (0.55 RN + 2.45 nurse aide + 0.48 flexible). An externally fixed regulatory
threshold is used precisely so that no threshold in this index was chosen by us against this data.

**Quarter admissibility.** A `(CCN, quarter)` is usable only with **≥60 reported days** and
`Σ MDScensus > 0`. Features 5–8 additionally require both weekend and weekday days present. A cell
whose feature quarter is inadmissible is dropped and counted. `hprd_trend` requires all four prior
quarters admissible; where they are not, the cell is dropped rather than imputed.

## 7. As-known-then: the publication-lag rule (frozen)

PBJ is published on a lag. Observed on the archive: 2026Q1 (ends 2026-03-31) carried
`Last-Modified: Tue, 30 Jun 2026` = **91 days**; 2025Q4 (ends 2025-12-31) carried
`Thu, 16 Apr 2026` = **106 days**.

    PBJ_AVAILABILITY_LAG_DAYS = 135

Quarter `Q`'s features may be used only for weeks beginning on or after `Q_end + 135 days`. The
margin over the observed 91–106 days is deliberate. **Without this rule the retrocast would assume
knowledge roughly three months before it was public**, and any lead-time claim would be a fiction.
This is the leak control that has no NHTSA analogue — complaints publish daily; PBJ does not.

## 8. Time base (frozen)

    WEEK_EPOCH = 2017-01-02   (a Monday)
    week(d)    = (d − WEEK_EPOCH).days // 7      # week w spans [EPOCH+7w, EPOCH+7w+6]
    HORIZON_WEEKS = 26

## 9. Splits (frozen) — the horizon-spillover guard is exact

| split | cell weeks (by week-start date) | weeks |
|---|---|---|
| **Train** | 2023-12-25 … 2024-09-23 | 40 |
| **Gap (unscored)** | 2024-09-30 … 2025-03-17 | 25 |
| **Test (held out)** | 2025-03-24 … 2025-09-22 | 27 |

The last train cell's horizon ends 2025-03-30; the first test cell's horizon begins 2025-03-31.
**The two horizons do not overlap by a single day** — the guard is arithmetic, not approximate.

PBJ quarters required end-to-end: **2022Q2 … 2025Q1** (features, including the four-quarter trend
baseline). Every one is read from the archive.

## 10. What was inspected before this workbook was frozen

Recorded so a hostile reviewer can check the boundary rather than take it on trust. Examined:
the deficiency file's **column list, row/event counts, survey-date span, per-year and per-month
event counts, harm shares, inspection-cycle spans, processing lag, per-facility earliest-citation
distribution**; the PBJ **column list, per-quarter PROVNUM counts, name/state churn, and CCN overlap**.

**Not examined, and not examinable until this and the pre-registration are committed and pushed:**
any relationship between a staffing value and a citation outcome. No model was fit, no feature
correlated with any label, no threshold evaluated. The per-year harm shares in §5 are label-side
marginals and are the reason the precision bar in the registration is set *above* the base rate
rather than at it — the specific way the NHTSA v1 precision bar turned out vacuous.
