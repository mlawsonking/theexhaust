# Hospital/Care Distress — retrocast v1 report

**Result: the retrocast did not clear its pre-registered bars.** Three of four failed. It is
published anyway, with the autopsy, because that is the rule we set before we knew the answer.

**Index:** Hospital/Care Distress (nursing-home care fragility) · **Version:** v1 · **Scored:** 2026-07-30
**Registration:** [PRE-REGISTRATION-v1.md](PRE-REGISTRATION-v1.md), frozen and pushed `d6b78c3`, 2026-07-29 23:47 −05:00
**Frozen constants:** [WORKBOOK](../../indexes/hospital-care/WORKBOOK.md) · **Results code:** `66d1815`, clean tree
**Hostile review:** [HOSTILE-REVIEW-v1.md](HOSTILE-REVIEW-v1.md) — 6/6 items zeroed, 5 findings
**Evidence bundle:** [`results/v1/`](results/v1/) · machine-readable [`scorecard.json`](results/v1/scorecard.json)

---

## 1. What was tested

Whether a nursing home's **payroll-verified nurse staffing** in one quarter measurably precedes an
**actual-harm deficiency citation** at that home in the following six months — well enough to
publish a county-level care-fragility index with receipts.

The join needs no matching: `PROVNUM` in the Payroll-Based Journal *is* the CMS Certification Number
in the deficiency file. 14,431 of 14,487 facilities (99.6%) appear on both sides. No semantic
matching, no entity resolution, and **no LLM anywhere in the pipeline** — a critic with no API key
can rerun every number.

This is **not a novel question.** Staffing→deficiency is a mature literature and CMS already
publishes star ratings built from these two datasets; see [prior-art-scan.md](prior-art-scan.md).
The contribution attempted here was not a method but a *scorecard*: pre-registered, falsifiable,
public, and permanent.

## 2. The verdict

| bar (registration §7) | required | measured | |
|---|---|---|---|
| PR-AUC vs the better dumb baseline | ≥ +0.05 | **0.1771 vs 0.2526** — loses by 0.0755 | ✗ |
| precision at the operating point | ≥ 0.35 | **0.1794** (base rate 0.1357) | ✗ |
| event-recall | ≥ 0.50 | **0.4605** | ✗ |
| median lead-time, and not degenerate | ≥ 60 d | **154 d**, 43.3% at the edge — under the 50% degeneracy bar | ✓ |

Held out: 27 weeks of cell-weeks (2025-03-24 … 2025-09-22), **369,750 scored cell-weeks**,
**4,643 harm-citation events** evaluated, at **14,314 facilities**. Train and test horizons do not
overlap by a single day.

## 3. Cause of death — a facility's own history beats its staffing

The pre-registered hard baseline was the facility's **prior harm-citation rate**: troubled homes
stay troubled. It scores **PR-AUC 0.2526**. The nine-feature staffing signature scores **0.1771**.
The registration required the signature to beat the better baseline by +0.05; it lost to it by
0.0755.

Two qualifications, because the bald statement overstates the baseline:

- **This is a ranking result, not an operating-point result.** The prior-harm baseline's own
  precision is **0.1357 — exactly the base rate** — and its event-recall of 0.9468 is exactly the
  ceiling: it flags nearly everything, in a better order than we do. *Neither* the signature nor the
  baseline reaches a precision anyone could act on.
- **The signature is essentially "how low is the staffing".** Staffing level alone
  (`−hprd_total`) scores 0.1726. The full nine-feature model scores 0.1771 — **+0.0045**. The
  instability and deterioration terms the registration was built around — the weekend staffing drop,
  the day-to-day variability, the share of days below the CMS minimum, the quarter-over-quarter
  trend — carry fitted coefficients of −0.003, +0.001, +0.005 and +0.055 and add almost nothing.

**Second cause: the horizon is short relative to the surveillance calendar.** Event-recall reached
0.4605 against a 0.50 bar. Unlike NHTSA v1 this was *not* a structural ceiling — 94.68% of held-out
harm events had a scored cell in their pre-window, so the misses are the model's, not the corpus's.
The threshold also transferred honestly: train event-recall at the chosen operating point is 0.5000,
exactly the target, and held-out is 0.4605. The model degraded modestly out of sample; it did not
collapse.

## 4. What did work, stated so the failure is not overstated

