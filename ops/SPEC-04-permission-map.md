# SPEC-04 — Permission map & gate mechanics

*Contract for what the machine may do alone versus what waits for Michael. The safe default everywhere is: do nothing, keep collecting, ask.*

## 1. Autonomous (no gate, ever-running)

| Action | Bound |
|---|---|
| Archival collection | approved collector roster only (SPEC-01 §2); pausing a failing collector is autonomous (safe direction), enabling one is not |
| Schema validation, quarantine, dedupe | always |
| Index recomputation | **frozen methodology versions only**, for already-launched indexes |
| Artifact compile + post (site, RSS/JSON, Bluesky) | cadence + anomaly artifacts of already-launched **aggregate** indexes, from approved templates |
| Scorecard updates | as official numbers arrive (chaining is doctrine) |
| Corrections **detection** + corrections-log entry + page flag | auto-publishes (accuracy-as-control covenant) |
| Heartbeats, alarms, health/state writes, site rebuilds | always |
| Drafting anything (reports, workbook drafts, gate items) | drafts are internal until gated |

## 2. Hard-stopped (gate item + operator decision required)

| Action | Notes |
|---|---|
| Publishing any **new index**, artifact type, or surface | launching a compiled workbook is a gate |
| Any **methodology, threshold, or calibration change** on anything published | approval triggers full backtest republication (doctrine) |
| Any **named-entity** publication or tier unlock | naming-gate covenant; financial institutions: **permanently sealed, non-waivable** |
| **New source onboarding**; any collection posture change (403-ladder step (b), universe expansion) | ToS surface |
| Reviving a **do-not-collect** item | double lock: gate + fresh written operator sign-off in the gate file |
| Any **metered spend** (backfills, adjudication batches) | pre-estimate + hard cap required in the gate file (SPEC-02 §3) |
| Any **paid service**, plan change, or new external dependency | |
| Anything with **legal surface**: C&D response, takedown, correction *narrative*, terms/privacy pages | the transparency-log *entry* auto-publishes; the *response* gates |
| External comms beyond scheduled artifacts: press replies, journalist-gift list, permissioned-panel outreach, grant submissions | |
| Orphan-mode exit actions and floor-mode configuration changes | SPEC-06 |

## 3. Gate item format

One file per decision: `ops/state/QUEUE/pending/GATE-YYYYMMDD-<slug>.md`

```
# GATE: <one-line title>
type: new-index | methodology | named-entity | source | spend | legal | comms | other
created: YYYY-MM-DD  by: <job/session>
expires: YYYY-MM-DD (default +28d)
default_on_expiry: no-action        # must be the safe option
estimate_usd / hard_cap_usd:        # spend gates only
## What & why now            (≤5 lines)
## Evidence                  (links: receipts, HEALTH, research §, diffs)
## Options                   (A recommended / B / C, one line each)
DECISION:                    # operator writes: approve-A | approve-B | reject | defer YYYY-MM-DD
notes:                       # optional operator free text
```

**Mechanics:** creating a gate file pings `exhaust-gate`. The operator decides by editing `DECISION:` (GitHub web edit suffices) or telling any Claude session, which edits + commits. The weekly session moves decided files to `QUEUE/decided/{YYYY}/` and *executes* approvals (or schedules them). Expired-undecided files move to `decided/` with `expired-no-action` — nothing ever executes by expiry. Every decision is thereby a permanent public record (transparency is on-brand; the repo is public).

## 4. The budget governor

- R1 holds no Anthropic key; R2 sessions are subscription-side. Therefore steady-state metered spend is **structurally $0**, not aspirationally.
- Every gated run: cap enforced in code (token accounting; abort at cap), actuals → `ops/state/BUDGET.json` (`{run_id, gate_id, estimate, cap, actual, date}`), estimate-vs-actual in the next report.
- `BUDGET.json` also tracks R2 storage projection (from manifests) and annual lines (domain, LLC, insurance) with renewal dates → `CALENDAR.md`.

## 5. Acceptance criteria (BUILD-02)

- Round-trip: job files a gate → ntfy received → operator edits `DECISION: approve-A` → weekly session executes + archives it.
- Expiry test: an undecided gate past `expires` archives as `expired-no-action` and demonstrably does not execute.
- Spend test: a $1-cap gated run aborts at cap and ledgers actuals.
- Static check in CI: no collector exists for do-not-collect sources; no Anthropic key in R1 secrets.
