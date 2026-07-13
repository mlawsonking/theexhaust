# NHTSA Shadow Recalls — retrocast pre-registration v1

**Index:** NHTSA Shadow Recalls (vehicle safety) — the first published retrocast (gameplan §2.1).
**Status:** FROZEN. Committed **before** any result is computed (SPEC-08 §2). The results commit will cite this file's commit hash; git history makes the ordering unforgeable.
**Author:** Opus, Phase 4 · **Date:** 2026-07-13 · **Harness:** [SPEC-08](../../ops/SPEC-08-retrocast-harness.md).
**Framing (constitutional):** this is a *measurement*, never a prediction. The claim class is: "this make/model/component accumulated complaints matching the pre-recall signature of N/M historical campaigns at similarity Y (receipts linked)" — past/present tense, receipts attached, never "will be recalled."

> Nothing in this document has been run against the data. Its purpose is to commit the signal, the labels, the controls, the splits, and the pass/fail bars *ahead* of results, so the published precision/recall cannot be a product of hindsight. If a change is needed **after results are seen**, that is a *new* pre-registration (v2) and the prior attempt is disclosed in [DEAD-REGISTRATIONS.md](../DEAD-REGISTRATIONS.md).

---

## 0. Why this index first
Cleanest falsification of the founding thesis: both the signal (consumer complaints) and the ground truth (recall campaigns) are official, free, bulk, and **already archived** — no scraping, no gray corpus, one self-consistent government ecosystem, and a hard make/model/year/component join (no LLM entity resolution required for the core retrocast). Prior art establishes the task is tractable (see §7). The headline artifact — a **lead-time distribution** ("the complaint signature crossed threshold a median of L days before the official recall") — is the strongest press hook in the portfolio.

## 1. Data — retrocast-of-record only
Both sides are the **archived NHTSA ODI flat-file vintages** snapshotted by collector C4 (`nhtsa-complaints` / `nhtsa-recalls`, SPEC-01), **never live endpoints** (constitution: government-continuity / stale-data posture; the Oct-2025 appropriations lapse is exactly why).

- **Signal source — Complaints:** NHTSA ODI `FLAT_CMPL` (verified live 2026-07-13, HTTP 200, ~367 MB zip). Fields used (ODI complaint layout; exact names pinned to the archived `CMPL.txt` record-layout at C4 build): odino (id), make/model/model-year, component description, **date received** (as-known-then), crash/fire flags, injuries/deaths, failure narrative. Only complaints with **received-date ≤ measurement time t** are ever used.
- **Ground truth — Recalls:** NHTSA ODI recalls flat file (recall campaigns). Labels file recorded with **source URL + vintage date + sha256** in the results `scorecard.json`. Fields: campaign number, make/model/model-year, component, **recall report-received date** (the event date), defect/consequence text. *Note: the recalls flat-file URL used in an earlier probe (`.../rcl/FLAT_RCL.zip`) 404'd on 2026-07-13; the correct current path is pinned at C4 build via the NHTSA ODI file index. This does not affect the design below.*

## 2. Unit of analysis
A **(make, model, model-year, component-group) × week** cell. Component grouping uses the NHTSA component taxonomy at its top level (e.g., "power train", "electrical system", "air bags"), frozen in the workbook. Weeks run over 2015-01 → 2025-12 (bounded by archived vintage coverage).

## 3. Signal construction (frozen)
For each cell and each week `t`, features computed **only from complaints with received-date ≤ t** (strict leak control):
1. `n_trailing` — complaint count in the trailing W = 12 weeks.
2. `rate_ratio` — `n_trailing` ÷ the cell's own trailing-52-week baseline mean (self-normalized, so "companies/models with more complaints" doesn't confound).
3. `accel` — week-over-week change in `n_trailing` (the "collapse/spike" shape).
4. `severity_frac` — fraction of the trailing complaints flagged crash OR fire OR injury/death.
5. `hazard_lang` — fraction of trailing complaint narratives matching a **frozen** hazard-term lexicon (committed in the workbook; e.g., stall, fire, brake failure, steering loss). Deterministic n-gram match, no LLM in the core signal.

The **signature score** `S(cell, t)` is a **logistic regression** over these five features (coefficients learned on the train window only, §5). A transparent threshold rule on `rate_ratio`+`accel`+`severity_frac` is pre-registered as the **fallback/interpretable model** and is the one whose coefficients are human-inspectable in the report. No feature uses the recall record, the recalled-component label, or any post-`t` information.

