# Claude session bootstrap

1. **Read `OBSERVATORY.md` first, every session.** It is the constitution: thesis, phase status, covenants, handoff notes.
2. **Check the phase and the assigned model.** Phase 1/3 = Fable (ideation/architecture). Phase 2/4 = Opus (research/implementation). If this session's model or task doesn't match the current phase, STOP and say so — do not do the wrong phase's work.
3. **No implementation code before Phase 4.** Phases 1–3 produce documents and specs only.
4. **Spend covenant:** steady-state work runs on subscription Claude Code sessions, the local RTX 4080, and free compute (GitHub Actions public repo, static hosting). Metered Anthropic API spend is gated per-run by Michael — never ambient, never assumed.
5. **Retrocast gate:** nothing publishes as an index without a historical backtest against named ground truth, with precision/recall published. "Never predict, only measure."
6. At session end: update the status block in `OBSERVATORY.md`, commit, and save a project memory (household-memory MCP) summarizing what changed.

## Build-grind contract (Phase 4, effective 2026-07-17)

7. **Roles.** The operator runs one ORCHESTRATOR session (reviews, maintains the queue, never builds) and serial WORKER sessions (each executes exactly one item, then dies). The full contract is [`ops/BUILD-PROTOCOL.md`](ops/BUILD-PROTOCOL.md) — read it if this session is either role.
8. **If your start prompt says "work the next item":** you are a WORKER. Read `ops/state/NEXT.md` and ONLY the files it lists. Never read `docs/01-VISION.md` or `docs/02-RESEARCH.md` wholesale — the queue cites exact sections. Target < 10 files before work starts.
9. **Scope is law.** Work the one item. Discoveries become gate files, `docs/05-SCOPE-LEDGER.md` notes, or WORKPLAN candidates — never detours. New indexes/joins enter only via ledger triggers or operator gates.
10. **No commit without the full suite green** (the verbatim block in BUILD-PROTOCOL §5; `ci/run_all.py` once it exists). New code lands with tests; fixed bugs land with regression tests.
11. **Blocked? Use the decision tree** (BUILD-PROTOCOL §3): pre-written fallback → reversible safe default → gate file → STOP with a precise report. A precise stop is a successful session. Never work around a denial, never touch the do-not-collect register, never put an LLM key near R1.
12. **Hand off:** buildlog entry with evidence → update `WORKPLAN.md` → draft the next `NEXT.md` → commit → memory → die. BUILD items are accepted only by the orchestrator after adversarial review (constitutional).
13. **Operator tasking:** Vikunja board `observatory` = current blockers + hard-dated items only; `vtask` works in PowerShell only on this box; reuse open tasks, never near-duplicate.
