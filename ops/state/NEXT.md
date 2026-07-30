# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. W-007c section written by the orchestrator 2026-07-30 and preserved verbatim below; surrounding notes updated by the W-008 worker at hand-off, 2026-07-30.*

## ⚑ Read this first — a worker ran the wrong item, and the cause is worth fixing

The orchestrator re-pointed this file to **W-007c ONLY** in commit `d986118`. The next session **did not `git fetch` before reading it**, so its local checkout still carried the older W-007b hand-off ordering W-008 — and it executed **W-008** instead. W-008 is delivered, green and severable (see below), but **it was worked out of order and W-007c is still outstanding.**

**Every worker: `git fetch && git pull --rebase origin main` BEFORE reading this file.** A stale checkout of the work order is indistinguishable, from inside the session, from a correct one. Recommended for BUILD-PROTOCOL §2 as a first-step requirement.

## Already done — do not redo

- **W-008 Hospital/Care retrocast (BUILD-05) is `done` (2026-07-30) and it FAILED its pre-registered bars**, published with an autopsy. PR-AUC 0.1771 vs the prior-harm baseline's 0.2526 · precision 0.1794 (base rate 0.1357) · event-recall 0.4605 · median lead 154 d. Registration `d6b78c3` pushed before the runner existed. Hostile review 6/6, and it found a real defect in the shared harness (the planted-leak guard did not catch a label oracle — fixed). **The PBJ `--all` backfill is complete**: 26 releases archived, 11 quarantined on a legacy lowercase header. Full record in the buildlog and `retrocast/hospital-care/`.
- Consequently **G10 no longer blocks anything** — the backfill it describes has run. The finding still stands (the run remains non-resumable) and is still worth fixing on its merits, just not as a blocker.

## Not your job (no worker needed)

- **BUILD-01 acceptance** is the **orchestrator's**: ⚑ **#215** — run `python ops/fleet_green.py` on/after **2026-08-04**; exit 0 closes SPEC-01 §6 criterion 1. As of 2026-07-30 it reports **7/8 GREEN**; the only laggard is `nhtsa-recalls`, whose sole blemish is the **2026-07-28** `startup_failure` from the long-fixed W-002b permission bug, and that day **ages out of the 7-day window before 08-04**. `cms-pbj` was briefly flipped to QUARANTINED by W-008's backfill and is GREEN again — restored by a real `--quarters 1` run, never a hand edit.
- **Operator residuals:** ⚑ **#212** healthchecks provisioning (8 checks) · ⚑ **#213** weekly-session scheduler · ⚑ **#217** Cloudflare Pages hookup · ⚑ **#219** the post-NHTSA-v1 move **and** whether the first public number is our own failure — now a choice between **two** published failures.
- **An independent hostile-review confirmation of the Hospital/Care v1 failure** is owed, exactly as the orchestrator required and obtained for NHTSA v1. The W-008 review was written in-session.

---

## Standing decision — do not pre-empt it

**⚑ #219 — publication is not decided.** `.github/workflows/site.yml` is `workflow_dispatch`-only with **no cron** (a scheduled full publish would decide #219 by default) and defaults to the operator-approved `placeholder` mode. Do not add a cron, flip the default to `full`, or deploy. **Do not soften, move, or hide either FAIL scorecard** on the Track Record page — that is constitutional, and there are now two of them.

---

## Item W-007c — BUILD-04 review fixes + NHTSA artifact corrections (acceptance + publish blocker)

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Why:** the BUILD-04 publish-path adversarial review + independent hostile confirmation returned **21 confirmed findings (1 CRITICAL / 3 HIGH / 9 MEDIUM / 8 LOW)**. The independent pass **CONFIRMS the NHTSA failure analysis** (nothing flips a bar), but the publish path can render numbers without receipts, the Track Record can silently lose its FAIL row, and three findings corrupt the ⚑ #215 (2026-08-04) acceptance evidence.

**Read (only these):** `ops/state/REVIEW-BUILD04.md` (**the spec — all 21 findings**), then the files it names as you work them. Do **not** read `docs/01-VISION.md` or `docs/02-RESEARCH.md`.

