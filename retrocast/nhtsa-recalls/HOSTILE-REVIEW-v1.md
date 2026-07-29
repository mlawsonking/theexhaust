# Hostile review — NHTSA Shadow Recalls retrocast v1

*SPEC-08 §5 checklist, walked as a separate pass over finished artifacts (results were already
written and committed before this review began). The posture is adversarial by design: the job is
to find the reason this result should not be believed, including reasons that would make a
**failing** result wrong. A retrocast that fails for the wrong reason is as bad as one that passes
for the wrong reason — it would defame the method instead of an entity.*

**Outcome: 6/6 checklist items zeroed. 5 findings raised, all dispositioned; 2 of them changed
what is published.** One residual is carried to a v2 pre-registration (F-1b) and one is an
acceptance note for the orchestrator (F-6b).

*Independence note: this pass was run by the same session that produced the results, which is
weaker than an independent reviewer. The constitution's standing rule — an independent adversarial
review before BUILD-item acceptance — still applies and is the orchestrator's, not this session's.*

---

## 1. Leakage hunt — *does any feature peek past the moment of measurement?*

**Checked.**

- Every feature window is closed at `t`: `[t-11, t]` and `[t-51, t]`, maintained by sliding sums
  that only ever add bucket `t` and drop buckets `t-12` / `t-52`. `test_a_complaint_in_the_future_
  moves_nothing_at_t` plants complaints at `t+1` and `t+50` and asserts every feature at every
  week ≤ t is bit-identical; `test_sliding_windows_match_brute_force` checks the sliding sums
  against a brute-force recompute on 25 random cells.
- Complaints enter on `max(DATEA, LDATE)` — the later of the two as-known-then dates — so no
  complaint can enter a window earlier than either date permits (194,986 rows have `DATEA` later,
  17,878 have `LDATE` later; the choice is the conservative one on both).
- Everything learned is learned on train only, and each was verified in the code path rather than
  assumed: the standardization means/stds (`Xtr`), the logistic coefficients (`Xtr`, `ytr`), the
  operating threshold (`tr_obs`, `tr_labels`), and the seasonality baseline's calendar-week rates
  (masked by `train_mask`).
- Labels use `RCDATE` (report received), never `ODATE` (owner notification), which post-dates the
  event and would have inflated every lead.
- The labelling used for the fit was cross-checked against the harness's own `label_cells` on
  200,000 rows: **0 mismatches**.

**F-1a (raised, disclosed, no bar affected).** The harness's own scan flagged **95 of 3,295 leads
as non-positive** — first crossings inside the *same week bucket* as the recall report date. This
is a genuine boundary leak: within that one bucket a complaint filed after the recall is reported
can still enter the feature scored against it. It is 2.9% of leads, cannot touch any lead ≥ 7
days, and cannot rescue any of the three failing bars. Published in REPORT §4 rather than filed
off. **F-1b (carried to v2):** a v2 registration should use a strictly-before-`t` window.

**F-2 (raised, judged not a leak).** The component crosswalk was authored after measuring
top-level label frequencies across the *whole* corpus, test window included. Those counts describe
the two vocabularies, never which cells were recalled; no version of the crosswalk was scored
against outcomes, and the mapping was committed (`122c89e`) before any result existed. Judged
vocabulary evidence, not outcome evidence. Disposition: disclosed in the workbook, no change.

**Zeroed.**

## 2. Vintage audit — *revised-data contamination?*

**Checked.** One vintage pair, both sides from the same 2026-07-28 12:20 UTC collection cycle,
both hash-pinned in code, both re-hashed at read time with the run aborting on mismatch. The
retrocast code imports no HTTP client at all — there is no live-endpoint path to take even by
accident. The archived flat file is the record, as the government-continuity posture requires.

Right-censoring is bounded and stated: the last scored week's 26-week horizon ends 2026-06-30,
inside the labels vintage, so no scored cell-week lacks label coverage; campaigns received in the
final days before 2026-07-28 may not yet appear.

**Zeroed.**

## 3. Base-rate honesty — *precision against realistic priors, not a balanced sample?*

**Checked.** Nothing is downsampled or rebalanced anywhere: all 2,547,639 held-out cell-weeks are
scored and the reported precision is against the natural 1.90% prevalence.

**F-3 (raised, and it changed what is published).** The scored universe excludes 59.4M cell-weeks
with no trailing complaints. Excluding near-certain negatives *raises* prevalence — the scored
universe runs at 1.90% against 0.714% for the full (cell × week) grid — which made the precision
bar **easier** than the full grid would have. A reviewer would rightly ask which direction that
cut. Disposition: the full-grid prevalence is now computed by the run itself, published in the
scorecard, and the direction of the bias is stated in REPORT §4. Precision still missed by 16×.

**Zeroed.**

## 4. Control validity — *would a dumb baseline score the same?*

