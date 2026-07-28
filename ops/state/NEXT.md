# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the W-004 worker at hand-off, 2026-07-28. The orchestrator may re-point this before the next worker starts.*

## Operator residuals still open (NOT your job — no worker needed)
- **#212** healthchecks provisioning (mint an HC API token → `python ops/setup/healthchecks_setup.py --apply` → 1-min `/fail` drill). This now provisions **7 checks incl. `HC_WARN`**; until it runs, collector heartbeats (incl. warn) are inert, so "green days via heartbeats" can't be measured — fall back to manifests/Actions-run history (see below).
- **#213** schedule the weekly session (`ops/setup/schedule-weekly-session.ps1`).
- **Push + optionally dispatch `collect-warn.yml`** — W-004 committed but did not push (not unprompted). The WARN Actions path hasn't run in Actions yet (mirrors the proven ats-boards pattern); verifying it is part of *your* fleet-green.

---

## Item: W-005 — Fleet-green + BUILD-01 acceptance

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** close **BUILD-01** formally. Prove the whole archival fleet runs green, drifts safely, honors the covenants, and costs ~nothing — then hand it to the orchestrator for the constitutional adversarial-review + acceptance.

**Read (only these):** `ops/SPEC-01` **§6 (acceptance) + §4 (covenant column)**, `docs/04-BUILDLOG.md` (skim the W-001…W-004 entries for what's live), `ops/state/BUDGET.json` (current storage line).

**State you inherit (don't re-derive):**
- **Enabled collectors (all self-scheduled in Actions, W-002/W-002b):** cms-deficiencies, cpsc-recalls, nhtsa-recalls, nhtsa-complaints, fdic-failures (framework `Collector`s) + ats-boards (fleet) + **warn (fleet, 10 states — NEW in W-004)**. Each per-collector job commits its own `ops/state/health/<c>.json` back to main (`[skip ci]`).
- **The WARN fleet is new since the last adversarial pass** — `collectors/warn.py`, `collectors/seed_warn.json`, `collect-warn.yml`, and the `_collector.yml` warn-branch are all in your review scope (the WORKPLAN already widened W-005 to the workflow YAMLs + W-002b state machinery — add the WARN fleet).
- **WARN Actions firing not yet proven in Actions:** W-004's real-R2 firing was local (round-tripped through `archive.theexhaust.org`). **Dispatch `collect-warn.yml`** (`gh workflow run collect-warn.yml`) and confirm it stores to R2 + commits `warn.json` state green — this is a fleet-green item, and it exercises the new reusable-workflow `warn` branch for the first time.
- **WARN dedupe caveat:** 6 of 10 WARN sources dedupe cleanly; **4 (NY, WA, MD, WI) carry per-request-volatile HTML** (ViewState/tokens) and re-store every firing (~127 MB/yr, within the free tier). This is expected, not a drift/quarantine. A content-normalization pre-hash to restore their dedupe is a **WORKPLAN candidate** (consider whether it belongs in BUILD-01 acceptance or a later cleanup).
- **`HC_WARN` + 6 other heartbeats are inert until #212.** SPEC-01 §6 wants "green 7 consecutive days (heartbeats + manifests)." If #212 isn't done, evidence green via **Actions run history + per-day `manifest.json` + committed `health/<c>.json`** instead of healthchecks, and say so; don't block BUILD-01 on the operator's #212.
- **Working Python:** `C:\ProgramData\miniconda3\python.exe`; full suite = `python ci/run_all.py` (now 9 steps). R2 creds are in the operator-box User env.

**Do (SPEC-01 §6):**
1. **7-consecutive-green-days evidence** across enabled collectors — heartbeats if #212 is live, else Actions runs + manifests + committed state. List any collector short of 7 days (the archive clock started W-001/W-002/W-004 at different times → several will be < 7 days; that's fine, list them).
2. **Injected-drift drill:** inject fake schema drift into ONE framework collector (e.g. a bad `cms-deficiencies` payload) → confirm it quarantines + alarms + does NOT pollute `raw/` + 3× → auto-pause + gate (the framework path already; prove it end-to-end, don't just cite the unit test). (WARN "drift" = fetch-failure quarantine, a different path — note it, the CsvSchema drill is the SPEC one.)
3. **Covenant review** of every collector vs SPEC-01 §4 (honest UA, no circumvention, robots at onboarding, dedupe-before-store, 403-ladder) — a table in the buildlog.
4. **C7 Kroger confirmed dark** (no `kroger` collector exists; covenant guard enforces) — state it.
5. **Storage projection into `BUDGET.json`** — sum R2 usage, project $/mo, confirm < $5/mo bar (WARN adds only tens of MB/yr).

**Accept:** SPEC-01 §6 checklist fully evidenced in the buildlog → hand to the **orchestrator** for the constitutional adversarial review over all collectors since the last pass **+ the workflow YAMLs (`_collector.yml` + all callers + `keepalive.yml`) + the W-002b state machinery + the WARN fleet/seed** → BUILD-01 marked accepted. (Workers don't self-accept BUILD items.)

**Catches (decision tree, don't improvise):**
- Any collector < 7 green days → BUILD-01 stays open **for that collector**; accept the rest, list the stragglers (don't hold the whole build for the newest collector).
- The injected-drift drill risks polluting real `raw/` → run it against a LocalFS/`--verify` backend or a throwaway prefix; never inject into the live R2 `raw/` tree.
- A covenant violation surfaces in review → that fails the build regardless of whether the code works (covenants are code review); fix or gate before acceptance.

**Hand off:** buildlog entry with evidence → mark W-005 in WORKPLAN → the orchestrator runs the adversarial review + marks BUILD-01 accepted → draft `NEXT.md` for **W-006** (NHTSA retrocast: run → hostile review → ⚑ launch gate) → `python ci/run_all.py` green → commit → save memory → die.
