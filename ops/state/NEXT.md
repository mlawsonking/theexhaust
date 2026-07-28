# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the W-002 worker at hand-off, 2026-07-28.*

## Item: W-003 — Alarms + weekly session live

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** the watching layer stops being inert — healthchecks alarms fire on a stopped collector, ntfy delivers to the phone, and the weekly R2 gate-report session runs headless and pulses. The machine starts watching itself.

**Read (only these):** `opscore/alarms.py`, `opscore/weekly.py`, `ops/SPEC-03`, `ops/playbooks/weekly-ops.md`.

**State you inherit (don't re-derive):**
- **The R1 fleet is live (W-002):** 6 scheduled collector workflows in Actions, green, writing to R2. Each already exports `HC_<COLLECTOR>` into `env:` (see `_collector.yml`) — they light up the moment you create the checks + secrets. Only **`HC_NHTSA_RECALLS`** exists so far (it pinged successfully from Actions); `HC_ATS_BOARDS` is *referenced by code* (ats-boards main reads it) but the secret doesn't exist yet.
- **ntfy:** topic `theexhaust-75Z`, phone-confirmed. `NTFY_ALARM/GATE/PULSE` are set as **Actions** secrets (all = the one topic). **The weekly session runs on the operator box (R2 runtime), so it needs `NTFY_ALARM/GATE/PULSE` in LOCAL env** — `opscore/alarms.py` reads them from `os.environ`. Persist them via `setx` (a fresh process inherits; see env note below) OR source a file.
- **healthchecks:** one check exists (the `HC_NHTSA_RECALLS` UUID `2b6e0c92-f34a-445c-83e8-6006c2d49fe8`). SPEC-03 §1 wants ≤18 checks, grace = cadence × over-schedule. Creating the rest may want a healthchecks.io API token (operator errand if so — file a `vtask` blocker, don't hand-create 6 checks silently if the API is cleaner).
- **⚑ Consider W-002b first (or fold in):** the state-commit-back gap (see WORKPLAN `W-002b`, HIGH). The SPEC-02 §2 weekly session is one candidate owner of state commits — if you wire the weekly session to commit `HEALTH.json`, you partially close W-002b. Decide with the orchestrator whether W-003 absorbs it or it stays separate; **don't silently leave it unaddressed** now that the fleet is storing.

**Do (SPEC-03):**
1. healthchecks checks per SPEC-03 §1 budget (per-collector + logical `warn`/`ats-boards`), grace = cadence × over-schedule; add each `HC_<COLLECTOR>` as an Actions secret so the live workflows ping them.
2. ntfy topics into **local env** (weekly session) + confirm the Actions secrets (already set).
3. Kill-one-collector drill (SPEC-03 §6): disable one firing, confirm healthchecks→ntfy alarm within grace.
4. Schedule the weekly R2 session (Windows Task Scheduler → `claude -p` per SPEC-02 §2 — **operator action**; file a `vtask` blocker with the exact command if you can't create the task from the session).
5. `python -m opscore.weekly` once for real → confirm the pulse lands on the phone.
6. Wire the futility-clause auto-gate (2027-12-31 from `CALENDAR.md`) into the weekly driver + a test.

**Accept:** SPEC-03 §6 drill items pass; one real weekly report compiled + pulsed to the phone; futility wiring tested offline; suite green (`python ci/run_all.py`).

**Catches (decision tree, don't improvise):**
- ntfy delivery fails → the topic string is the only auth; regenerate + update both local env and Actions secrets (operator ping via `vtask` if his action is needed).
- healthchecks free-tier limits hit → group per SPEC-03 §1 budget; never drop an outcome-based ping to fit.
- Task Scheduler / API-token needs the operator → `vtask add` a precise blocker and continue with what's severable; a precise stop is a successful session.

**Env/interpreter note (operator box):** working Python is `C:\ProgramData\miniconda3\python.exe` (boto3 installed); `python`/`py` on PATH are only the MS-Store shim. `setx` persists to the registry but only a **freshly launched** process sees it — a same-process continuation must source a creds file. R2 creds already persisted to user env (W-000); the W-000 scratch `r2-creds.env` is session-scoped (gone next session).

**Hand off:** buildlog entry with evidence → mark W-003 in WORKPLAN → draft NEXT.md for **W-004** (C2 WARN tranche 1) → `python ci/run_all.py` green → commit → save memory → die.
