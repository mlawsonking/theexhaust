# SPEC-02 — Scheduling & runtimes

*Contract for how anything runs. Two runtimes, both bounded, self-verifying, dying clean.*

## 1. R1 — deterministic runtime (GitHub Actions)

- **Host:** public repo `theexhaust`, **standard runners only** (larger runners are billed even on public repos — banned). Jobs chunk under the 6-hour cap.
- **No metered LLM calls in R1, ever.** No Anthropic key exists in Actions secrets until a gated-run mechanism explicitly injects one for a single approved workflow run, then removes it.
- **Cron-drift defense (mandatory, constitutional):**
  - Over-schedule: collectors schedule 2–4× their target cadence and **dedupe by content hash** (SPEC-01 §4.4) so extra firings are free and missed firings are covered.
  - Odd minutes only, never `:00` (e.g., `17,47 * * * *` patterns); stagger collectors across the hour.
  - Every scheduled workflow also carries `workflow_dispatch` (manual re-fire) and a repo-activity keepalive is unnecessary while collectors commit state — but if all commits pause (orphan mode), a monthly keepalive commit prevents GitHub's 60-day cron disablement.
  - Success is measured by **outcome** (snapshot stored, heartbeat pinged), never by "the cron fired."
- **Concurrency:** one concurrency group per collector (`cancel-in-progress: false`) so overlapping firings queue rather than collide.
- **Job contract (every R1 job):** read config → do one bounded thing → verify own output (schema, hashes, row bands) → write state (`HEALTH.json`, manifests) → ping heartbeat on success → exit nonzero loudly on failure (which alarms via SPEC-03). No job writes to `raw/` without validation; no job retries more than twice without alarming.

## 2. R2 — semantic runtime (scheduled Claude Code sessions, operator box)

- **Mechanism:** Windows Task Scheduler → `claude -p "<playbook invocation>"` headless, subscription-side (spend covenant). Playbooks live in `ops/playbooks/`, versioned.
- **Standing sessions:**
  - `weekly-ops.md` — Mondays: read constitution → verify phase → triage alarms/quarantine → spot-verify one pipeline end-to-end (rotating) → compile the gate report (SPEC-05) → update `CALENDAR.md` → commit → ntfy `exhaust-pulse` with the report link → exit.
  - `monthly-audit.md` — first Monday: alarm-budget review, `BUDGET.json` reconciliation vs. Cloudflare/Anthropic consoles, storage projection, covenant spot-check (pick 2 collectors, audit against SPEC-01 §4), orphan-clock check, dependency/ToS re-verify rotation (one research-§5 row per month, refreshed `verified` date).
  - Construction sessions (Phase 4) — operator-started, work the BUILD queue per gameplan §6.
- **Session contract (every R2 session):** bootstrap (read `OBSERVATORY.md`, confirm phase + model; STOP on mismatch) → execute playbook only (no improvisation; discoveries become gate items or BUILDLOG notes) → verify (clean tree test: all changes committed, all tests it touched green) → record (BUILDLOG or report) → notify (ntfy) → die (no background residue). Hard time-box per playbook (default 90 min; construction sessions per-item).
- **The 4080:** local embeddings/classifiers (MiniLM/model2vec-class, cross-encoder rerank, hazard classifiers) run here or in R1-CPU where small enough. Anything wanting metered API is a **gated run**: gate item with pre-estimate → operator approves → single keyed execution → key removed → spend ledgered.

## 3. Gated-run mechanics

A gated run is: the gate file (SPEC-04 format) carrying `estimate_usd`, `hard_cap_usd`, the exact command/workflow ref, and the model/batch parameters → on approval, executed once (R2 locally, or R1 via a temporarily-injected secret) with the cap enforced in code (token accounting, OnScript budget-governor pattern) → actuals written to `BUDGET.json` → key/secret removed. Estimated-vs-actual appears in the next gate report.

## 4. Acceptance criteria (BUILD-02, jointly with SPEC-03/04/05)

- A collector workflow deliberately skipped by GitHub (simulated by disabling one firing) still meets its cadence via over-scheduling, with dedupe confirmed by identical-hash skip logs.
- Weekly session runs headless end-to-end twice consecutively: triage → report → commit → ntfy, inside the time-box, leaving a clean tree.
- A test gated run round-trips with a $1 cap and correct ledger entry.
- Phase-mismatch bootstrap test: an R2 session pointed at a wrong-phase instruction stops and says so.
