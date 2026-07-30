# Hostile review — Hospital/Care Distress retrocast v1

*The [SPEC-08](../../ops/SPEC-08-retrocast-harness.md) §5 checklist, walked as a separate pass after
the run, deliberately hunting the ways this retrocast could have **failed for the wrong reason**.
A failure caused by a bug is worthless; a failure caused by the world is the product.*

**Outcome: 6/6 items zeroed, 5 findings, one of which was a real defect in the shared harness and
is fixed.** Run artifacts: [`results/v1/`](results/v1/) · registration
[`PRE-REGISTRATION-v1.md`](PRE-REGISTRATION-v1.md) (`d6b78c3`, 2026-07-29 23:47 −05:00) · results
code `66d1815` (2026-07-30) · clean tree (`dirty: false`).

---

## 1. Leakage hunt — **zeroed**, with one finding

**The automated flag.** The harness reported *"5 label(s) 'detected' at/after the event (lead≤0)"* —
5 of 2,138 true-positive leads (0.23%).

**Answered with arithmetic, not argument.** A score at week *w* is built from a PBJ quarter that
ended at least `PBJ_AVAILABILITY_LAG_DAYS = 135` days before *w* begins. The run measures the
realised gap directly: over the **2,424** held-out cell-weeks that share their week with a harm
survey, the smallest gap between the staffing quarter's **end** and that week is **139 days**
(`diagnostics.min_days_feature_quarter_end_to_same_week_event`). Leakage is therefore arithmetically
impossible: the staffing data was already 4½ months stale when the surveyor arrived. A lead of 0
means only that the crossing *week bucket* equals the event *week bucket*. Carried to v2 as the
same residual NHTSA v1 carried: a strictly-before-`t` window would remove the bucket entirely.

**FINDING H-01 (real defect, fixed).** SPEC-08 §7 criterion 2 requires that *"a deliberately-leaked
feature planted in a test run is caught by the checklist procedure."* Planting the cell label itself
as the score produced **precision 1.0000 against a 13.6% base rate** — unmistakably leaked — and
`harness.leakage_scan` returned an **empty** flag list. Both existing rules are about the *shape* of
the score and both missed it: a binary oracle's PR curve has two points, so its PR-AUC came out
0.1357 (nowhere near the ≥0.999 trigger); and with a horizon-based label an oracle *leads* the event
by construction, so no lead was nonpositive. Precision against the base rate does not care about
score granularity, so it catches a plant of either shape; it is now a fourth rule, with both plant
shapes under regression test. NHTSA v1 is unaffected (its precision was 0.0190) — the guard only
ever got stricter. **The criterion is met only because the review ran it for real rather than
assuming the previous index's plant generalised.**

**Structural controls, each independently checkable.** Features use only PBJ quarters admitted by
the 135-day rule (asserted week-by-week in `test_the_operative_quarter_for_a_week_is_always_already_published`);
the operating threshold is chosen on train and frozen before test is scored; the last train horizon
ends **2025-03-30** and the first test horizon begins **2025-03-31**, so the two do not overlap by a
single day.

## 2. Vintage audit — **zeroed**

Every input is an archived, hash-pinned R2 object, re-hashed on every run; a mismatch aborts.
Neither `run_v1` nor `features` imports an HTTP client, so "no live endpoint" is a property of the
code rather than a promise. Twelve feature quarters (2022Q2…2025Q1) plus four presence-only
quarters, and one deficiency vintage (`NH_HealthCitations_Jun2026.csv`, Processing Date 2026-06-01).

**Independent corroboration of the as-known-then rule.** CMS embeds the publication month in each
download URL (`.../files/YYYY-MM/<uuid>/...`). The run checks all 16 releases and **aborts** if the
135-day rule would have permitted use before the file's own publication month ended. All 16 pass,
with margin — e.g. 2025Q1 ends 2025-03-31, publishes 2025-07, and is usable under the rule only from
2025-08-13.

**FINDING H-02 (disclosed limitation, not fixable in v1).** The ground truth is **one** vintage. CMS
overwrites this file in place and The Exhaust only began snapshotting it on 2026-07-28, so there is
no second vintage against which to audit label revisions. This is the single largest limitation of
v1 and it is the one the archive itself repairs: every vintage collected from now on preserves
label history CMS will later drop out of its three-cycle retention window.

