# Hospital/Care Distress — retrocast pre-registration v1

**Index:** Hospital/Care Distress (nursing-home care fragility) — the **second** published retrocast (gameplan §6 BUILD-05).
**Status:** FROZEN. Committed and pushed **before** any result is computed and before the runner exists (SPEC-08 §2). The results commit cites this file's commit hash and the run **aborts** unless that commit is an ancestor of `HEAD`.
**Author:** Opus, Phase 4 (worker W-008) · **Date:** 2026-07-29 · **Harness:** [SPEC-08](../../ops/SPEC-08-retrocast-harness.md) · **Frozen constants:** [WORKBOOK](../../indexes/hospital-care/WORKBOOK.md).
**Framing (constitutional):** a *measurement*, never a prediction, and never causal. The claim class is: "this county's facilities showed a staffing pattern matching the pre-citation signature of N/M historical harm citations (receipts linked)" — past tense, receipts attached. Staffing→harm invites causal language; there is none here and the report is scanned for it.

> Nothing in this document has been run against the data. Its purpose is to commit the signal, the labels, the controls, the splits, and the pass/fail bars *ahead* of results. If a change is needed **after results are seen**, that is a new pre-registration (v2) and this attempt is disclosed in [DEAD-REGISTRATIONS.md](../DEAD-REGISTRATIONS.md).

---

## 0. Why this index, and what it is not

Research §5 called this the cleanest retrocast in the portfolio, and the reason is mechanical: the
signal and the ground truth are joined by a **hard key** (`PROVNUM` = CCN), so there is no semantic
matching, no entity resolution, and no LLM anywhere in the pipeline. Both sides are official, free,
bulk, and archived by us.

It is **not novel**, and this registration does not pretend otherwise. Staffing→deficiency is a
mature literature and CMS already publishes star ratings from these two datasets; see
[prior-art-scan.md](prior-art-scan.md). Two of that scan's findings are binding constraints below:
staffing *level* is already a published CMS rating and is therefore a **baseline, not a result**
(§6), and the literature is overwhelmingly cross-sectional, so the only thing worth grading is
whether the signature beats **the facility's own citation history** (§6).

## 1. Data — retrocast-of-record only

Archived, hash-pinned R2 objects, never live endpoints. `scorecard.json` records every object key
and sha256 used. The runner imports no HTTP client, so this is enforced by construction rather than
by discipline.

- **Signal — CMS Payroll-Based Journal Daily Nurse Staffing**, quarters **2022Q2 … 2025Q1**, one archived release per quarter (`raw/cms-pbj/<QUARTER>/…`). 33 columns; daily rows per CCN.
- **Ground truth — CMS Nursing Home Health Deficiencies** (`r5ix-sfxw`), the archived vintage `NH_HealthCitations_Jun2026.csv` (Processing Date 2026-06-01; 418,479 rows; 90,760 distinct survey events; 14,632 CCNs).

**A disclosed weakness, stated before results:** the ground truth is **one** archived vintage. CMS
overwrites this file in place, and The Exhaust only began snapshotting it on 2026-07-28, so there is
no second vintage to check revisions against. Every consequence of that — the three-cycle censoring
in §3, the inability to audit label revision — is a limitation of v1 that **the archive itself
fixes over time**: each vintage collected from now on preserves label history that CMS will later
drop out of its retention window. A v2 run in a year will have history that exists nowhere else.

## 2. Unit of analysis

A **(CCN, week)** cell. `week(d) = (d − 2017-01-02) // 7`. The score is a step function — it changes
only when a new PBJ quarter becomes *available* under §4 — and that quantization is the reason for
the lead-time rule in §7.

## 3. Labels

A **survey event** is a distinct `(CCN, Survey Date)` pair, not a CSV row (418,479 rows collapse to
90,760 events; grading rows would count one inspection dozens of times).

