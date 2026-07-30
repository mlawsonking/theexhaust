# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the W-007c worker at hand-off, 2026-07-30; the orchestrator may re-point it before the next session starts.*

## ⚑ Step zero, before anything else

**`git fetch && git pull --rebase origin main` BEFORE reading this file.** A stale checkout of the work order is indistinguishable, from inside the session, from a correct one — W-008 read a superseded `NEXT.md` and executed the wrong item. This is now **BUILD-PROTOCOL §2.0**, enacted by W-007c.

## Already done — do not redo

- **W-007c BUILD-04 review fixes are `done` (2026-07-30): 21/21 dispositioned, all fixed**, each with a regression test or a committed artifact correction. **No bar moved, no metric changed, no retrocast was re-run, nothing was deployed.** Suite 15/15, +18 tests. `ops/state/REVIEW-BUILD04.md` is now a closed spec — it is history, not a to-do list. Full disposition table in the buildlog.
- **W-008 Hospital/Care retrocast is `done` (2026-07-30) and it FAILED its pre-registered bars**, published with an autopsy. The PBJ `--all` backfill is complete: 26 releases archived, 11 quarantined on a legacy lowercase header.
- **The BUDGET re-projection (G11) has run** against a real measured sweep — 2.1766 GB / 160 objects. `ops/storage_sweep.py` makes it a one-command trigger from now on.

## Not your job (no worker needed)

- **BUILD-01 acceptance** is the **orchestrator's**: ⚑ **#215** — run `python ops/fleet_green.py` on/after **2026-08-04**; exit 0 closes SPEC-01 §6 criterion 1. As of 2026-07-30 it reports **7/8 GREEN**, the only laggard being `nhtsa-recalls`'s **2026-07-28** `startup_failure` from the long-fixed W-002b permission bug, which ages out of the 7-day window before 08-04. No collector carries a paused unit.
- **BUILD-04 acceptance** is the **orchestrator's**, and it needs an **independent adversarial-review pass over the W-007c fixes** (constitutional; the W-007c dispositions were written by the session that made them).
- **An independent hostile-review confirmation of the Hospital/Care v1 failure** is still owed, exactly as the orchestrator required and obtained for NHTSA v1.
- **Operator residuals:** ⚑ **#212** healthchecks provisioning (8 checks) · ⚑ **#213** weekly-session scheduler · ⚑ **#217** Cloudflare Pages hookup · ⚑ **#219** the post-NHTSA-v1 move **and** whether the first public number is our own failure — a choice between **two** published failures.

---

## Standing decision — do not pre-empt it

**⚑ #219 — publication is not decided.** `.github/workflows/site.yml` is `workflow_dispatch`-only with **no cron** (a scheduled full publish would decide #219 by default) and defaults to the operator-approved `placeholder` mode. Do not add a cron, flip the default to `full`, or deploy. **Do not soften, move, or hide either FAIL scorecard** on the Track Record page — that is constitutional, and there are two of them. W-007c added disclosure to both rows (missed bars, leakage flags, evidence links); nothing may subtract it.

---

## Item W-007d — a recovery must be able to reach committed state (`_collector.yml`)

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Why:** `.github/workflows/_collector.yml` skips the state commit whenever the collector's `last_action` is `unchanged`. That was a deliberate anti-spam rule for dedupe firings, and it has a hole with teeth: **a collector can only clear a stale `quarantined` / `paused` flag from committed state on a run that *stores* something.** For a quarterly source that is months. This is not hypothetical on three counts:

1. It **bit ⚑ #215 during W-008** — the PBJ backfill left node-level `last_action: "quarantined"`, the exact field `ops/fleet_green.py` reads, and the recomputed `unchanged` never reached `main`. It was cleared only because that session happened to run the collector in its normal scope and store.
2. It is the **mirror of W-005c/F02** (there a *failure* could not reach committed state; here a *recovery* cannot).
3. **W-007c/G10 made it load-bearing**: a rerun after a lost ledger now correctly reads today's manifest and reports `unchanged`, so the recovered per-quarter baseline lands on the runner's disk and is then thrown away by this skip.

