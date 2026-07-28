# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the W-002b worker at hand-off, 2026-07-28.*

## Item: W-003 — Alarms + weekly session live

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** the watching layer stops being inert — healthchecks alarms fire on a stopped collector, ntfy delivers to the phone, and the weekly R2 gate-report session runs headless and pulses. The machine starts watching itself.

**Read (only these):** `opscore/alarms.py`, `opscore/weekly.py`, `ops/SPEC-03`, `ops/playbooks/weekly-ops.md`.

**State you inherit (don't re-derive):**
- **The R1 fleet is live and self-persisting (W-002 + W-002b):** 6 scheduled collector workflows, green against R2, and each now **commits its own `ops/state/health/<collector>.json`** back to main on a real state change (`[skip ci]`) so the dedupe baseline persists. `_collector.yml` already exports `HC_<COLLECTOR>` into `env:` — checks light up the moment you create them + add the secrets. Only **`HC_NHTSA_RECALLS`** exists (it pings from Actions).
- **Health is now merged:** `opscore.report.merged_health(root)` unions `ops/state/health/*.json` (authoritative) + legacy `HEALTH.json` (fallback). `report.py`/`weekly.py` read it; **`weekly.run_weekly` re-materializes the legacy `HEALTH.json`** from the per-collector files — that write is part of what the weekly session commits, so the weekly session needs repo write (it runs on the operator box with a normal git remote, not a workflow token — fine).
- **ntfy:** topic `theexhaust-75Z`, phone-confirmed. `NTFY_ALARM/GATE/PULSE` set as **Actions** secrets (all = the one topic). The weekly session runs on the **operator box**, and `opscore/alarms.py` reads `NTFY_*` from `os.environ` — so those three must be in **local user env** (persist via `setx`, a fresh process inherits; a same-process continuation must source a file).
- **healthchecks:** one check exists (`HC_NHTSA_RECALLS` UUID `2b6e0c92-f34a-445c-83e8-6006c2d49fe8`). SPEC-03 §1 wants ≤18 checks, grace = cadence × over-schedule. If creating the rest is cleaner via a healthchecks.io API token, that's an operator errand — file a `vtask` blocker, don't hand-create silently.
- **Repo token default is `read`:** any *new* workflow that must push declares `permissions: contents: write` at the **caller** level (a reusable's request can't exceed the caller's grant — this bit W-002b). The kill-one-collector drill likely just disables a schedule + watches healthchecks, so may not need this.

**Do (SPEC-03):**
1. healthchecks checks per SPEC-03 §1 budget (per-collector + logical `warn`/`ats-boards`), grace = cadence × over-schedule; add each `HC_<COLLECTOR>` as an Actions secret so the live workflows ping them.
2. `NTFY_ALARM/GATE/PULSE` into **local user env** (weekly session) + confirm the Actions secrets.
3. Kill-one-collector drill (SPEC-03 §6): disable one firing, confirm healthchecks→ntfy alarm within grace.
4. Schedule the weekly R2 session (Windows Task Scheduler → `claude -p` per SPEC-02 §2 — **operator action**; file a precise `vtask` blocker with the exact command if you can't create the task from the session).
5. `python -m opscore.weekly` once for real → confirm the pulse lands on the phone (note: this now also rewrites `HEALTH.json` from the per-collector files — commit it).
6. Wire the futility-clause auto-gate (2027-12-31 from `CALENDAR.md`) into the weekly driver + a test.

**Accept:** SPEC-03 §6 drill items pass; one real weekly report compiled + pulsed to the phone; futility wiring tested offline; suite green (`python ci/run_all.py`).

**Catches (decision tree, don't improvise):**
- ntfy delivery fails → the topic string is the only auth; regenerate + update both local env and Actions secrets (operator ping via `vtask` if his action is needed).
- healthchecks free-tier limits hit → group per SPEC-03 §1 budget; never drop an outcome-based ping to fit.
- Task Scheduler / API-token needs the operator → `vtask add` a precise blocker and continue with what's severable; a precise stop is a successful session.

**Env/interpreter note (operator box):** working Python is `C:\ProgramData\miniconda3\python.exe` (boto3 installed); `python`/`py` on PATH are only the MS-Store shim. `setx` persists to the registry but only a **freshly launched** process sees it. R2 creds already persisted to user env (W-000).

**Hand off:** buildlog entry with evidence → mark W-003 in WORKPLAN → draft NEXT.md for **W-004** (C2 WARN tranche 1; its inherited-state notes are in the WORKPLAN W-004 entry) → `python ci/run_all.py` green → commit → save memory → die.
