# NHTSA Shadow Recalls — retrocast v1 report

**Result: FAILED its pre-registered bars. This index does not publish as a signature.**

*Generated 2026-07-29 from `results/v1/scorecard.json`. Pre-registration:
[`PRE-REGISTRATION-v1.md`](PRE-REGISTRATION-v1.md), frozen 2026-07-13 in commit `e3d4d84` —
**fifteen days before the code that produced any number below was written.** Workbook freeze (component
crosswalk + hazard lexicon): `d28d8fa`, 2026-07-28. Results code: `2f914c2`. Git history is the
receipt; `git log` will show the same ordering to anyone who checks.*

---

## 1. What was measured

Did the pattern of consumer complaints filed with NHTSA measurably precede the recall campaigns
NHTSA went on to receive — and if so, by how many days? This is a backward-looking measurement
over a closed historical window. Nothing here forecasts a future recall.

- **Unit:** one (make, model, model-year, component-group) cell per week, 2015-01-01 → 2025-12-31.
- **Signal:** five features per cell-week, computed only from complaints received on or before
  that week — trailing 12-week count, the cell's rate relative to its own trailing-52-week
  baseline, week-over-week acceleration, the share of trailing complaints flagged crash/fire/
  injury/death, and the share whose narrative matches a frozen 82-term hazard lexicon.
  Scored by a logistic regression fit on the training window only.
- **Ground truth:** NHTSA recall campaigns, dated by **RCDATE** (the report-received date, not the
  later owner-notification date). A cell-week is positive iff a campaign for that cell was
  reported in the following 26 weeks.
- **Data:** the **archived** ODI flat files, never live endpoints — `FLAT_CMPL.zip`
  (`73acbdca6b6f…`, 2,229,384 rows) and `FLAT_RCL_POST_2010.zip` (`efab48ed2da2…`, 243,126 rows),
  both collected 2026-07-28 12:20 UTC and both hash-verified at read time. The run aborts if the
  bytes do not match the pin.
- **Splits:** signature and operating point learned on cell-weeks whose 26-week horizon ends on or
  before 2020-12-31; **everything reported below is the held-out 2021–2025 window**, which the
  model never saw. Cell-weeks whose horizon straddles the boundary (250,356 of them) are dropped.

Scale: 1,206,959 complaints and 216,449 recall rows entered the window; 5,928,725 cell-weeks were
scored across 113,761 cells; 21,093 distinct (cell, week) recall events were joined, of which
7,806 fall in the held-out evaluation window.

## 2. The scorecard against the frozen bars

| Pre-registered bar (§7) | Required | Measured | |
|---|---|---|---|
| PR-AUC vs the volume-only baseline | ≥ baseline **+0.05** | **0.0280** vs baseline **0.0331** | ✗ **worse than naive volume** |
| Precision at the operating point | ≥ **0.30** | **0.0190** (95% CI 0.0188–0.0192) | ✗ off by a factor of 16 |
| Event-recall at that point | ≥ **0.50** | **0.4221** | ✗ — and see §3.1: 0.4221 is the *ceiling* |
| Median lead time | ≥ **60 days** | **168 days** | ✓ *degenerately — see §3.3* |
| Calibration published | disclosed | published, near-flat | disclosed |

**Three of four bars fail, and the fourth passes for a reason that does not count.** Under the
registration and the constitution's doctrine, that is the end of the matter: the bars are not
moved, the model is not re-tuned, and the index does not publish a signature. The autopsy is
logged in [`../DEAD-REGISTRATIONS.md`](../DEAD-REGISTRATIONS.md).

## 3. Why it failed

### 3.1 Most recalls are invisible to complaints at this unit of analysis

Of the 7,806 recall events in the held-out window, **only 3,295 (42.2%) occurred in a cell that
had *any* complaint at all in the preceding 26 weeks.** The other 57.8% are recalls of
make/model/year/component combinations that the complaint corpus was silent about right up to the
filing.

No model can flag an event it has no data for, at any threshold. **The 0.50 event-recall bar was
therefore unreachable before a single coefficient was fit** — the ceiling is 0.4221. This is not a
test-window fluke: the same coverage on the training window is 0.3983.

