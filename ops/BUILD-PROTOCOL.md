# BUILD-PROTOCOL — the two-session grind contract

*How the build proceeds without wavering: one ORCHESTRATOR session (long-lived, holds context, monitors), many WORKER sessions (fresh, scoped, disposable). Written 2026-07-17 (Fable). Binds every session that touches this repo during Phase 4. The constitution outranks this file; this file outranks convenience.*

---

## 1. Roles

**ORCHESTRATOR** (the operator's standing session): maintains [`ops/state/WORKPLAN.md`](state/WORKPLAN.md) and [`ops/state/NEXT.md`](state/NEXT.md), reviews each completed work item against its acceptance criteria, runs/reads the adversarial review at BUILD-item acceptance (constitutional standing rule), adjusts priorities, and never does the work itself. Context economy: the orchestrator reads worker *handoffs* (buildlog delta + git log + suite tail), not worker transcripts.

**WORKER** (fresh session, started by the operator in this directory): executes exactly one WORKPLAN item, then dies. Start prompt is always the same line:

> **Work the next item: read `ops/state/NEXT.md` and execute it under the build-grind contract in `CLAUDE.md` and `ops/BUILD-PROTOCOL.md`.**

## 2. Worker session lifecycle (the contract)

1. **Bootstrap:** read `OBSERVATORY.md` status block + covenants (skim, not stroll), `ops/state/NEXT.md`, and **only** the files NEXT.md's read-list names. NEVER read `docs/01-VISION.md` or `docs/02-RESEARCH.md` wholesale — the WORKPLAN cites exact sections when an item needs them. Phase/model check per the constitution; STOP on mismatch.
2. **Execute the one item.** Its scope is the scope. Anything discovered along the way becomes (a) a gate file, (b) a `SCOPE-LEDGER` note, or (c) a one-line WORKPLAN candidate for the orchestrator — never a detour.
3. **Verify:** the item's own acceptance checks, plus the **full suite** (§5) green before any commit. "Should work" is not done; live sources are re-verified before being depended on (standing order).
4. **Record:** append a session entry to `docs/04-BUILDLOG.md` (what built, what verified, what deferred, exact commits).
5. **Hand off:** update `ops/state/WORKPLAN.md` (mark the item done/partial/blocked) and **draft the next `ops/state/NEXT.md`** from the top of the WORKPLAN (the orchestrator may adjust it before the next worker starts).
6. **Commit** (all changes, clean tree) and **save the session memory** (household-memory) per the constitution's session-end rule. Then die — no background residue.
7. **Provenance hashes come from PUSHED history only** (lesson, W-006): Actions may commit fleet state to `main` mid-session, so a hand-off `pull --rebase` REWRITES any local commit hashes already cited as provenance (scorecards, reports, registrations). Pull/rebase FIRST, then cite; any artifact citing a hash must re-verify that hash exists in `origin/main` before the session dies.

## 3. Decisions in absence — the blocked-decision tree

When a worker hits something the item didn't anticipate, it does NOT improvise and does NOT stall. In order:

1. **Is there a pre-written fallback on the item?** Execute it, note it in the buildlog.
2. **Is the safe default obvious and reversible?** (Pause a failing collector; skip a flaky source this run; store data even if anomalous.) Take it, note it. The safe default is always: *do nothing destructive, keep collecting, ask.*
3. **Is it gate-shaped?** (New source, ToS surface, methodology, spend, anything named-entity, anything legal.) File the gate (`opscore.gates.new_gate` format), continue with the rest of the item if severable, else mark the item `blocked(gate:<slug>)` in WORKPLAN and proceed to hand-off.
4. **Is it a STOP condition?** (Covenant conflict; phase/model mismatch; reality diverged from spec — e.g., an endpoint vanished; anything in the do-not-collect register; any metered-LLM temptation.) STOP the item, write precisely what was found and what decision is needed, hand off. **A precise stop is a successful session.**

Never: work around a permission denial, accept any ToS, create accounts, touch CAPTCHA-guarded anything, put an LLM key anywhere near R1, or "just quickly" exceed the item's scope.

## 4. Acceptance & the review gate

- A WORKPLAN item is **done** when its listed acceptance checks pass and the buildlog says so with evidence (output pasted or path cited).
- A **BUILD item** (the gameplan §6 units) is **accepted** only after an adversarial review pass over its code (constitutional rule, 2026-07-13): multi-reviewer, findings verified, each confirmed finding fixed or dismissed-with-reasons in the buildlog. The orchestrator runs this; workers don't self-accept.
- Anything touching a **published** surface (once anything is published) additionally walks the SPEC-08 hostile-review checklist before deploy.

## 5. The full suite (run before every commit, verbatim)

```
python ci/covenant_guard.py
python ci/test_covenant_guard.py
python -m collectors.tests.test_framework
python -m collectors.tests.test_warn
python -m opscore.tests.test_opscore
python -m retrocast.tests.test_harness
python -m sitegen.tests.test_site
python -m engines.tests.test_engines
python -m resolver.tests.test_resolver
```

All green or no commit. (W-001 adds `ci/run_all.py` as the one-liner; until then, the block above is the liturgy.) New code lands with tests; fixed bugs land with regression tests; CI (`.github/workflows/ci.yml`) runs the same suite on every push once the remote exists.

## 6. Context economy (why this protocol exists)

- Workers read: `CLAUDE.md` (auto) + constitution status/covenants + `NEXT.md` + the item's read-list. Target: **< 10 files before work starts.**
- The WORKPLAN carries per-item read-lists precisely so nobody "reads around" for orientation.
- History lives in `docs/04-BUILDLOG.md`; scope truth lives in `docs/05-SCOPE-LEDGER.md`; queue truth lives in `ops/state/WORKPLAN.md`; the next action lives in `ops/state/NEXT.md`. One source each; cite, don't duplicate.

## 7. Operator tasking (unchanged rules, restated)

Michael's ledger is the Vikunja board `observatory`: **current blockers + hard-dated items only** (amended 2026-07-17). Workers never file operator tasks for things a future session can do; a gate that needs Michael also gets a `vtask add` blocker (PowerShell only on this box). Never re-file a near-duplicate — reuse the open task.
