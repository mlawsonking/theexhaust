# SPEC-08 — The retrocast harness

*Contract for the credibility engine. One falsification protocol, reused by every index. The constitution's retrocast gate is enforced here, in machinery.*

## 1. Inputs (per index, from its workbook)

- **Signal spec:** exact construction of the candidate series from archived raw data (code ref + parameters). Runs only against the **retrocast-of-record** (archived flat files/vintages, never live endpoints).
- **Ground truth:** named labels file (source + vintage + hash) — e.g., NHTSA recall archive, CMS deficiency citations, Sheps closure list, layoffs.fyi export.
- **Control design:** matched non-event population (how matched, stated).
- **Temporal splits:** signature learned on the train window only; scored on a held-out later window. **Leak controls are explicit:** no feature may use information post-dating the moment of measurement; vintage data only (as-known-then, not as-revised-later).
- **Pass thresholds:** the P/R and lead-time bars the index must clear to publish — written in the workbook **before** any result is computed.

## 2. Pre-registration (the anti-p-hacking receipt)

The full spec (signal, labels hash, controls, splits, thresholds) is committed to the public repo **before** the harness computes a single result; the publication cites that commit. Git history makes the ordering unforgeable — this is the field-wide differentiator (research §13.4) made mechanical. If the spec must change after seeing results, that is a *new* pre-registration, and the report discloses the prior attempt (a dead-registration log — failed retrocasts are published too; a killed index with a public autopsy builds exactly the trust the scorecard exists to build).

## 3. Outputs (standard, every retrocast)

- `retrocast/results/{version}/`: precision/recall curve (full curve, not one point), lead-time distribution, calibration plot, headline metrics with CIs, per-case scored table (the receipts).
- `scorecard.json` — machine-readable: registration commit, data vintages, metrics, pass/fail vs. pre-registered bars. The Track Record page (BUILD-10) renders **only** from scorecard JSONs.
- The retrocast report page — human-readable, methodology-linked, hostile-reviewer-proof.

## 4. Forward-validation mode (layoffs-class indexes)

Same harness, labels accrue with time: the signal publishes as *observation* from day one; every arriving label (a WARN notice, a confirmed layoff) scores the trailing signal automatically; the scorecard updates on a fixed cadence with "n labels so far, provisional P/R" clearly marked provisional until a pre-registered n is reached. No signature language until the pre-registered bar clears — the naming gate reads this field.

## 5. The hostile-review checklist (pre-publication, one adversarial R2 session)

Leakage hunt (any feature peeking past measurement time?) · vintage audit (revised-data contamination?) · base-rate honesty (is precision reported against realistic priors, not balanced samples?) · control validity (would a dumb baseline — volume alone, seasonality alone — score the same?) · threshold archaeology (do published bars match the registration commit?) · overclaim scan of the report prose against never-predict-only-measure. Every item zeroed or the publication gate does not open.

## 6. Standing rules

- The **prior-art scan** (constitution): before any novel join/index is pre-registered, a 15-minute scholarly sweep (Scholar/NBER/AEA/SSRN) is logged in the workbook — J-14 died as a published null result someone had already run.
- A methodology change on a published index = new version = **full backtest republication** under the new version (doctrine), old scorecards preserved.
- Official-number chaining (the Google-Flu-Trends clause) is part of this spec's surface: the divergence detector (SPEC-03) reads the calibration bands published here.

## 7. Acceptance criteria (BUILD-03, first exercised by NHTSA)

- Registration commit demonstrably predates results in git history.
- A deliberately-leaked feature planted in a test run is caught by the checklist procedure.
- A dumb-baseline comparison is present in the published report.
- `scorecard.json` validates against schema; the report page renders from it.
- The dead-registration log exists (empty is fine; the page exists).