A survey event is a **harm event** iff any of its rows carries scope/severity in `{G,H,I,J,K,L}`.
Immediate jeopardy `{J,K,L}` is reported separately and is **not** a second bar.

Cell `(c, w)` is **positive** iff a harm event at `c` falls in weeks `(w, w+26]` — strictly future.
`H = 26` weeks.

**Label window `2024-01-01 … 2026-03-31`, and the censoring that forces it.** The file retains
roughly the three most recent inspection cycles per facility, so it is censored at both ends and
**the left censoring is not random: a frequently-surveyed facility has a shorter observed history,
and frequently-surveyed facilities are the troubled ones.** Using earlier labels would under-label
precisely the facilities this index is about. The window start is where facility coverage reaches
92.4%; the end drops 2026-05 (50 cited surveys against a ~2,000–2,600 monthly norm — 2% reported).
Full counts are tabulated in WORKBOOK §5.

**Per-facility left truncation** applies on top: a cell is scored only if the facility's earliest
observed citation precedes the cell's week start by ≥182 days. Dropped-cell counts are published.

## 4. Signal construction (frozen) — including the leak control with no NHTSA analogue

Nine features per `(CCN, quarter)`, defined exactly in WORKBOOK §6: three level terms
(`hprd_total`, `hprd_rn`, `rn_share`), three instability terms (`weekend_gap`, `hprd_cv`,
`low_days_frac`), one workforce-composition term (`contract_frac`), one **deterioration** term
(`hprd_trend`, the quarter against its own trailing four-quarter mean), and `census` as a size
control. `low_days_frac` uses **3.48 HPRD** — the CMS 2024 minimum-staffing final rule's total
threshold, chosen because it is externally fixed and therefore untunable by us.

`S(c, w)` is a **logistic regression** over the nine features, standardised on the train split,
coefficients fit on the **train split only**. The published report prints every coefficient.

**The publication-lag rule.** Quarter `Q`'s features may be used only for weeks beginning on or
after **`Q_end + 135 days`** (observed lags: 91 days for 2026Q1, 106 days for 2025Q4). Without it
the retrocast would silently assume knowledge about three months before it was public and every
lead-time number would be fiction. NHTSA needed no such rule because complaints publish daily.

Leak controls, each independently auditable in the hostile review: (a) features use only PBJ
quarters available under the 135-day rule; (b) archived vintages only, never as-revised; (c) the
operating threshold is fixed on train before test is scored; (d) train and test horizons do not
overlap by one day (§5); (e) lead time is measured from the first pre-event crossing.

## 5. Temporal split (frozen)

| split | cell week-starts | weeks |
|---|---|---|
| Train | 2023-12-25 … 2024-09-23 | 40 |
| **Gap — not scored** | 2024-09-30 … 2025-03-17 | 25 |
| Test (held out) | 2025-03-24 … 2025-09-22 | 27 |

Last train horizon ends **2025-03-30**; first test horizon begins **2025-03-31**. Reported metrics
are test-only. The train window is short in *calendar* terms (about three distinct feature
quarters) while being large in cells; the report states this rather than letting the cell count
imply more temporal variation than exists.

## 6. Controls, base rate, and the two dumb baselines