That is the single most useful thing this retrocast produced. Recall campaigns are overwhelmingly
manufacturer- and regulator-initiated on evidence the public complaint stream does not carry —
supplier notifications, internal warranty data, compliance testing. The founding intuition that
"the complaints run ahead of the recall" is true for a *minority* of campaigns, and the
pre-registered bar assumed a majority.

### 3.2 The signature is beaten by counting complaints

| Model | PR-AUC (held-out) | Lift over the 0.0190 base rate |
|---|---|---|
| **Volume-only dumb baseline** (`n_trailing` alone) | **0.0331** | 1.74× |
| Pre-registered signature (5-feature logistic regression) | 0.0280 | 1.48× |
| Interpretable threshold rule (2× own normal / accelerating / ≥20% severe) | 0.0198 | 1.04× |
| Seasonality-only dumb baseline (calendar-week rate) | 0.0196 | 1.03× |

The registration required the signature to beat volume-only by 0.05 absolute. It does not beat it
at all. The fitted coefficients say why:

```
n_trailing +0.163   rate_ratio -0.318   accel +0.014   severity_frac +0.137   hazard_lang -0.150
intercept  -3.981   (features standardized on the train split; train log-loss 0.09555153)
```

Only raw volume and severity carry positive weight. **`rate_ratio` — the self-normalizing feature
the registration leaned on hardest, so that "models with more complaints" could not confound — and
`hazard_lang`, the frozen hazard lexicon, both get negative weight.** Normalizing a cell against
its own history actively destroys the one thing that predicts a recall: that the cell is a
high-volume cell. Big, popular, heavily-complained-about model-years get recalled more, and the
registration deliberately engineered that signal away.

Two dumb baselines were mandatory (§6) and both are here. Seasonality-only lands at the base rate,
as it should — the calendar tells you nothing, which is a sanity check that the harness is
measuring what it claims.

### 3.3 The operating point degenerates, and so does the lead time

The operating threshold is chosen on the training split as the highest score still reaching 50%
event-recall (§5c). Train coverage is 39.8%, so **50% is unreachable on the train split too**, and
the harness falls back to the lowest observed score. The model therefore flags *everything*.

Everything that follows is downstream of that:

- Precision equals the base rate exactly (0.018985) — that is what flagging everything gets you.
- Cell-recall is 1.0, which is meaningless for the same reason.
- The "median lead time of 168 days" is an artifact: with everything flagged, the "first crossing"
  is simply the first week the cell has any complaint history inside the 26-week window.
  **1,646 of the 3,295 leads sit exactly at the 175-day window edge.** The lead-time bar passed
  because the window is 26 weeks wide, not because the signal led anything.

We report the 168 days because the pre-registration says to report it, and we say plainly that it
is not evidence. A number that survives only because the threshold collapsed is not a measurement.

### 3.4 Calibration: honest, and nearly flat

| decile | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| predicted | .0092 | .0127 | .0129 | .0139 | .0165 | .0200 | .0213 | .0241 | .0268 | .0371 |
| observed | .0118 | .0072 | .0191 | .0163 | .0219 | .0155 | .0238 | .0203 | .0220 | .0321 |

Predicted risk spans 0.009 → 0.037 across the whole test set against a 0.019 base rate. The model
is roughly calibrated in the sense that it is not systematically over-confident — it simply has
almost nothing to say. Observed rates do trend upward with predicted risk, which is why the
signature scores *some* lift (1.48×), just far less than naive volume and nowhere near a bar.
(The full table in `results/v1/calibration.csv` carries an 11th remainder bin of 9 rows.)

## 4. Leakage, vintage and base-rate audit

- **Leak control is structural.** Every feature window is closed at `t` (`[t-k+1, t]`), and a unit
  test plants a complaint at `t+1` and at `t+50` and asserts every feature at every week ≤ t is
  bit-identical. Complaints enter on `max(DATEA, LDATE)` — the later of the two as-known-then
  dates the file carries — so nothing can enter a window earlier than either date permits.
- **The automated leakage scan flagged 95 of 3,295 leads as non-positive (2.9%)** — first crossings
  in the *same week bucket* as the recall report date. This is a real, disclosed wart, not a
  hidden one: within that one bucket, a complaint filed on Wednesday can land in a feature scored
  against a recall reported on Tuesday. It affects 2.9% of leads, it cannot affect anything at
  lead ≥ 7 days, and it does not touch any of the three failing bars. A v2 would use a
  strictly-before-`t` window.