## 3. Base-rate honesty — **zeroed**

Metrics are computed at natural prevalence; nothing is balanced or downsampled.

| universe | base rate |
|---|---|
| scored test cell-weeks (369,750) | **0.135651** |
| full facility × week test grid (386,478) | **0.136587** |

The §3/§5 exclusions moved the prevalence **down** by 0.000936 — so the scored universe runs
marginally *cooler* than the full grid and the precision bar was, if anything, very slightly
**harder** than it would have been otherwise. This is the opposite direction from NHTSA v1 (where
exclusions made the bar easier) and it is stated either way, because which way it cuts is not
something the publisher gets to choose after the fact.

The precision bar itself (0.35) was set at roughly twice a label-side prior measured **before** the
freeze (harm share of cited surveys: 0.182 / 0.193 / 0.193 for 2023 / 2024 / 2025). Measured
precision **0.1794** is 1.32× the realised base rate — better than chance, and less than half the
bar.

## 4. Control validity / dumb baselines — **zeroed**, and this is the cause of death

Both pre-registered baselines were computed, and the bar was applied against **the better of the
two**, as registered.

| | PR-AUC | precision | event-recall |
|---|---|---|---|
| **signature (9 features)** | **0.1771** | 0.1794 | 0.4605 |
| dumb baseline (i) — prior-harm rate | **0.2526** | 0.1357 | 0.9468 |
| dumb baseline (ii) — staffing level only | 0.1726 | 0.1664 | 0.4812 |

**The signature loses to the facility's own citation history by 0.0755 of PR-AUC**, against a bar
that required beating it by +0.05.

Two honest qualifications, both of which belong in the record:

- **The comparison is about ranking, not about a usable operating point.** The prior-harm baseline's
  own precision at its operating point is **0.1357 — exactly the base rate**, and its event-recall
  of 0.9468 is exactly the ceiling; it "wins" by flagging almost everything in an order that happens
  to be better than ours. Neither the signature nor the baseline reaches a precision anyone could
  act on. Saying only "we lost to the dumb baseline" would overstate the baseline.
- **The signature barely beats plain staffing level.** Best single-feature test PR-AUCs:
  `hprd_total` 0.1726 (negative sign), `low_days_frac` 0.1717, `census` 0.1536, `contract_frac`
  0.1534, `hprd_rn` 0.1528, `rn_share` 0.1424, `hprd_trend` 0.1410, `weekend_gap` 0.1392, `hprd_cv`
  0.1385 — against a 0.1357 base rate. The full nine-feature model scores 0.1771, i.e. **+0.0045
  over the best single feature.** The instability and deterioration terms the registration was built
  around carry coefficients of −0.003 (`weekend_gap`), +0.001 (`hprd_cv`) and +0.005
  (`low_days_frac`) and add essentially nothing at quarterly aggregation.

**Matched controls are valid here, unlike NHTSA v1.** 523,787 matched controls (same state, same
25-bed census band, observed in the same pre-window), of which **288,227 (55.03%) did not cross
threshold**. The column means something and is published; the flag rate is 0.3352.

**FINDING H-03 (reported, not graded).** The survey-conditional variant — universe restricted to
cells with a cited survey of any severity in the horizon, which controls the surveillance confound —
scores PR-AUC **0.3036** and precision **0.3028**, by far the most flattering cut. It is reported
and **deliberately not graded**, because it conditions the scored universe on a post-`t` fact. It is
named here so that nobody can later present it as the headline.

## 5. Threshold archaeology — **zeroed**

`BARS` in `retrocast/hospital_care/spec.py` is asserted equal to the registration's §7 prose by
`test_bars_match_the_pre_registration_verbatim`, which runs in CI. The registration commit
`d6b78c3` (2026-07-29 23:47) is asserted by the run to be an ancestor of `HEAD` **and of
`origin/main`** — the run aborts otherwise. The second check exists because `git cat-file -e`
false-passes a hash that only ever existed locally (BUILD-PROTOCOL §2.7).

