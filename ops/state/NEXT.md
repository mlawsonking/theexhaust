# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the W-005 worker at hand-off, 2026-07-28. The orchestrator may re-point this before the next worker starts.*

## Not your job (no worker needed)

- **BUILD-01 acceptance** is the **orchestrator's**: run the adversarial review (scope: every collector since the last pass + `_collector.yml` and all callers + `keepalive.yml` + the W-002b state machinery + the WARN fleet/seed + the W-005 manifest changes), then mark BUILD-01 accepted **on/after 2026-08-04 conditional on `python ops/fleet_green.py` exiting 0**. That command is the entire remaining evidence for SPEC-01 §6 criterion 1 — one command, no session.
- **Operator residuals:** ⚑ **#212** healthchecks provisioning (mint an HC API token → `python ops/setup/healthchecks_setup.py --apply` → 1-min `/fail` drill; provisions 7 checks incl. `HC_WARN`). ⚑ **#213** weekly-session scheduler (`ops/setup/schedule-weekly-session.ps1`). Until #212 lands, heartbeats are inert and fleet-green evidence comes from Actions runs + manifests + committed state (`ops/fleet_green.py` says so in its own output).

---

## Item: W-006 — NHTSA retrocast: run → hostile review → ⚑ launch gate

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** the flagship credibility artifact. Run the **pre-registered** NHTSA recalls retrocast against archived vintages, produce `results/v1/`, then walk the hostile-review checklist to zero. This is the first thing the project publishes a number from, so the pre-registration is law and the review is adversarial by design.

**Read (only these):** `retrocast/nhtsa-recalls/PRE-REGISTRATION-v1.md` (**the law — signal construction, thresholds, bars, all frozen**), `retrocast/harness.py`, `ops/SPEC-08` **§3 (harness contract) + §5 (hostile-review checklist)**.

**State you inherit (don't re-derive):**
- **The corpus is in R2 and is the retrocast-of-record** — never fetch live endpoints for this. `raw/nhtsa-complaints/2026/07/28/` holds two 368 MB `FLAT_CMPL.zip` vintages (51 tab-delimited fields, ~2.23 M rows); `raw/nhtsa-recalls/2026/07/28/` holds three `FLAT_RCL_POST_2010.zip` objects across two distinct hashes (29 fields, 243 k rows). Manifests carry the sha256 of every one; **34/34 manifest hashes verified against their object keys on 2026-07-28**.
- **Pull vintages through the custom domain** `archive.theexhaust.org` (egress covenant — never raw `r2.dev`); the W-001 restore drill proves that path (sha256 + schema match).
- **Working Python:** `C:\ProgramData\miniconda3\python.exe`; full suite = `python ci/run_all.py` (9 steps, currently green). R2 creds are in the operator-box User env.
- **Compute:** the operator box + its RTX 4080 is the sanctioned heavy-compute runner (Actions has a 6-hr job cap; a 368 MB × 2.2 M-row join belongs local). **No metered LLM anywhere in this** — signal construction is deterministic per the frozen spec.

**Do (SPEC-08 §3):**
1. **Freeze the hazard lexicon in the workbook first**, then construct the signal exactly as pre-registration §3 specifies — deterministic, no tuning against outcomes.
2. Run the harness over archived vintages only; emit `results/v1/` + `scorecard.json` **citing the registration commit** (the git ordering IS the proof the registration predates the results — verify it does).
3. Write `REPORT.md` (what was measured, precision/recall/calibration, the dumb baseline it must beat).
4. **Then a SEPARATE hostile-review pass** (SPEC-08 §5) to zero: leakage, vintage discipline, base rate, dumb baseline, threshold archaeology, overclaim.

**Accept:** scorecard validates; the registration commit demonstrably predates the results; hostile checklist zeroed; suite green. **Then the ⚑ operator launch gate** (TX LLC + insurance decision + sign-off) — file it with `vtask add` when reached, don't assume it.

**Catches (decision tree, don't improvise):**
- **Bars fail → that is a publishable outcome, not a failure of the session.** Write the dead-registration autopsy; a v2 pre-registration is allowed only with the disclosure the doctrine requires. Never retune the frozen spec to make a bar pass — that is threshold archaeology and the hostile review exists to catch it.
- Component-taxonomy mismatch vs the layout doc → freeze the mapping in the workbook and note it; never bend the spec silently.
- Compute too heavy for Actions → operator box (expected; note the switch).
- Anything that tempts a live fetch of NHTSA data → STOP; the archived vintages are the record (government-continuity posture).

**Hand off:** buildlog entry with evidence → mark W-006 in WORKPLAN → draft `NEXT.md` for **W-007** (BUILD-04 launch surfaces) → `python ci/run_all.py` green → commit → save memory → die.
