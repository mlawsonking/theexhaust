# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the W-001 worker at hand-off, 2026-07-28.*

## Item: W-002 — Actions cron fleet + the scheduled complaints delta

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** the 6 collectors run **scheduled in R1 (GitHub Actions)** with the mandatory cron-drift defenses, writing to the real R2 backend (BUILD-00/W-001 green). Confirm dedupe on re-fire. This makes the archive self-sustaining without the operator box.

**Read (only these):** `ops/SPEC-02` §1 (R1 contract — over-scheduling, odd minutes, concurrency, job contract), `.github/workflows/ci.yml` (the working Actions pattern), `collectors/nhtsa.py` (the complaints/ recalls entry points).

**State you inherit from W-001 (don't re-derive):**
- **R2 is live and the first full vintage of all 6 collectors is already in R2** (`raw/<collector>/2026/07/28/…` + manifests). So a scheduled run's **first firing will mostly dedupe to `unchanged`** unless the source changed — that IS your dedupe confirmation (SPEC-02 §1). Do **not** think you must re-pull 368 MB; `nhtsa-complaints`' first vintage is done.
- **R2 Actions secrets already set:** `R2_BUCKET`, `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`. Each workflow must export these into `env:` so `collectors.run`'s `select_storage` picks R2 automatically (it keys off `R2_BUCKET`+`R2_ENDPOINT` in env).
- **Heartbeat env pattern:** `collectors.run` reads `HC_<COLLECTOR_NAME_UPPER_WITH_UNDERSCORES>` (e.g. `HC_NHTSA_RECALLS`). Only `HC_NHTSA_RECALLS` exists so far; missing ones make the heartbeat inert (no crash). The full per-collector healthchecks + `HC_*` secrets are **W-003** — wire the `env:` references now; they light up as W-003 creates the checks.
- **`ats-boards` runs differently:** `python -m collectors.ats_boards` (its own entry point), **not** `collectors.run`. It already R2-routes via `select_storage` when `--verify` is off (fixed in W-001). Its workflow differs from the 5 REGISTRY collectors.
- Collector names for `collectors.run`: `cms-deficiencies`, `cpsc-recalls`, `nhtsa-recalls`, `nhtsa-complaints`, `fdic-failures`.

**Do (SPEC-02 §1):**
1. One workflow per collector (or group ≤3 where cadence matches per SPEC-01 §2): **odd-minute** schedules, never `:00`; **2–4× over-scheduling** vs target cadence; `workflow_dispatch` on every one; **per-collector concurrency group** `cancel-in-progress: false`; export the R2 (+ `HC_*` where present) secrets into env.
2. A dedicated workflow for `nhtsa-complaints` (chunk under the 6-hr cap; it's one file — fine).
3. `workflow_dispatch` each one this session to get **≥1 green scheduled/dispatched run in Actions**, and confirm the **dedupe/`unchanged` log** on a second firing (cheap now that vintages exist).

**Accept:** every enabled collector has ≥1 green run in Actions writing to R2; second firing shows identical-hash `unchanged`; heartbeats ping where an `HC_*` secret exists (visible in healthchecks); suite green (`python ci/run_all.py`).

**Catches (pre-written — decision tree, don't improvise):**
- **Datacenter-IP 403 (the big one for W-002):** W-001 ran from the operator's *home* box and every source served 200. **Actions runners are datacenter IPs** — a source that served at home may `403` in Actions. That's the SPEC-01 §4.5 **403-ladder**: (b) generic datacenter 403 → run that collector from the operator box (Task Scheduler) at identical politeness, **log the switch**; (c) collector-specific block/CAPTCHA → **STOP + gate**, never evade. Do not escalate past (b).
- Complaints flaky in Actions → retry once, else operator-box fallback (note it).
- Cron doesn't fire (drift) → `workflow_dispatch` this session; the over-scheduling + heartbeat grace windows are the systemic answer, not a fix.
- Row count wildly off layout → `ZipTabSchema` quarantines it — file the gate, never bend the schema to pass.

**Open WORKPLAN candidate (from W-001, for the orchestrator — not W-002 work):** Cloudflare **Bot Fight Mode 403s the bare `Python-urllib` UA** on `archive.theexhaust.org` (framework `DEFAULT_UA`, curl, browsers, requests all 200). Decide at the site phase (W-007) whether to tune it / add a WAF allow-rule so "anyone can rerun the receipts" holds literally, or just document "send a UA."

**Hand off:** buildlog entry with evidence (Actions run URLs + dedupe logs) → mark W-002 in WORKPLAN → draft NEXT.md for **W-003** (alarms + weekly session) → `python ci/run_all.py` green → commit → save memory → die.

**Env/interpreter note (operator box):** working Python is `C:\ProgramData\miniconda3\python.exe` (boto3 installed); `python`/`py` on PATH are only the MS-Store shim. For any local R2 run, the four `R2_*` env vars must be in the process (a fresh session inherits the persisted `setx` values; a same-process continuation must source a creds file).
