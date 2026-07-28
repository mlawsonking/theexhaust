# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the W-003 worker at hand-off, 2026-07-28. The orchestrator may re-point this before the next worker starts.*

## Heads-up: W-003 is `partial`, not done — but it is NOT your job
The W-003 code + live weekly session are done and green (futility auto-gate, `NTFY_*` in User env, one real pulsed report). Its **remaining acceptance is pure operator infra**, filed as Vikunja blockers — **no worker session is needed** for either:
- **#212** — mint a healthchecks.io API token, add the ntfy integration, run `python ops/setup/healthchecks_setup.py --apply` (creates the 6 dead-man checks + sets `HC_<COLLECTOR>` secrets), then the 1-min `/fail` drill in `ops/playbooks/kill-drill.md`. This is what makes SPEC-03 §6 pass.
- **#213** — review + run `ops/setup/schedule-weekly-session.ps1` to schedule the Mondays weekly session (a permission-posture + subscription decision is baked in as comments).

Proceed to W-004 below.

---

## Item: W-004 — C2 WARN, tranche 1 (top-10 states)

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** the WARN Watch corpus begins to archive. Ten states' WARN (Worker Adjustment and Retraining Notification) notice pages become collectors, archiving on schedule to R2 — the perishable ground truth behind the Shadow Layoffs observational flagship. Heterogeneous by construction: each state publishes differently.

**Read (only these):** `ops/SPEC-01` (the C2 row + §4 covenant column), `docs/02-RESEARCH.md` **§3-① the WARN paragraph ONLY** (the queue cites it; do not read the doc wholesale), `collectors/cms_deficiencies.py` (the CSV-adapter pattern), and `collectors/ats_boards.py` (the **one-collector-many-targets-one-heartbeat** pattern you'll likely mirror — see the heartbeat note below).

**State you inherit (don't re-derive):**
- **The fleet framework is mature:** `collectors/framework.py` has `select_storage` (R2 in prod, LocalFS in verify), `CsvSchema`/`ZipTabSchema`/`JsonSchema`, and `Collector` with content-hash dedupe + drift-streak (3× → auto-pause + `needs_gate`) + volume-alarm + per-collector state files `ops/state/health/<c>.json` (W-002b). HTML/PDF states won't fit the existing schema types — the WORKPLAN's steer is **store raw + parse what's parseable; parsing completeness is per-state manifest metadata, not a gate**.
- **Actions fleet pattern (W-002):** each collector is a `collect-<name>.yml` caller of the reusable `_collector.yml` (standard runner, no LLM key, `contents: write` at the caller — the repo default token perm is `read`, so a missing `permissions:` block breaks the reusable's state-commit push with a `startup_failure`; W-002b's scar). Odd-minute, staggered, 2–4× over-scheduled crons; `workflow_dispatch`; per-collector `concurrency`.
- **Heartbeat design — DO NOT create 10 checks.** SPEC-03 §1 wants WARN grouped into **one shared `warn` logical heartbeat** (free tier = 20 checks; §1 budget ≤18). Cleanest: **one `collect-warn.yml` running all states in a fleet loop** (mirror `ats_boards.py`: many targets, one `HC_WARN` heartbeat that pings OK only if every state's fetch was clean / `/fail` on any quarantine), rather than 10 separate workflows. Then add `HC_WARN` to `_collector.yml`'s `env:` and it lights up once the operator provisions it (extend `opscore/healthchecks.py` to emit the logical `warn` check, or hand-create it — coordinate with #212). This keeps you inside the check budget and the alarm taxonomy.
- **403 ladder (W-001/W-002 findings):** every source served 200 to Azure runners in W-002, but state portals are a new surface. Use the framework's `DEFAULT_UA` (bare `Python-urllib` is 403'd by Cloudflare Bot Fight Mode; `DEFAULT_UA`/requests are fine). If a state portal blocks datacenter IPs → 403-ladder step (b) is the operator box; log it, don't evade.
- **Working Python on the operator box:** `C:\ProgramData\miniconda3\python.exe` (PATH `python`/`py` are the MS-Store shim). Full suite = `python ci/run_all.py`.

**Do (WORKPLAN W-004):**
1. Per-state WARN collectors for **CA, NY, TX, WA, IL + 5 more by layoff volume** (pick from research §3-①). **Primary state sources only** — aggregators are cross-checks, never sources (covenant).
2. Per-state schema contract each (HTML/PDF → store raw + parse what's parseable; record parse completeness in the manifest).
3. One shared `warn` logical heartbeat (see the heartbeat note — one fleet workflow, not ten).
4. Wire the Actions schedule(s) per the W-002 pattern; verify at least one real firing archives to R2.

**Accept:** 10 states archiving on schedule; **≥1 real WARN notice visible end-to-end in a stored snapshot** (pull it back from R2 and show the row/field); suite green (`python ci/run_all.py`); new collectors land with tests; covenant guard still clean.

**Catches (decision tree, don't improvise):**
- A state portal blocks datacenter IPs → 403-ladder step (b) operator box, log it, keep the other nine.
- A state is JS-walled or CAPTCHA'd → **STOP that state**, file a `source` gate, continue the other nine (never burn a session on one state; never evade a control).
- Format drifts mid-tranche → quarantine semantics already handle it (store + flag, 3× → auto-pause + gate).
- A source is on the do-not-collect register or a ToS surface appears → STOP, gate, do not collect.

**Hand off:** buildlog entry with evidence (name the state whose real notice you round-tripped from R2) → mark W-004 in WORKPLAN → draft `NEXT.md` for **W-005** (fleet-green + BUILD-01 acceptance; note its adversarial-review scope now includes the workflow YAMLs + W-002b state machinery + the W-003/W-004 additions) → `python ci/run_all.py` green → commit → save memory → die.