**Read (only these):** `.github/workflows/_collector.yml` (the whole file — it is 100 lines and it is the item), `collectors/cms_pbj.py` `run_fleet` tail (what the node record actually says after a recovery), `opscore/fleetgreen.py` (`committed_state` / `score` — the consumer whose verdict this protects), and the W-005c/F02 + W-008 + W-007c/G10 buildlog entries for the three precedents. Do **not** read `docs/01-VISION.md` or `docs/02-RESEARCH.md`.

**Scope:** make the skip test *state equivalence*, not `last_action`. A dedupe firing that changes nothing but timestamps still must not commit (that rule is good and keeps over-scheduled collectors off `main`); a run that changes any flag a watcher reads — `quarantined`, `paused`/`paused_*`, `needs_gate`, `ambiguous_quarters`, `last_hash`, a per-unit record — must commit even when its `last_action` is `unchanged`. The obvious shape is to diff the committed file against the new one with timestamp fields excluded, rather than branching on one string.

**Catches (decision tree, don't improvise):**
- **`_collector.yml` is shared by all 8 collectors.** A bug here stops the whole archive from persisting state, which is worse than the defect being fixed. The safe default is to commit *more* often, never less.
- **A green local suite does not prove a workflow change.** Acceptance requires a real dispatched Actions run.
- The file holds R2 secrets and a `contents:write` token — W-007c/G18 moved every `workflow_dispatch` input behind an env var. **Do not reintroduce `${{ inputs.* }}` into a `run:` body.**
- Blocked → BUILD-PROTOCOL §3: pre-written fallback → reversible safe default → gate file → STOP with a precise report. A precise stop is a successful session.

**Accept:** a timestamp-only dedupe still commits nothing; a run that clears a quarantine/pause while reporting `unchanged` **does** commit, proven by a **dispatched Actions run** with the commit cited; `python ci/run_all.py` green; `python ops/fleet_green.py` unchanged against current state (7/8, same laggard).

**State you inherit (don't re-derive):** working Python `C:\ProgramData\miniconda3\python.exe`; full suite = `python ci/run_all.py` (**15 steps**, green at hand-off); R2 creds in this box's env; `gh` authenticated. `site/data/` is gitignored and rebuildable — after W-007c a **torn or stale** derived layer now refuses the build by design (`python -m artifacts.compile` rebuilds it).

**Hand off:** buildlog entry with the Actions run cited → mark W-007d in `WORKPLAN.md` → draft the next `NEXT.md` → `python ci/run_all.py` green → commit → push → memory → die.

---

## If the orchestrator prefers to advance the BUILD queue instead

W-007d is a small, time-sensitive integrity fix that protects the ⚑ #215 evidence dated **2026-08-04**, which is why it is drafted first. The queued alternatives, in WORKPLAN order:

- **W-009 · expansion collectors C6/C8/C10/C11** — model-bills (Wayback-only for ALEC-Exposed), EDGAR 8-K (10 req/s + UA rule), mouseprint, EIA-861. Severable from every open gate, and "every uncollected week is lost forever" outranks most things.
- **PBJ legacy-header recovery (11 quarters, 2017Q1–2020Q3)** — case-insensitive column matching plus an alias map would recover them from the **already-archived** quarantine bytes with no refetch, giving a Hospital/Care v2 a far longer signal history. Touches `CsvSchema`, shared by 8 collectors.
- **The county-level observational staffing surface** — severable from the failed retrocast; publishable under covenant 2 as observational facts with receipts, with no signature claim.

## Candidates raised by W-007c (recorded in WORKPLAN; **not** this item's scope)

- **Hospital/Care carries the identical G20 defect**: its hostile review and the autopsy both assert an independent Newton/IRLS solve that `hospital_care/run_v1.py` does not emit. Raised rather than fixed, because the independent hostile confirmation of that failure is the orchestrator's.
- **The gate slug names the wrong cause**: `_fleet_gate` emits `cms-pbj-fetch-3x-<Q>`, but after G05 a *drift* pause reaches it too, handing the operator a filename that says "fetch" about a schema problem.
- Unchanged from W-008: `release_count` reads 37/37 published while 11 are quarantined rather than archived, so it no longer signals the archive gap.