- **Realistic base rate.** Metrics are computed at the natural prevalence of positive cell-weeks, never a balanced sample. Because the scored universe excludes cells dropped by §3/§4, **both the scored base rate and the full-grid base rate are computed and published**, in that order, whichever way they cut. (NHTSA v1's scored universe made its precision bar *easier*; that was disclosed with the number and the same disclosure is pre-committed here.)
- **Dumb baseline (i) — prior-harm rate.** The facility's harm events per observed year, up to the cell week. This is the hard one: "troubled facilities stay troubled" explains most of this literature, and if staffing adds nothing to it, the index does not publish as a signature.
- **Dumb baseline (ii) — level only.** `−hprd_total` alone: the plain staffing level CMS already publishes as a star rating. This tests whether the *instability and deterioration* construct adds anything to the number already on Care Compare.
- **The bar is against the better of the two** (§7). Beating only the weaker one is not a pass.
- **Matched controls.** For the per-case receipts, each flagged harm event is shown against non-flagged facilities in the same state and census band. If the operating threshold collapses such that controls are flagged too, the column is **declared vacuous in the report** rather than printed as if it meant something.

## 7. Pre-registered pass thresholds (frozen — the publish gate)

Computed on the **held-out** window at the **train-chosen** operating point, against the real base rate:

1. **PR-AUC** of the signature **≥ max(prior-harm PR-AUC, level-only PR-AUC) + 0.05 absolute**; AND
2. **precision ≥ 0.35** at the primary operating point; AND
3. **event-recall ≥ 0.50** of held-out harm events led; AND
4. **median lead-time ≥ 60 days**, *and* **not degenerate** (below); AND
5. calibration published across deciles, miscalibration disclosed rather than hidden.

**The degeneracy rule, pre-committed (new in v2 of our own practice).** If **≥50% of true-positive
lead times fall within one week of the horizon edge (182 days)**, the lead-time result is
**declared degenerate and `lead_ok` is FALSE regardless of the median.** NHTSA v1's median lead of
168 days "passed" only because the threshold had collapsed and half the leads sat on the window
edge; that was caught in hostile review after the fact. Here it is a bar, in advance. Because the
score is a quarterly step function, this index is *a priori* at high risk of failing it — and
failing it is the informative outcome: it would mean the staffing signature is a persistent
facility characteristic, not a timed early warning, which is a true and publishable finding.

**Why precision 0.35.** The label-side harm share was measured **before** freezing — 0.182 (2023),
0.193 (2024), 0.193 (2025) of cited surveys — so the cell-level base rate is expected in the high
teens. The bar is set at roughly **twice the prior**, deliberately, because NHTSA v1's precision bar
of 0.30 against a 1.9% base rate produced the useless result `precision = 0.0190 = the base rate
exactly`. A precision bar must be meaningfully above the prevalence it is graded against or it
measures nothing. This is the one place where knowing a label-side marginal in advance makes the
bar **harder**, not easier, and it is disclosed here for exactly that reason.

**Failing these bars is a publishable outcome** — autopsy in DEAD-REGISTRATIONS.md — not a reason to
move them. No bar moves after results. No model is re-tuned after results.

## 8. Reported but NOT graded

Published because they are informative, excluded from the gate because they were not designed as
falsification tests: the immediate-jeopardy-only variant; the **survey-conditional** variant
(universe restricted to cells with a cited survey in the horizon, which controls the surveillance
confound but conditions the universe on a post-`t` fact); the interpretable single-feature rankings;
and the PROVNAME-change sensitivity re-run required by WORKBOOK §3/R1.

## 9. The naming gate is not opened by this registration

Per covenant 2 and the work order: **no named facility publishes.** The publishable surface for this
index is the **county-level** aggregate (PBJ carries `COUNTY_NAME`/`COUNTY_FIPS`); the named-facility
tier stays gated behind a published track record, a frozen editorial rubric, and explicit operator
sign-off. A passing retrocast does not by itself open it. Publication of *anything* from this index
also remains behind operator gate ⚑ #219, which this worker does not pre-empt.

## 10. Outputs (SPEC-08 §3)

`retrocast/hospital-care/results/v1/` will hold the full PR curve, the lead-time distribution, the
calibration table, headline metrics with CIs, and the per-case scored table. `scorecard.json`
records this file's commit hash, the archived object keys and sha256s, the metrics, and pass/fail
against §7. `REPORT.md` is written to survive the SPEC-08 §5 hostile-review checklist, which is run
as a separate pass before anything is considered done.

---
*Frozen 2026-07-29. Any change after results are seen ⇒ v2 + disclosure in DEAD-REGISTRATIONS.md.*