**Checked, and this is the finding that decides the outcome.** Both pre-registered dumb baselines
were run. Volume-only reaches PR-AUC **0.0331**; the five-feature signature reaches **0.0280**.
The signature does not merely fail to beat naive volume by the required 0.05 — it loses to it.
Seasonality-only lands at 0.0196 against a 0.0190 base rate, which is the sanity check that the
harness measures what it claims.

**F-4 (raised, and it changed what is published).** The matched-control design of registration §6
is **vacuous in this run**: `matched_controls_not_flagged` is 0 for all 7,806 cases, because the
collapsed threshold flags the controls too. Presenting that column without comment would imply a
discrimination that does not exist. Disposition: stated in `results/v1/README.md` and REPORT §3.3.

**Zeroed.**

## 5. Threshold archaeology — *do the published bars match the registration commit?*

**Checked.**

- `lexicon.BARS` is asserted equal to the registration §7 numbers by a test that runs in CI
  (`test_bars_match_the_pre_registration_verbatim`), and `scorecard.json` carries the same values.
- The run resolves the registration's own commit from git, asserts it is an ancestor of the code
  commit, and **aborts** otherwise. Recorded ordering: registration `e3d4d84` 2026-07-13 → workbook
  freeze `122c89e` 2026-07-28 → results code `54b48e5` 2026-07-29, tree clean.
- Nothing in the frozen set moved after results were seen: not the signal, the labels rule, the
  splits, the lexicon, the crosswalk, the interpretable rule, or the bars.
- Two post-first-run corrections exist and both are published with pre-fix numbers (REPORT §5).
  The one that touches a metric — labels as distinct events rather than duplicated flat-file rows
  — moved event-recall 0.3120 → 0.4221, i.e. **toward** the bar, and it still fails. That
  direction is stated explicitly so the correction cannot be read as bar-shopping.
- The harness changes this item required (`test_start`, train/test label windows, the O(N log N)
  operating-threshold search) all landed **before** the first run, carry a backward-compatibility
  test proving the defaults are unchanged, and an exact-equivalence test against the brute-force
  implementation — which caught a real divergence at target-recall 0.

**F-5 (raised, judged benign).** The fit's optimizer settings (2,000 epochs, lr 0.5) are an
implementation choice made pre-run and could in principle have hidden a stronger model behind a
half-trained one — a way to fail for the wrong reason. Checked rather than argued: the published
gradient norm is 5.99e-08 and an independent IRLS/Newton solve reproduces the coefficients to 4
decimals and the log-loss to 8 in 9 iterations. The fit is at the maximum-likelihood optimum.

**Zeroed.**

## 6. Overclaim scan — *report prose vs never-predict-only-measure*

**Checked.** The report states a failure in the first line, reports the one passing bar as *not*
evidence, and carries an explicit "what this does and does not say" section. The opening question
was reworded during this pass from "the vehicles NHTSA is about to recall" to a backward-looking
formulation — the original read as forecasting even though the artifact forecasts nothing.

**F-6a (raised, and it changed what is published).** `cases.csv` pairs manufacturer and model
names with a `flagged` column produced by an unvalidated signature. Under covenant 2 the naming
gate opens only after a published, passing retrocast plus a frozen rubric plus written operator
sign-off — none of which exist. Balanced against SPEC-08 §3, which *requires* a per-case receipts
table, and the anti-ShadowStats clause, which requires that a critic can rerun the derivation.
Disposition: the file stays (it is the falsifiability), no site surface renders it, and
`results/v1/README.md` states plainly that it is an audit trail, that the signature failed, and
that the `flagged` column means only "this cell had complaint history in the window" because the
threshold collapsed.

**F-6b (acceptance note for the orchestrator).** Landing this scorecard flips the site's Track
Record page from its "no scorecards yet" branch to a live PASS/FAIL table. The page now states
that the bars were pre-registered and that failures stay published — but the site is **not
deployed** (⚑ #217 is open, and `--placeholder` mode emits exactly one page that renders none of
this), so nothing has been published to the public yet. Whether The Exhaust's first public number
should be its own failure is a launch-surface decision for W-007 and the operator, not a worker's.

**Zeroed.**

---

## Verdict

The failure is real, and it fails for the right reasons. The three failing bars are not artifacts
of a leak, a stale vintage, a rebalanced sample, a mis-set threshold or an under-trained model —
each of those was the specific thing this pass tried to prove, and each was ruled out with
evidence rather than assertion. The binding constraint is structural and would defeat any model:
**57.8% of held-out recall campaigns occur in cells with no complaint at all in the preceding 26
weeks**, so the pre-registered 0.50 event-recall bar was unreachable the moment the corpus was
joined.

The publication gate does not open. The autopsy is logged in
[`../DEAD-REGISTRATIONS.md`](../DEAD-REGISTRATIONS.md), and a v2 requires a new pre-registration
with the disclosure the doctrine mandates.
