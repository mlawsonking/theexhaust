# ops/state — the machine's memory

Small machine-readable files: R1 (Actions) writes facts, R2 (Claude sessions) writes judgment, the operator writes decisions. This directory is the interface between the runtimes (gameplan §3.2).

| File / dir | Written by | Read by | Contract |
|---|---|---|---|
| `HEALTH.json` | R1 collectors (on validated store) | report compiler, every session, heartbeat | SPEC-03 §1 |
| `QUEUE/pending/` | any job/session (drafts a gate) | operator, weekly session | SPEC-04 §3 |
| `QUEUE/decided/{YYYY}/` | weekly session (moves decided/expired) | audit trail (public, permanent) | SPEC-04 §3 |
| `BUDGET.json` | budget governor, gated runs | report, monthly audit | SPEC-04 §4 |
| `CALENDAR.md` | weekly/monthly session | report | SPEC-05 §5 |
| `ACK` | operator (touch) / any activity | orphan clock | SPEC-06 §1 |

Nothing here executes anything — files are state, jobs act on them. Safe default everywhere: do nothing, keep collecting, ask.
