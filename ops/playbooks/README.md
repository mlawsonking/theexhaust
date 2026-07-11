# ops/playbooks — R2 session scripts

Versioned instructions the semantic runtime executes headless via `claude -p` (SPEC-02 §2). Each obeys the session contract: bootstrap (read `OBSERVATORY.md`, confirm phase + model, STOP on mismatch) → execute playbook only → verify (clean tree) → record → notify (ntfy) → die.

| Playbook | Cadence | Status |
|---|---|---|
| `weekly-ops.md` | Mondays | built at BUILD-02 (needs the gate-report compiler + alarm state) |
| `monthly-audit.md` | first Monday | built at BUILD-02 |

Construction sessions (Phase 4) are operator-started and work the BUILD queue directly; they are not cron playbooks.
