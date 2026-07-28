# Playbook: kill-one-collector drill (SPEC-03 §6)

**Goal:** prove that a stopped collector produces an *audible phone alarm* — that the whole dead-man
chain works: `collector stops → healthchecks grace expires → healthchecks notifies ntfy → phone`.
"A silently-stopped collector is an alarm, never a discovery" (constitution).

**Prerequisite (W-003 item 1):** the collector checks exist in healthchecks and an **ntfy integration**
(topic `theexhaust-75Z`) is attached (checks are created with `channels:"*"`, so one integration covers
all). Run `python ops/setup/healthchecks_setup.py --apply` first if not. Until then this drill cannot run.

---

## Path A — fast chain proof (~1 min, **skips no collection window**) — DO THIS FIRST

This forces one check "down" via healthchecks' `/fail` endpoint and confirms the ntfy alarm lands,
without disabling any collector — so no real collection window is missed (archival-first covenant).

1. Pick a check (e.g. `nhtsa-recalls`). Its ping URL is the `HC_NHTSA_RECALLS` value (from the HC
   dashboard). Force it down:
   ```bash
   curl -fsS "https://hc-ping.com/<uuid>/fail" && echo " -> failed"
   ```
2. Within a few seconds healthchecks flips the check to **down** and fires the ntfy integration.
   **Confirm the high-priority alarm arrives on the phone.** (If not: the ntfy integration isn't
   attached — fix in the HC dashboard, Integrations.)
3. Recover the check (so it's green again and won't keep alarming):
   ```bash
   curl -fsS "https://hc-ping.com/<uuid>" && echo " -> recovered"
   ```
   The collector's next real firing would also recover it.

Pass = the phone received an audible alarm in step 2 and the check returned to "up" in step 3.

## Path B — true grace-window drill (real wall-clock; run periodically, not every session)

Proves healthchecks' *detection* (grace timeout), not just the notification wiring. Costs real time
and, if you disable a schedule, risks the archival-first covenant — so pick a collector whose next
window is far off and **re-enable promptly**.

1. Disable one collector's schedule (keeps `workflow_dispatch`, so you can still collect manually):
   ```bash
   gh workflow disable collect-nhtsa-recalls.yml
   ```
   (or comment out the `schedule:` block on a branch). **Note the grace window** for that check from
   `ops/setup/healthchecks_setup.py` output — e.g. nhtsa-recalls grace = 6d.
2. Do not ping. After the grace elapses past the next expected firing, healthchecks fires → ntfy
   alarm on the phone. Confirm receipt and the timestamp is within grace.
3. **Re-enable immediately** and collect the missed window so nothing is lost:
   ```bash
   gh workflow enable collect-nhtsa-recalls.yml
   gh workflow run collect-nhtsa-recalls.yml     # backfill the skipped firing
   ```

Pass = the alarm fired within the check's grace window and no collection window was permanently lost.

---

**Alarm-budget note (SPEC-03 §4):** drill alarms count toward the alarm ledger only when routed through
`opscore.alarms` (they are not — these are healthchecks-originated). If you ever wire drill alarms through
the bus, record the drill so the >5/week-for-2-weeks budget check doesn't misfire.