**No bar was moved and no model re-tuned after results.** The workbook, the registration and the
frozen constants were committed and pushed in a single commit before `run_v1.py` existed.

**FINDING H-04 (the degeneracy rule did not fire, which is the point).** The registration
pre-committed that if ≥50% of true-positive leads sat within a week of the 182-day horizon edge, the
lead-time result would be declared degenerate and `lead_ok` forced FALSE regardless of the median.
Measured: **925 of 2,138 leads at the edge = 43.3%**, under the bar. So the one bar this retrocast
passed, it passed legitimately — median lead **154 days** (p25 70, p75 175). Had the rule been
written after seeing 43.3%, it would be worthless; it was written before, and it did not fire.

**Under-training ruled out with evidence.** Published fit: gradient norm 3.83e-05, train log-loss
0.435322. Refit at 20,000 epochs: gradient norm **2.19e-16**, log-loss 0.435322, and metrics
identical to four decimals (PR-AUC 0.1771, precision 0.1794, event-recall 0.4607 vs 0.4605). An
independent Newton/IRLS solve reaches the same log-loss in 6 iterations (max coefficient difference
8.59e-03). The published coefficients are the maximum-likelihood fit; the failure is not an
optimiser artefact.

**The operating point transferred.** Train event-recall at the chosen threshold is **0.5000** —
exactly the target — and held-out event-recall is 0.4605; train flag rate 0.4096 vs test 0.3352. The
threshold did **not** collapse to the floor (`operating_point_is_degenerate: false`), which is a
materially different situation from NHTSA v1.

## 6. Overclaim scan — **zeroed**, with one correction

The report is past-tense and comparative throughout. **No causal language**: this measures whether a
staffing pattern *preceded* a harm citation, and states plainly that it does not establish that
staffing *caused* it — a distinction this index invites readers to blur more than any other in the
portfolio.

**No named facility appears in any published surface.** The naming gate (covenant 2) is untouched
and a failed retrocast opens nothing. The per-case receipts (`results/v1/cases.csv`) carry CCN,
state and county because an evidence bundle a critic cannot check is not evidence; that file is the
scorecard's audit trail, not a published claim, and no site page renders a facility.

**FINDING H-05 (corrected before publication).** A first draft of the report described the result as
"staffing does not predict harm". That is an overclaim in the *negative* direction — the signature
does carry signal (precision 0.1794 against a 0.1357 base rate; calibration monotone across all ten
deciles, 0.0879→0.0747 at the bottom and 0.2217→0.2104 at the top). What the evidence supports is
narrower and is what the report now says: *at this unit of analysis, on this window, the staffing
signature did not beat the facility's own citation history, and did not reach the pre-registered
bars.* Failing honestly includes not overstating the failure.

---

## Three defects found by running it, all before any number was published

Recorded because each would have quietly changed a published figure, and because none was found by
reading the code:

1. **The test label window reached one week past the furthest any cell horizon can reach.** Events
   in that week would have been counted as misses no threshold could ever have caught — roughly
   0.7% of held-out harm events, straight off event-recall. Fixed before the first successful run;
   no published number was ever computed with it.
2. **Facility-quarters reporting a resident census with zero weekday nursing hours** make
   `weekend_gap` undefined rather than zero (a division by zero). Handled as the workbook prescribes
   for an inadmissible quarter: drop and count, never impute.
3. **One trailing short row per PBJ release.** Skipped and counted (3 across the run), so a release
   that genuinely changed width would surface as a number rather than as silence.

## What this review did not and could not check

- **Label revision**, per H-02 — one vintage exists.
- **Whether a different unit of analysis would pass.** Nothing here tests a facility-quarter unit, a
  longer horizon, or a case-mix-adjusted staffing measure. Those are v2 hypotheses and are named in
  [DEAD-REGISTRATIONS.md](../DEAD-REGISTRATIONS.md) as untested.
- **The in-session problem.** This review was written by the same session that ran the retrocast.
  For NHTSA v1 the orchestrator required an *independent* hostile-review confirmation before
  publication; the same precondition should apply here, and this document does not substitute for
  it.