## 4. Labels
Cell×week `(c, t)` is **positive** iff a recall campaign for cell `c` (matching make/model/year and component-group) has report-received date in the horizon `(t, t + H]`, with **H = 26 weeks** (the prediction/measurement horizon). All other cell-weeks are negatives. The recall date is taken from the recalls vintage as-archived (no later revisions).

## 5. Temporal split & leak controls (explicit)
- **Train:** cell-weeks whose horizon ends on/before **2020-12-31** (signature coefficients + operating threshold learned here only).
- **Test (held-out):** cell-weeks from **2021-01-01 → 2025-12-31**. Reported metrics are **test-only**.
- **Leak controls (each independently auditable in the hostile review, SPEC-08 §5):** (a) features use complaints received ≤ t only; (b) vintage-only — the flat file as archived, never as-revised; (c) the operating threshold is fixed on train and **frozen before scoring test**; (d) no cell-week within H weeks of the train/test boundary is scored (horizon spillover guard); (e) lead-time is measured from the **first** pre-recall threshold crossing using only ≤-crossing-time information.

## 6. Controls, base rate, and the mandatory dumb baseline
- **Realistic base rate:** metrics are computed against the **natural** prevalence of positive cell-weeks (recalls are rare), **never a balanced/downsampled set**. Precision is reported against that real prior. (SPEC-08 §5 base-rate-honesty.)
- **Matched controls:** for the per-case receipts, each flagged recall is shown against matched non-recalled cells (same make-segment + model-year band) that did **not** cross threshold.
- **Dumb baselines (must be beaten):** (i) **volume-only** — `n_trailing` alone, no rate/accel/severity; (ii) **seasonality-only** — calendar-week base rate. The signature must beat both on the held-out set (§7 bars). If it does not, the index does **not** publish as a signature (it may still publish the observational complaint-rate series).

## 7. Pre-registered pass thresholds (frozen — the publish gate)
Computed on the **held-out** window at the **train-chosen** operating point, against the real base rate:
- **PR-AUC** of the signature **≥ volume-only PR-AUC + 0.05 absolute** (the signature must add signal over naive volume), AND
- at the primary operating point: **precision ≥ 0.30** while **recall ≥ 0.50** of recalled cells flagged, AND
- **median lead-time ≥ 60 days** (first threshold crossing → official recall date) over true-positive recalls, with the **full lead-time distribution** (not just the median) published, AND
- calibration: predicted-vs-observed within the published band across deciles (miscalibration is disclosed, not hidden).

Rationale for the numbers (set from domain priors + prior art, **before** data): vehicle-complaint signals are noisier than the medical-device recall models that reported ~75% sensitivity / ~100% specificity at 12-month lead (Zhu et al. and the RECALL-MM 2025 line), so bars are deliberately conservative; a rare-event precision of 0.30 against the true prior is a strong, honest result. **Failing these bars is a publishable outcome** (autopsy in DEAD-REGISTRATIONS.md), not a reason to move the bars.

## 8. Prior art (replicate-then-run; this task is not novel)
Logged per SPEC-08 §6 / the constitution's prior-art rule; see [prior-art-scan.md](prior-art-scan.md). Summary: complaint→recall forecasting is established (RECALL-MM multimodal recall dataset, 2025; documented ML on unstructured NHTSA complaints to forecast failing components; medical-device recall ML). The Exhaust's contribution is **not** methodological novelty — it is **live + public + a published precision/recall + lead-time scorecard with receipts**, which no live public entity in this lane maintains (research §8, §13.4). This index *replicates a known-tractable result and then runs it forever.*

## 9. Outputs (SPEC-08 §3) and the publish gate
`retrocast/nhtsa-recalls/results/v1/` will hold: the full PR curve, the lead-time distribution, the calibration plot, headline metrics with CIs, and the per-case scored table (the receipts). `scorecard.json` records this file's commit hash, the data vintages+hashes, the metrics, and pass/fail vs. §7. The report page (`REPORT.md`) is written to survive the **hostile-review checklist** (SPEC-08 §5) — leakage hunt, vintage audit, base-rate honesty, control validity, threshold archaeology, overclaim scan — every item zeroed by one adversarial R2 session before the ⚑ operator launch gate (LLC + insurance + sign-off, BUILD-03) opens.

---
*Frozen 2026-07-13. Any change after results are seen ⇒ v2 + disclosure in DEAD-REGISTRATIONS.md.*
