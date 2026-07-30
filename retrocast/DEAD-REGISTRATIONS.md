# Dead registrations — the autopsy log

Retrocasts that were pre-registered and then **failed their pre-registered bars, or were abandoned**, are published here with a short autopsy: what was tried, why it didn't clear the bar, what that implies. Publishing failures is doctrine (SPEC-08 §2) — a killed index with a public autopsy builds exactly the calibrated trust the scorecard exists to build, and it is the anti-ShadowStats tell.

---

## Hospital/Care Distress — v1 · **DEAD** · registered 2026-07-29 (`d6b78c3`), scored 2026-07-30

**The claim tested.** That payroll-verified nurse staffing at a nursing home, measured over a
quarter, measurably precedes an actual-harm deficiency citation at that home in the following six
months — well enough to publish a county-level care-fragility index with receipts. Research §5
called this the cleanest retrocast in the portfolio: a hard CCN join, both sides official and
archived, no semantic matching and no LLM anywhere.

**The verdict.** Three of four pre-registered bars failed on the held-out window
(2025-03-24 … 2025-09-22; 369,750 cell-weeks, 4,643 harm events, 14,314 facilities).

| bar (registration §7) | required | measured |
|---|---|---|
| PR-AUC vs the better dumb baseline | ≥ +0.05 | **0.1771 vs 0.2526** — loses to the facility's own citation history by 0.0755 |
| precision at the operating point | ≥ 0.35 | **0.1794** (base rate 0.1357) |
| event-recall | ≥ 0.50 | **0.4605** (ceiling 0.9468 — not the binding constraint) |
| median lead, and not degenerate | ≥ 60 d | 154 d, 43.3% at the edge — **passed, legitimately** |

**Cause of death — a facility's own history beats its staffing.** The pre-registered hard baseline
was the facility's prior harm-citation rate: troubled homes stay troubled. It ranks better
(PR-AUC 0.2526) than the nine-feature staffing signature (0.1771). Two qualifications keep that
honest: the baseline wins on *ranking* only — its own precision is 0.1357, exactly the base rate,
because it flags nearly everything, so **neither** model reaches a usable operating point; and the
signature barely beats plain staffing level (0.1726 alone → 0.1771 with all nine features, **+0.0045**).

**Second cause — the instability construct did nothing.** The registration was built around
staffing *instability* and *deterioration* — the weekend drop, day-to-day variability, days below
the CMS 3.48 HPRD minimum, the quarter-over-quarter trend — on the strength of a literature that
proposes instability as a Five-Star input. At the maximum-likelihood fit those terms carry
coefficients of −0.003, +0.001, +0.005 and +0.055. At quarterly aggregation the whole model reduces
to "how low is the staffing."

**What was ruled out before calling it dead:** leakage (the staffing quarter had already ended a
minimum of 139 days before any same-week event, so leakage is arithmetically impossible; and the
planted-leak guard was found *broken*, fixed, and then re-run — see below); a flattering base rate
(the scored universe runs marginally *cooler* than the full grid, 0.135651 vs 0.136587, so the bar
was very slightly harder); a collapsed operating point (train event-recall 0.5000 exactly, test
0.4605 — it transferred); vacuous controls (55.03% of 523,787 matched controls did not cross); and
under-training (refit to a gradient norm of 2.19e-16 changes nothing to four decimals; an
independent IRLS solve agrees). Full record: [hostile review](hospital-care/HOSTILE-REVIEW-v1.md),
6/6 zeroed.

**The review found a real defect in the shared harness.** SPEC-08 §7 requires that a deliberately
planted leak be caught. Planting the cell label itself produced precision 1.0000 against a 13.6%
base rate and `leakage_scan` flagged **nothing** — a binary oracle's PR-AUC is low, and a
horizon-based label makes an oracle *lead* the event rather than coincide with it, so neither
existing rule fired. Precision against the base rate is now a fourth rule. NHTSA v1's flags are
unchanged (its precision was 0.0190). The criterion is met only because the review actually ran the
plant instead of assuming the previous index's plant generalised.

**What is genuinely limiting, and what fixes it.** CMS overwrites the deficiency file in place and
retains only ~3 inspection cycles per facility, so its 2017–2026 span is a rolling censored window —
and the censoring is *not random*: frequently-surveyed (troubled) facilities have shorter observed
histories. That is what confines v1 to a 40-week train and 27-week test window, and there is only
**one** archived vintage to work from because collection began 2026-07-28. Every vintage collected
from now on preserves label history CMS will later drop. **This is the clearest case yet for the
archival-first covenant: the reason a v2 will be better is that we started collecting.**