- **The signature carries real signal.** Precision 0.1794 against a base rate of 0.1357 is 1.32×
  chance, with a Wilson 95% interval of [0.1773, 0.1815].
- **It is well calibrated.** Predicted-vs-observed is monotone across all ten deciles and tracks
  closely — 0.0879 → 0.0747 in the bottom decile, 0.2217 → 0.2104 in the top — with a mild,
  consistent over-prediction. Full table: [`calibration.csv`](results/v1/calibration.csv).
- **The direction of every meaningful coefficient is the one the literature predicts.** Lower total
  hours per resident-day raises predicted harm risk (`hprd_total` −0.342, the strongest term), and
  greater reliance on contract staff raises it (`contract_frac` +0.119).
- **Matched controls are valid**, unlike NHTSA v1's: of 523,787 matched controls (same state, same
  25-bed census band), **55.03% did not cross threshold**.
- **The lead-time result is real.** Median 154 days (p25 70, p75 175). We pre-committed to declaring
  it degenerate if half the leads piled on the horizon edge; 43.3% did, which is under the bar, so
  the one bar that passed, passed legitimately.

## 5. The three-cycle censoring problem, and why the window is short

This is the finding most likely to matter to anyone else who uses this file. CMS's Health Citations
download retains roughly the **three most recent inspection cycles per facility**, so its
2017–2026 date span is not nine years of history — it is a rolling window, censored at both ends,
and **the left censoring is not random**: a frequently-surveyed facility has a *shorter* observed
history, because three cycles cover less calendar time, and frequently-surveyed facilities are the
troubled ones.

Before 2023 the file holds about **one** cited survey per facility per year across a minority of
facilities; from 2023 it holds 1.7–2.3. Scoring pre-2024 labels would have under-labelled precisely
the facilities this index is about, and would have manufactured a failure that had nothing to do
with staffing. The label window was therefore fixed at **2024-01-01 … 2026-03-31** (92.4% facility
coverage at the start; the final month is 2% reported and was dropped along with the one before it),
with a per-facility 182-day observation requirement on top. Counts are in
[WORKBOOK §5](../../indexes/hospital-care/WORKBOOK.md).

That is what caps the study at 40 train weeks and 27 test weeks. **The archive is the repair.** Every
deficiency vintage collected from 2026-07-28 onward preserves label history CMS will later drop out
of its own retention window — history that will exist nowhere else. A v2 run in a year will have
more of it than anyone, including CMS, can reconstruct.

## 6. As-known-then: the control with no NHTSA analogue

NHTSA complaints publish daily; PBJ does not. Quarter *Q*'s staffing may only be used for weeks
beginning at or after **Q_end + 135 days** — otherwise the retrocast would silently assume knowledge
about three months before it was public, and every lead-time number here would be fiction.

The rule is verified rather than asserted: CMS embeds the publication month in each download URL,
the run checks all 16 archived releases against it and **aborts** if the rule would have permitted
an early read. All 16 pass. The realised consequence is visible in the data — over the 2,424
held-out cell-weeks that share a week with a harm survey, the staffing quarter had already ended a
minimum of **139 days** earlier.

## 7. Scope, and what does not follow from this

- **No facility is named anywhere on the site.** The naming gate (covenant 2) is untouched; a failed
  retrocast opens nothing. The published surface for this index, if it ever has one, is the
  **county-level** aggregate.
- **Nothing here is causal.** This is a measurement of whether a pattern *preceded* a citation. It
  does not establish that staffing *caused* harm, and no sentence in this report should be read that
  way. Never predict, only measure.
- **This does not refute the staffing–quality literature.** That literature is cross-sectional and
  well supported, and our own coefficients point the same way. What failed is a specific,
  pre-registered *forecasting* claim at a specific unit of analysis over a 27-week held-out window.

## 8. What it cost

About five minutes of desktop CPU per scored run after the archive was in place, one session, and
**no metered spend of any kind**. The full-history PBJ backfill it required moved ~8.7 GB and
brought the archive to 1.9 GB against R2's 10 GB free tier.

---

*A v2 is permitted and would be a **new** pre-registration with this attempt disclosed — not an edit
of v1. Candidate hypotheses the evidence points at, none of them tested here and none of them
claimed, are listed in [DEAD-REGISTRATIONS.md](../DEAD-REGISTRATIONS.md).*
