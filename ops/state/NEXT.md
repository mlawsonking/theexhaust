# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the orchestrator 2026-07-28 after W-002 review (W-002 accepted; W-002b promoted ahead of W-003 by orchestrator decision).*

## Item: W-002b — Collector state-commit-back (per-collector state files)

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** close the dedupe-persistence gap W-002 filed. R1 collector jobs currently run `contents: read` and never commit health state, so any source that drifts from the *committed* baseline re-stores identical content every firing (complaints = 367 MB a pop). The design is **decided — option (a), locked in WORKPLAN W-002b. Do not re-litigate the fork; build it.**

**Read (only these):** `ops/state/WORKPLAN.md` (the W-002b entry — the locked design is the spec), `collectors/framework.py`, `collectors/ats_boards.py`, `opscore/report.py`, `opscore/weekly.py`, `.github/workflows/_collector.yml`.

**Build (per the locked design):**
1. Per-collector state files `ops/state/health/<collector>.json` as source of truth; framework `Collector` + `ats_boards` write them in R1 mode (verify mode unchanged).
2. Readers (`opscore/report.py` `_collector_board`, `weekly.py` collector-gate filing) merge `ops/state/health/*.json` with legacy `HEALTH.json` fallback; the weekly driver materializes the merged legacy view.
3. `_collector.yml`: `contents: write` + state-commit step — `git pull --rebase --autostash`, retry ≤2, commit `state(<collector>): <action> <hash12> [skip ci]`, push; 2 failed pushes → exit nonzero loudly.
4. Migrate the current `HEALTH.json` collectors node into the per-collector files.
5. Add the trivial monthly `keepalive.yml` (`git commit --allow-empty`, `[skip ci]`) for the 60-day cron-disable backstop.
6. Tests: reader-merge (two per-collector files + legacy → correct board), per-collector write path, and regression coverage for the ats-boards path.

**Accept (all, with evidence in the buildlog):**
- Suite green (`python ci/run_all.py`; interpreter: `C:\ProgramData\miniconda3\python.exe` — PATH `python` is the MS-Store shim).
- One real Actions firing **commits its state file** to `main`.
- The **next** firing of that same collector dedupes `unchanged` against the freshly *committed* baseline — the concrete proof W-002 couldn't produce. (Pick a stable source, e.g. `cms-deficiencies` or `fdic-failures`, and dispatch twice.)
- `[skip ci]` verified: state commits trigger no workflow runs.

**Catches (decision tree, don't improvise):**
- Push rejected repeatedly (race with another collector's commit) → the rebase-retry IS the mechanism; after 2 retries fail loudly. Never force-push, never widen to a shared-file design (that's rejected option (b)).
- A state commit triggers CI anyway → fix the `[skip ci]` marker placement; never disable CI.
- Rebase conflicts on a per-collector file → should be impossible by construction (distinct files); if one occurs, STOP and report the exact git state — something is wrong with the design's premise.
- R2 creds: already in the operator-box user env (W-000/W-001); Actions has them as secrets. If absent locally, `setx` persisted values need a *fresh* shell.

**Hand off:** buildlog entry with evidence → mark W-002b `done` in WORKPLAN → **draft NEXT.md for W-003** (its inherited-state notes are already in the WORKPLAN W-003 entry — carry them into the draft) → suite green → commit + push → save memory → die.
