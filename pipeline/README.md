# pipeline/

The five shared engines (posting-diff, text-provenance, hazard-language, price/package, filing-drift) and shared services (entity resolver, retrocast harness, receipts store, artifact compiler). See docs/01-VISION.md §3 for the engine architecture.

Empty until Phase 4. Engines are built once and amortized across every index in their family. The two shared-service contracts are specified: retrocast harness → [ops/SPEC-08](../ops/SPEC-08-retrocast-harness.md), entity resolver + receipts store → [ops/SPEC-09](../ops/SPEC-09-entity-resolver-receipts.md).
