"""Deterministic weekly-ops driver (SPEC-02 §2 / SPEC-05). The weekly R2 session's non-judgment
steps, callable headless: sweep decided/expired gates, file gate items collectors requested
(drift-3x auto-pause), compile the gate report, run the alarm-budget check, pulse the report.
Returns a summary; the session wraps this with judgment (triage, spot-verify one pipeline) and
NEVER executes anything the operator didn't decide. No metered LLM here — this is pure orchestration.
"""
from __future__ import annotations

import json
import os

from . import gates, report
from .alarms import AlarmBus


def _pending(root):
    return os.path.join(root, "ops", "state", "QUEUE", "pending")


def _decided(root):
    return os.path.join(root, "ops", "state", "QUEUE", "decided")


def file_collector_gates(root, health, today):
    """A collector that auto-paused (needs_gate set by the framework on drift-3x) gets exactly one
    source gate — de-duplicated by slug so repeated weekly runs don't spam the board."""
    pend = _pending(root)
    existing = {g.slug for g in gates.load_pending(pend)}
    filed = []
    for name, rec in (health.get("collectors") or {}).items():
        ng = rec.get("needs_gate")
        if not ng:
            continue
        slug = f"collector-{name}-{ng}"
        if slug in existing:
            continue
        gates.new_gate(pend, slug, f"Collector {name}: {ng}", "source", by="weekly-session",
                       what=f"Collector {name} auto-paused after {ng}. Investigate, then re-enable or re-scope the source.",
                       options="A investigate + re-enable / B re-scope the source / C leave paused",
                       created=today)
        filed.append(slug)
    return filed


def run_weekly(root, today, week_num, bus=None):
    bus = bus or AlarmBus(ledger_path=os.path.join(root, "ops", "state", "ALARMS.jsonl"))
    # 1. sweep decided/expired gates (execution of approvals is the session's job, not sweep's)
    actions = gates.sweep(_pending(root), _decided(root), today)
    # 2. file gates for collectors that asked for one — read the merged per-collector state
    # (W-002b), then materialize the merged legacy view so HEALTH.json stays human-readable and
    # SPEC-02-compliant (this write is committed by the weekly session).
    health = report.merged_health(root)
    hp = os.path.join(root, "ops", "state", "HEALTH.json")
    os.makedirs(os.path.dirname(hp), exist_ok=True)
    json.dump(health, open(hp, "w", encoding="utf-8"), indent=2)
    filed = file_collector_gates(root, health, today)
    # 3. compile the operator report (decisions-as-headline, orphan clock, etc.)
    report_path = report.compile_from_repo(root, today, week_num)
    # 4. alarm-budget check -> gate item if breached
    breach = bus.budget_breach(today)
    if breach:
        bus.gate("Alarm budget breached — fix the root cause or mute with a recorded decision",
                 json.dumps(breach), today=today)
    # 5. pulse: report ready
    bus.pulse(f"Weekly report W{week_num:02d} ready", report_path, today=today)
    return {"report": report_path, "gate_actions": actions,
            "executed": [a for a in actions if a["executes"]],
            "gates_filed": filed, "alarm_budget_breach": breach}


if __name__ == "__main__":  # invoked by the weekly R2 session (SPEC-02 §2)
    from datetime import date
    _t = date.today()
    _res = run_weekly(".", _t, _t.isocalendar().week)
    print(json.dumps({k: v for k, v in _res.items() if k != "gate_actions"}, indent=2, default=str))
