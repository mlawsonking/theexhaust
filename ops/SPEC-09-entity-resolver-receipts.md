# SPEC-09 — Entity resolver & receipts store

*Contract for the evidence layer: the semantic-join moat and the immutable trail from every published number back to raw exhaust.*

## 1. Entity resolver — tiered, ledgered, itself retrocast-scored

**Tiers (cheapest first; a pair only escalates if the tier below can't decide):**

| Tier | Mechanism | Cost |
|---|---|---|
| **T0** | Hard keys: CCN (CMS), CIK (SEC), LEI (GLEIF), FIPS (Census), make/model/year (NHTSA), docket IDs | $0 |
| **T1** | Deterministic crosswalks: SEC CIK↔ticker↔name, GLEIF LEI↔legal name (free bi-weekly file), HUD ZIP↔tract, Census Gazetteer | $0 |
| **T2** | Fuzzy-deterministic: normalized-name token similarity + geo/sector blocking + local embeddings (4080; MiniLM-class) with a conservative auto-accept band and an ambiguity band | $0 |
| **T3** | LLM adjudication of T2-ambiguous pairs only: **gated** Haiku batch (~$90/100k pairs, per research), each verdict cached forever | gated |

**The resolution ledger:** append-only `derived/resolver/ledger/` — every accepted pair: `{entity_a_ref, entity_b_ref, tier, confidence, evidence, method_version, date}`. Published joins cite ledger entries; a pair is never re-adjudicated at cost (cache is permanent); method-version bumps re-score only forward unless a methodology gate orders a re-run.

**Resolver accuracy is publishable methodology, not plumbing:** maintain a labeled pair set per join family; publish resolver precision on the methodology page; resolver changes on launched indexes are methodology gates (they move published numbers).

## 2. Receipts store — every number's evidence bundle

For every published number: `receipts/{index}/{number_id}/` containing `bundle.json`:

```
{ number, unit, as_of, index_version, methodology_ref,      # what was claimed
  inputs: [ {r2_path, sha256, manifest_ref} ],              # exact raw vintages used
  code_ref: <git sha>, resolver_entries: [ledger refs],     # exact computation
  official_chain: {series, last_value, divergence_state} }  # the chained official number
```

- Bundles are immutable; corrections create a successor bundle + a corrections-log entry (never mutation).
- The public "receipts" link on every site number resolves to a human-readable rendering of the bundle (raw-source links included — R2 custom-domain paths are directly citable).
- Named-entity items (when a tier is ever unlocked) additionally embed the full signature computation per-case — the defamation shield is *in the bundle* (opinion on fully disclosed true facts, by construction).

## 3. Interfaces

- **Engines (E1–E5)** call the resolver; they never ship their own matching.
- **The artifact compiler** refuses to render a number lacking a valid bundle (fail-closed — an unreceipted number cannot physically publish).
- **The retrocast harness** consumes ledger + bundles for per-case scored tables.
- **The site build** validates every receipts link resolves before deploy.

## 4. Acceptance criteria (BUILD-02 skeleton; full at BUILD-03/04)

- T0/T1 crosswalk tables load and round-trip known entities (sample: 100 companies SEC↔GLEIF, 100 facilities CCN, 50 places FIPS).
- T2 auto-accept band calibrated on a labeled sample with published precision ≥ the workbook's bar; ambiguous pairs demonstrably queue rather than auto-accept.
- A test T3 gated batch (tiny, $1-cap) writes cached ledger entries; re-run touches zero API calls.
- Fail-closed test: an artifact missing a bundle is refused by the compiler and alarms.
- End-to-end: pick one published test number → follow its receipts link → arrive at raw R2 objects whose hashes match the bundle.
