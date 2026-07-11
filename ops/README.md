# ops/

The autonomy machinery. Specified in Phase 3 (2026-07-11) as nine binding contracts; built in Phase 4 to their acceptance criteria. The narrative map is [docs/03-GAMEPLAN.md](../docs/03-GAMEPLAN.md) §3–§6.

| Spec | Contract |
|---|---|
| [SPEC-01](SPEC-01-archival-fleet.md) | Archival fleet: collectors, storage layout, quarantine, collection etiquette + the 403 ladder |
| [SPEC-02](SPEC-02-scheduling.md) | Two runtimes: R1 Actions (cron-drift defense) + R2 scheduled Claude sessions (contracts, playbooks, gated runs) |
| [SPEC-03](SPEC-03-alarms-and-drift.md) | External dead-man heartbeat, drift detectors, ntfy taxonomy, the alarm budget |
| [SPEC-04](SPEC-04-permission-map.md) | Autonomous vs. hard-gated actions; gate-file mechanics; the budget governor |
| [SPEC-05](SPEC-05-gate-report.md) | The weekly gate report — Michael's ~1 hour, compiled never hand-written |
| [SPEC-06](SPEC-06-orphan-protocol.md) | Orphan protocol, floor mode, stale-data posture, succession seed |
| [SPEC-07](SPEC-07-workbook-compiler.md) | Index workbooks + the compiler: how index N+1 costs a document, not a system |
| [SPEC-08](SPEC-08-retrocast-harness.md) | The retrocast harness: pre-registration, splits, hostile-review checklist, forward-validation mode |
| [SPEC-09](SPEC-09-entity-resolver-receipts.md) | Entity resolver (tiered, ledgered) + receipts store (fail-closed evidence bundles) |

Phase 4 additions land here as they're built: `playbooks/` (R2 session playbooks), `state/` (HEALTH, QUEUE, BUDGET, CALENDAR, ACK), `reports/` (weekly gate reports).
