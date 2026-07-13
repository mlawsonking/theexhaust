# ops/playbooks — R2 session scripts

Versioned instructions the semantic runtime executes headless via `claude -p` (SPEC-02 §2). Each obeys the session contract: bootstrap (read `OBSERVATORY.md`, confirm phase + model, STOP on mismatch) → execute playbook only → verify (clean tree) → record → notify (ntfy) → die.

| Playbook | Cadence | Status |
|---|---|---|
| `weekly-ops.md` | Mondays | **built** (drives `python -m opscore.weekly`: sweep gates, file collector gates, compile report, alarm-budget check, pulse) |
| `monthly-audit.md` | first Monday | **built** (budget reconciliation, mute review, covenant spot-check, ToS re-verify rotation) |

Construction sessions (Phase 4) are operator-started and work the BUILD queue directly; they are not cron playbooks.
