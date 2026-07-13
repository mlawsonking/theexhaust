# Playbook: weekly-ops (Mondays)

Runtime: R2 (scheduled `claude -p`, operator box, subscription). Time-box: 90 min. **No metered API.**
This is the session that gives Michael his ~1 hour. Follow the session contract exactly; do only
safe autonomous actions; anything gate-shaped becomes a gate file, never a direct action.

## 1. Bootstrap (STOP conditions are real)
- Read `OBSERVATORY.md`. Confirm phase + that this is the right runtime. If the constitution says a
  different phase/model owns this work, STOP and say so.
- `git pull` is unnecessary (single box); confirm a clean tree before starting.

## 2. Deterministic core (run the driver — do not hand-do these)
- Run: `python -m opscore.weekly`
  It sweeps decided/expired gates (expiry is always no-action), files a source gate for any
  collector that auto-paused on drift-3x, compiles this week's report to `ops/reports/{YYYY}/W{ww}.md`,
  runs the alarm-budget check (files a gate if breached), and pulses `exhaust-pulse` with the report link.
- Read the printed summary + the compiled report.

## 3. Judgment (the part that needs a mind, bounded)
- **Triage alarms/quarantine:** for each `exhaust-alarm` since last week and each `quarantine/…`
  snapshot, decide: transient (note it) or real (ensure a gate exists — file one if not). Do NOT
  un-pause a collector or change a threshold yourself; that's a gate.
- **Spot-verify one pipeline end-to-end** (rotating, name it in the report): pull yesterday's snapshot
  for one collector, revalidate its schema + manifest hash. Log pass/fail.
- **Do NOT** publish anything new, change any methodology, unlock any named tier, onboard any source,
  or spend anything. Those are gates. The safe default is: do nothing, keep collecting, ask.

## 4. Execute only DECIDED approvals
- For gates the operator has already marked `approve-*` (surfaced by the sweep as `executes: true`),
  carry out the approved action now (or schedule it) and note it. Never execute a `reject`, `defer`,
  `expired-no-action`, or free-text decision.

## 5. Verify → record → notify → die
- Verify: clean tree except the intended report/gate/state changes; any test you touched is green.
- Commit (`weekly ops: week {ww}`). The driver already pulsed `exhaust-pulse`. Exit — no background residue.
- Reading the report is optional for Michael; acting on gates is the only required operator labor.
