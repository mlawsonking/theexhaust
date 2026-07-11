# SPEC-07 — Index workbooks & the compiler

*Contract for how index N+1 costs a document, not a system. The workbook is the only hand-written artifact; everything else about an index is compiled from it.*

## 1. The workbook

`indexes/<slug>/WORKBOOK.md` — authored (by an R2 session, at gate time) when an index is proposed; approving the compiled output IS the launch gate. Required blocks:

```
# WORKBOOK: <index name>
slug / family / engine:            # E1..E5 + shared services used
verdict_ref:                       # research §4.1 row (or later re-verification)
corpora:                           # rows from the access ledger, each with verified date
official_number:                   # what it chains to + publication cadence + lag removed
tier: aggregate | aggregate+named  # named requires the firewall (constitution)
## Retrocast spec                  # ground truth source; protocol (SPEC-08 profile);
                                   # pass thresholds — set BEFORE any result is computed;
                                   # forward-validation? (labels source + accrual cadence)
## Methodology v0                  # signal construction, entity resolution tiers used,
                                   # calibration band vs. official, known biases stated
## Artifacts                       # cadence artifact (chart+sentence+receipts template);
                                   # anomaly artifact + thresholds; piggyback (official release days);
                                   # local variants (per-state/metro/county)?
## Alarms                          # volume bands, divergence band, staleness expectations
## Weekly jobs                     # each: name, cadence, bound (<45min), acceptance criteria
## Covenant notes                  # naming-gate posture, do-not-collect adjacencies, legal notes
```

## 2. The compiler

A deterministic R2 tool (built BUILD-06): `compile-workbook <slug>` emits, from the workbook alone:

- `indexes/<slug>/jobs/*.md` — bounded job specs with acceptance criteria (R1 workflow stubs referenced, not auto-enabled).
- `indexes/<slug>/retrocast/spec.yaml` — SPEC-08 harness config, **pre-registration ready**.
- `indexes/<slug>/methodology/v0.md` — frozen-format methodology page source.
- `indexes/<slug>/site/` — page + artifact templates wired to the artifact compiler.
- Ops wiring diff: cron entries (odd-minute slots auto-assigned), heartbeat check assignment, alarm thresholds, permission-map classification.
- `indexes/<slug>/LAUNCH-GATE.md` — the gate file draft for SPEC-04, summarizing everything above.

**Rules:** compiler output is proposed via a single commit/PR — nothing it emits is live until the launch gate approves; recompiling an unchanged workbook is byte-identical (determinism); compiling a changed workbook on a *launched* index auto-classifies as a methodology gate.

## 3. Worked example (abbreviated) — the first workbook Phase 4 authors

```
# WORKBOOK: Shadow Recalls (NHTSA)
slug: nhtsa-recalls   family: product-safety   engine: E3 + retrocast harness
corpora: NHTSA complaints API + FLAT_CMPL (GREEN, ver. 2026-07-11); NHTSA recalls API (GREEN, same)
official_number: NHTSA recall announcements (continuous; lag removed = complaint-pattern → recall gap)
tier: aggregate (named watchlist = separate future gate after track record)
Retrocast: ground truth = all recalls 2015–2024 by make/model/year; signal = complaint
  volume/severity/narrative-hazard clustering in trailing windows; controls = matched
  never-recalled MMY cells; splits = train 2015–2020 / test 2021–2024; metrics = P/R curve,
  lead-time distribution, calibration; pass = pre-registered thresholds (set at authoring,
  before computation — SPEC-08 §2).
Artifacts: monthly category hazard-pressure chart; anomaly = category z>3; piggyback =
  every NHTSA recall announcement → "signal history for this MMY" receipt card.
Jobs: weekly complaints-delta compute (<15 min); monthly index recompute + artifact batch.
Covenant notes: aggregate-only launch; naming gate clock starts at retrocast publication.
```

## 4. Acceptance criteria (BUILD-06)

- Compiling the NHTSA workbook retroactively (it launched hand-built at BUILD-03/04) produces specs equivalent to what was built — divergences reconciled in BUILDLOG (the compiler must describe reality, or reality must be fixed).
- Legislative-Authorship and FOIA workbooks compile clean; their dry-run jobs meet their own acceptance criteria; determinism check passes.
- A deliberate workbook edit on a launched index auto-files a methodology gate.
