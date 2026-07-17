# Playbook: monthly-audit (first Monday)

Runtime: R2 (scheduled `claude -p`). Time-box: 90 min. **No metered API.** Runs after (or as part of)
the weekly session and appends a one-page audit section to that week's report (SPEC-05 §3).

## 1. Bootstrap
- Read `OBSERVATORY.md`; confirm phase/runtime; STOP on mismatch. Confirm a clean tree.

## 2. Audit checklist (record each result in the report's monthly section)
- **Alarm-budget review:** list every active mute; confirm each still has a decision file. A mute
  without a recorded decision is prohibited — file a gate to fix or remove it.
- **Budget reconciliation:** compare `ops/state/BUDGET.json` against the Cloudflare R2 usage and (if any
  gated runs happened) the Anthropic console. Update the storage projection from the manifests. If R2
  projection > $5/mo, that's already a gate; confirm it exists.
- **Storage projection:** recompute GB from `raw/…/manifest.json` row/byte totals; write it to BUDGET.json.
- **Covenant spot-check:** pick 2 collectors at random; audit their code against SPEC-01 §4 (honest UA,
  no circumvention, robots/ToS, dedupe) and the do-not-collect register. `python ci/covenant_guard.py`
  must be green.
- **ToS re-verify rotation:** refresh the `verified` date on ONE research §5 corpus row (rotate monthly);
  if reality drifted from the spec, STOP and file a gate rather than improvise.
- **Orphan-clock check:** confirm the clock reflects reality; if the operator has been away, verify
  orphan-mode behavior is correct (collectors still running, gated surfaces frozen).
- **Scope-ledger trigger review:** walk `docs/05-SCOPE-LEDGER.md`; for every TRIGGERED row, check
  whether its condition now holds (they are checkable facts by design). Each fired trigger → file a
  gate (never auto-build). Note fired/unfired counts in the audit section.
- **Futility-clause horizon:** state months remaining to 2027-12-31 and the current standing vs the
  bar (published retrocasts count, external citations count). No spin — the number is the number.

## 3. Verify → record → notify → die
- Append the audit section to `ops/reports/{YYYY}/W{ww}.md`; commit (`monthly audit: {YYYY}-{MM}`).
- ntfy `exhaust-pulse` with the audit summary. Exit clean.
