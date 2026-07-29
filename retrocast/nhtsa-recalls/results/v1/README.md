# results/v1 — what these files are, and what they are not

Machine-readable output of a retrocast that **failed its pre-registered bars**. Read
[`../../REPORT.md`](../../REPORT.md) first; it is the human-readable record and it explains every
number here, including the one bar that "passed" and why that does not count.

| file | contents |
|---|---|
| `scorecard.json` | the record of account: registration/freeze/code commits and their dates, hash-pinned data vintages, metrics, pass/fail against the frozen §7 bars, the fitted model, and the structural diagnostics. The Track Record page renders **only** from scorecards. |
| `metrics.json` | the signature and all three comparators (volume-only, seasonality-only, interpretable rule) side by side, plus the lead-time distribution. |
| `pr_curve.csv` | the precision/recall curve, thinned to 2,000 evenly spaced points from the full per-threshold curve. |
| `calibration.csv` | predicted vs observed by score decile (plus an 11th remainder bin of 9 rows). |
| `lead_times.csv` | every measured lead in days. Half of them sit exactly at the 175-day window edge — see REPORT §3.3. |
| `cases.csv` | the per-case receipts: all 7,806 held-out recall events, their cell and campaign numbers, whether the signature flagged them, the first crossing and the feature values there. |

## `cases.csv` is an audit trail, not a claim about any manufacturer

It names makes and models because the recall campaigns it lists are public record and because a
retrocast nobody can re-check is worthless. It is **not** a named-entity signature claim, and
three things keep it from becoming one:

1. The signature **failed**. Nothing derived from it is published as a finding.
2. The operating point degenerated to "flag everything" (REPORT §3.3), so the `flagged` column
   means only *"this cell had some complaint history inside the 26-week window"*. It carries no
   per-vehicle judgement, and `matched_controls_not_flagged` is 0 for every single row precisely
   because every control crossed the collapsed threshold too — the matched-control design of
   registration §6 is uninformative in this run, and is reported as such rather than presented as
   if it discriminated.
3. Under constitution covenant 2 the naming gate opens only after a **published, passing**
   retrocast, a frozen editorial rubric and written operator sign-off. None of those exist. No
   site surface renders this file.
