# Dead registrations — the autopsy log

Retrocasts that were pre-registered and then **failed their pre-registered bars, or were abandoned**, are published here with a short autopsy: what was tried, why it didn't clear the bar, what that implies. Publishing failures is doctrine (SPEC-08 §2) — a killed index with a public autopsy builds exactly the calibrated trust the scorecard exists to build, and it is the anti-ShadowStats tell.

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