**Priority order:**
1. **G01 (CRITICAL) + G02 + G04 (HIGH, publish path):** strict-load the derived layer (exists-but-unparseable ⇒ abort build, never render-with-zero-receipts); `require_receipt` must check **claim-evidence agreement** (number/as_of/version vs the bundle); atomic end-of-run JSON writes; a corrupt scorecard **aborts the build** (absent ≠ broken — the FAIL row must be unlosable). Regression tests mirroring the reviewers' repros.
2. **G03 + G05 + G06 (fleet + #215 evidence):** paused/dup-only runs never ping heartbeat success; dup counts toward the pause streak; `fleetgreen.score()` sees quarter-level pauses.
3. **G10 (no longer a blocker — W-008's backfill has run):** persist health state per-release during `--all` (interrupt-safe, KeyboardInterrupt included) + an interruption test.
4. **G18 (security):** stop raw-interpolating `workflow_dispatch` inputs in `_collector.yml` (env-var indirection) — the job holds R2 secrets + a write token.
5. **G13/G14/G19/G20 (NHTSA artifact corrections — required before any #219 publication):** re-state the 57.8% claim to describe its actual computation (or recompute as described); correct the freeze-commit citation to the true freeze (`4a24a39`) and note the rebase effect on dates; remove or soften the unverifiable ordering claim in the hostile-review preamble; publish the train-coverage + IRLS-reproduction computations as committed artifacts or drop the claims. **These are transparency corrections — results and bars do not change; note each edit inline as a correction.**
6. **Remaining MEDIUM/LOW** (G07–G09, G11–G12, G15–G17, G21): fix or defer-with-reasons (G09 duplicate-quarter and G12 evidence-links are cheap; G11 is a one-command BUDGET re-projection).

**State you inherit (don't re-derive):** working Python `C:\ProgramData\miniconda3\python.exe`; full suite = `python ci/run_all.py` (**15 steps**, green at hand-off); R2 creds in this box's env; `gh` authenticated. **The Track Record now renders TWO FAIL rows** (`nhtsa-recalls`, `hospital-care`) and the Retrocasts page lists two pre-registrations — any G04 fix must keep both. PR-AUC is now rendered to 4 decimals (`sitegen.build._num`); the raw value stays in `scorecard.json`.

**Accept:** all 21 dispositioned (fix + regression test, or dismiss/defer with reasons in the buildlog); suite green; one post-fix build renders both Track Record FAIL rows with evidence links and refuses a fixture with a corrupt scorecard **and** a torn `artifacts.json`; `python ops/fleet_green.py` still exits correctly against current state.

**Catches (decision tree, don't improvise):**
- A finding that turns out to be wrong is **dismissed with evidence and reasoning**, not silently skipped — W-005c's F19a fixture correction is the precedent.
- NHTSA artifact corrections publish **with the pre-fix wording**, never quietly rewritten. If a fix would change a number, STOP — that is a new registration question.
- Never touch the do-not-collect register; never put an LLM key near R1.
- Blocked → BUILD-PROTOCOL §3: pre-written fallback → reversible safe default → gate file → STOP with a precise report. A precise stop is a successful session.

**Hand off:** buildlog disposition table → mark W-007c in WORKPLAN → draft the next `NEXT.md` → `python ci/run_all.py` green → commit → push → memory → die.

---

## Candidates raised by W-008 (recorded in WORKPLAN; **not** this item's scope)

Listed so the next worker does not rediscover them: the **11 quarantined legacy-header PBJ releases** (recoverable from already-archived bytes with case-insensitive matching + an alias map — would give a v2 far more signal history); **a recovery cannot reach committed state** (`_collector.yml` skips the state commit on a dedupe, so a stale quarantine only clears on a `stored` run — this bit ⚑ #215 this session and is the mirror of W-005c/F02, adjacent to G03/G05/G06); **`release_count` no longer signals the archive gap** (reads 37/37 published while 11 are quarantined, not archived); the severable **county-level observational staffing surface**; and the **v2 hypotheses** for Hospital/Care, none tested and none claimed.
