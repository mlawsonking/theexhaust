# Claude session bootstrap

1. **Read `OBSERVATORY.md` first, every session.** It is the constitution: thesis, phase status, covenants, handoff notes.
2. **Check the phase and the assigned model.** Phase 1/3 = Fable (ideation/architecture). Phase 2/4 = Opus (research/implementation). If this session's model or task doesn't match the current phase, STOP and say so — do not do the wrong phase's work.
3. **No implementation code before Phase 4.** Phases 1–3 produce documents and specs only.
4. **Spend covenant:** steady-state work runs on subscription Claude Code sessions, the local RTX 4080, and free compute (GitHub Actions public repo, static hosting). Metered Anthropic API spend is gated per-run by Michael — never ambient, never assumed.
5. **Retrocast gate:** nothing publishes as an index without a historical backtest against named ground truth, with precision/recall published. "Never predict, only measure."
6. At session end: update the status block in `OBSERVATORY.md`, commit, and save a project memory (household-memory MCP) summarizing what changed.