**What it cost and what it bought.** About five minutes of desktop CPU per scored run, one session,
no metered spend. It bought the full PBJ history in the archive (37 releases, 26 stored and 11
quarantined on a legacy header), a measured answer to whether staffing forecasts harm at this unit
of analysis, a fixed hole in the credibility engine every future index depends on, and the second
entry in this log.

**A v2 is permitted, and would be a new pre-registration** (with this attempt disclosed), not an
edit of v1. Candidates the evidence points at — none tested here, none claimed: a
facility-*quarter* unit rather than facility-week, which would stop the quarterly step function
from doing the work of a weekly signal; the prior-harm rate as a *covariate* rather than a rival, so
the question becomes what staffing adds to history rather than whether it replaces it; case-mix
adjustment, which CMS applies to its own staffing ratings and this registration did not; a longer
horizon matched to the ~110-day median gap between surveys; and re-running the whole thing in a year
against the deeper label history the archive will by then hold. Reporting:
[`hospital-care/REPORT.md`](hospital-care/REPORT.md) · scorecard:
`hospital-care/results/v1/scorecard.json`.

---

## NHTSA Shadow Recalls — v1 · **DEAD** · registered 2026-07-13 (`e3d4d84`), scored 2026-07-29

**The claim tested.** That complaint patterns at the (make, model, model-year, component-group) ×
week level measurably precede NHTSA recall campaigns, well enough to publish a lead-time
distribution with receipts. This was the project's first retrocast and its intended flagship.

**The verdict.** Three of four pre-registered bars failed on the held-out 2021–2025 window, and
the fourth passed for a reason that does not count.

| bar (registration §7) | required | measured |
|---|---|---|
| PR-AUC vs volume-only | ≥ +0.05 | **0.0280 vs 0.0331** — loses to counting complaints |
| precision at the operating point | ≥ 0.30 | **0.0190** (= the base rate) |
| event-recall | ≥ 0.50 | **0.4221** — which is also the ceiling |
| median lead | ≥ 60 days | 168 days, degenerate (half the leads sit at the window edge) |

**Cause of death — one structural fact.** **57.8% of held-out recall campaigns happened in cells
with no complaint at all in the preceding 26 weeks.** No model can flag an event it has no data
for, so the 0.50 recall bar was unreachable before a coefficient was fit — on the training window
too (coverage 0.398). Recalls are overwhelmingly initiated on evidence the public complaint stream
does not carry. The registration assumed the complaint trail leads a majority of campaigns; it
leads a minority.

**Second cause.** The five-feature signature is beaten by naive complaint volume. At the
maximum-likelihood fit, `rate_ratio` (−0.318) and `hazard_lang` (−0.150) — the two features the
registration leaned on hardest — carry *negative* weight. Self-normalizing each cell against its
own history deliberately removed the only thing that predicts a recall: that it is a high-volume
cell.

**What was ruled out before calling it dead:** leakage (structural window closure + a planted
future-complaint test), a stale or revised vintage (one hash-pinned archived pair, no live
endpoint in the code), a flattering base rate (the scored universe runs *hotter* than the full
grid — 1.90% vs 0.714% — so the precision bar was if anything easier), a mis-set threshold (the
bars are asserted equal to the registration commit in CI), and an under-trained model (gradient
norm 5.99e-08, reproduced by an independent IRLS solve). Full record:
[hostile review](nhtsa-recalls/HOSTILE-REVIEW-v1.md), 6/6 items zeroed.

**What it cost and what it bought.** About five minutes of desktop CPU per full run, one session,
and no metered spend of any kind — no LLM touches the signal. It bought
a hard, publishable measurement of how far the complaints→recalls channel actually reaches, a
credibility engine exercised end-to-end on real data at 5.9M cell-weeks, and the first entry in
this log.

**A v2 is permitted, and would be a new pre-registration** (with this attempt disclosed), not an
edit of v1. The honest candidates the evidence points at — none of them tested here, none of them
claimed: a coarser unit (make × component, dropping model-year), a longer horizon, a
defect-narrative join rather than the component taxonomy, or reframing the index as the
observational complaint-rate series that v1's own volume baseline shows carries 1.74× lift.
Reporting: [`nhtsa-recalls/REPORT.md`](nhtsa-recalls/REPORT.md) ·
scorecard: `nhtsa-recalls/results/v1/scorecard.json`.