- **Vintage discipline:** one archived vintage pair, same collection cycle, hash-pinned, no
  revised-data path — the code has no live endpoint in it. The last scored week's horizon ends
  2026-06-30, inside the 2026-07-28 labels vintage, so no scored cell-week is short of coverage.
  Recalls received in the last days before the vintage may not yet appear in the file.
- **Base-rate honesty:** precision is reported against the natural prevalence, never a balanced
  sample. The scored universe (cell-weeks with ≥1 complaint in the trailing 12 weeks) has a test
  prevalence of **1.90%**; the full (cell × week) grid, including the 59.4M cell-weeks with no
  trailing complaints, has a prevalence of **0.714%**. Excluding near-certain negatives *raises*
  prevalence, so the scored universe made the precision bar **easier** than the full grid would
  have — and it still failed by a factor of 16. The direction of that bias is stated here rather
  than left for a reviewer to find.
- **The fit is at its optimum, not half-trained.** The published gradient norm is 5.99e-08, and an
  independent IRLS/Newton solve converged in 9 iterations to the same coefficients (to 4 decimals)
  and the same log-loss (to 8). The null result is not an under-fitting artifact — checked
  precisely because a weak result invites that excuse.

## 5. Two corrections made before publication

Both were found by auditing the first completed run, both are corrections of *implementation*
against the frozen spec, and both are disclosed with their pre-fix numbers so nobody has to take
our word that the fix was not chosen for its effect on a bar.

1. **Labels are events, not rows.** The recall flat file writes one row per campaign × make/model/
   year and repeats across component sub-descriptions that canonicalize to one group, so the raw
   rows carry ~3.5× duplication of the same (cell, week) event (74,636 rows → 21,093 events). Left
   as rows, every event-level metric silently weights the most-repeated cells. Registration §4
   defines a positive by whether "a recall campaign for cell c" falls in the horizon — a set test.
   **Pre-fix test event-recall 0.3120; post-fix 0.4221.** Both are below the 0.50 bar; the fix
   moved the number toward passing and it still fails.
2. **`dirty` provenance.** The first scorecard stamped itself `dirty: true` because the results
   directory it was writing is untracked. Now counted separately. No metric affected.

Neither the signal, the labels rule, the splits, the lexicon, the crosswalk nor the bars were
touched after any result was seen. That is the whole point of the pre-registration.

## 6. What this does and does not say

**It says:** the specific signal frozen in `PRE-REGISTRATION-v1.md` §3, at the
(make, model, model-year, component-group) × week unit, does not identify NHTSA recalls well
enough to publish — it does not beat counting complaints, it cannot reach half of recalls because
half of recalls leave no complaint trail in the preceding six months, and its operating point
collapses.

**It does not say** that NHTSA complaints are uninformative. Volume alone carries 1.74× lift over
the base rate, which is real and small. It does not say a different unit of analysis, a longer
horizon, or a defect-level join would fail — those are untested, and saying anything about them
here would be exactly the unfalsifiable hand-waving this project exists to be the opposite of.

**No named claim is made about any manufacturer, model or vehicle anywhere in this report.** The
naming gate (constitution covenant 2) requires a *published, passing* track record, and there
isn't one.

## 7. Reproduce it

```bash
curl -O https://archive.theexhaust.org/raw/nhtsa-complaints/2026/07/28/1220-73acbdca6b6f.zip
curl -O https://archive.theexhaust.org/raw/nhtsa-recalls/2026/07/28/1220-efab48ed2da2.zip
python -m retrocast.nhtsa_recalls.run_v1 --complaints 1220-73acbdca6b6f.zip --recalls 1220-efab48ed2da2.zip
```

~5 minutes on a desktop CPU, no API key, no network beyond those two archived objects, no LLM
anywhere in the signal. Outputs in `results/v1/`: `scorecard.json` (the machine-readable record —
the Track Record page renders only from these), `pr_curve.csv` (2,000-point thinning of the full
curve), `lead_times.csv`, `calibration.csv`, `metrics.json`, and `cases.csv` — the per-case
receipts: all 7,806 held-out recall events with their cell, campaign numbers, whether the
signature flagged them, the first crossing, and the feature values at that crossing.

*Hostile-review record: [`HOSTILE-REVIEW-v1.md`](HOSTILE-REVIEW-v1.md).*
