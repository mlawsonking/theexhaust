"""Deterministic weekly-ops driver (SPEC-02 §2 / SPEC-05). The weekly R2 session's non-judgment
steps, callable headless: sweep decided/expired gates, file gate items collectors requested
(drift-3x auto-pause), compile the gate report, run the alarm-budget check, pulse the report.
Returns a summary; the session wraps this with judgment (triage, spot-verify one pipeline) and
NEVER executes anything the operator didn't decide. No metered LLM here — this is pure orchestration.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from datetime import date

from . import gates, report
from .alarms import AlarmBus

# The futility clause (constitution, standing doctrine): a pre-registered hard-kill date. On/after
# it, the weekly driver auto-files a MANDATORY project-scoring gate. Sourced from CALENDAR.md so an
# operator override that re-arms the clause (a new pre-registered date) lands in one place; this
# constant is the fallback / original registration.
FUTILITY_DATE = date(2027, 12, 31)
FUTILITY_SLUG = "futility-clause"


def _pending(root):
    return os.path.join(root, "ops", "state", "QUEUE", "pending")


def _decided(root):
    return os.path.join(root, "ops", "state", "QUEUE", "decided")


def _futility_date(root) -> date:
    """The currently-ARMED kill date: the latest valid date on any CALENDAR.md futility line, else
    the original pre-registered constant.

    Hardened (W-005c/F08): the old version took the FIRST date on the FIRST line mentioning
    FUTILITY, so a stray earlier mention silently re-dated the constitutional kill review, and a
    malformed re-arm date silently reverted to 2027. Taking max() over every valid date on every
    futility line means a re-arm can only ever move the review LATER than an existing arming, and a
    typo cannot quietly disarm it — the clause is re-armed, never deleted."""
    cal = os.path.join(root, "ops", "state", "CALENDAR.md")
    found = []
    if os.path.exists(cal):
        for line in open(cal, encoding="utf-8"):
            if "FUTILITY" not in line.upper():
                continue
            for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2})", line):
                try:
                    found.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
                except ValueError:
                    continue                    # malformed (e.g. 2029-13-45) -> ignore, never disarm
    return max(found) if found else FUTILITY_DATE


def _futility_slug(fdate: date) -> str:
    """The gate slug carries the ARMED DATE, so each arming is its own gate (W-005c/F08). With a
    constant slug, the decided 2027 approve-override matched forever and a re-armed 2029 date could
    never file — silent continuation, exactly what the mandatory clause forbids."""
    return f"{FUTILITY_SLUG}-{fdate.isoformat()}"


def _futility_score(root) -> tuple[bool, str]:
    """Score the project against the pre-registered bar: >=2 PUBLISHED retrocasts AND >=1 external
    citation/use. Reads `ops/state/SCORECARD.json` if a later session wires publication tracking;
    pre-launch there is none, so the honest default is 0/0 -> bar unmet -> archive-mode is the
    standing default. This never *decides* — it only reports the score into the gate body."""
    pubs = cites = 0
    src = "no SCORECARD.json yet (nothing published) — bar unmet by construction"
    p = os.path.join(root, "ops", "state", "SCORECARD.json")
    if os.path.exists(p):
        try:
            d = json.load(open(p, encoding="utf-8"))
            pubs = int(d.get("published_retrocasts", 0))
            cites = int(d.get("external_citations", 0))
            src = "ops/state/SCORECARD.json"
        except Exception:
            pass
    met = pubs >= 2 and cites >= 1
    return met, f"{pubs} published retrocast(s), {cites} external citation(s) [{src}]"


def _futility_terminally_decided(root, slug) -> bool:
    """True once the operator has recorded a REAL terminal decision on the gate for THIS armed date
    (approve-*/reject/no-action). An expired-undecided gate (empty DECISION, swept to decided/) does
    NOT count — the clause is mandatory, so inaction re-files it rather than silently retiring it.

    Scoped to `slug` (which now carries the armed date) so a decision on the 2027 arming cannot
    satisfy a re-armed 2029 one (W-005c/F08). Legacy gates written under the bare constant still
    count for the ORIGINAL date, so an already-decided 2027 gate is not re-litigated."""
    base = _decided(root)
    if not os.path.isdir(base):
        return False
    accepted = {slug} | ({FUTILITY_SLUG} if slug == _futility_slug(FUTILITY_DATE) else set())
    for dirpath, _dirs, files in os.walk(base):
        for fn in files:
            if not (fn.startswith("GATE-") and fn.endswith(".md")):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                g = gates.parse(open(fp, encoding="utf-8").read(), fp)
            except Exception:
                continue
            if g.slug in accepted and g.is_decided:
                return True
    return False


def maybe_file_futility_gate(root, today, bus=None):
    """Constitution's futility clause. On/after the pre-registered date, file exactly one mandatory
    project-kill gate. Idempotent: skipped while one is pending or after a real decision; re-files if
    the operator let a prior one expire undecided (inaction may not silently kill OR silently continue
    the project). Returns the slug when it files, else None. Never executes anything — the archive-mode
    default is a posture the operator enacts, and gate expiry never executes (SPEC-04 §3)."""
    fdate = _futility_date(root)
    if today < fdate:
        return None
    slug = _futility_slug(fdate)
    pend = _pending(root)
    if any(g.slug in (slug, FUTILITY_SLUG) for g in gates.load_pending(pend)):
        return None
    if _futility_terminally_decided(root, slug):
        return None
    _met, detail = _futility_score(root)
    what = (
        f"The pre-registered futility date ({fdate.isoformat()}) has passed. This is the MANDATORY "
        "project-scoring gate (constitution, standing doctrine). It re-files every week until you "
        "record a written decision — inaction can neither silently kill nor silently continue the "
        "project.\n\n"
        f"Pre-registered bar: >=2 PUBLISHED retrocasts AND >=1 external citation/use.\n"
        f"Current score: {detail}.\n\n"
        "Constitutional default if the bar is unmet and you do not override IN WRITING: ARCHIVE-MODE "
        "— all publication freezes; every collector keeps running forever (the archive is the residual "
        "public good); a public plaque states these metrics and the why. Nothing is ever deleted.")
    options = (
        "A approve-archive — accept archive-mode (freeze publication, keep collecting, post the plaque)\n"
        "B approve-override — continue publishing; REQUIRES a written re-entry rationale AND a new "
        "pre-registered kill date recorded in notes: (the clause is re-armed, never deleted — update "
        "the CALENDAR.md futility line to the new date)")
    g = gates.new_gate(
        pend, slug,
        f"FUTILITY CLAUSE — mandatory project-kill review (pre-registered {fdate.isoformat()})",
        "other", by="weekly-session", what=what, options=options, created=today)
    if bus:
        bus.gate(g.title, g.path, today=today)
    return slug


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


def _ping_weekly_heartbeat(ok=True) -> str:
    """SPEC-03 §1 weekly-session dead-man: the weekly session is the one runner GitHub can't see, so
    a stopped Task Scheduler job would be silent. Pinging HC_WEEKLY on a clean completion lets
    healthchecks alarm if the session stops firing. Inert until the operator sets HC_WEEKLY (the
    check can only be created once the Task Scheduler job exists — else it false-alarms). Never crashes
    the session."""
    url = os.environ.get("HC_WEEKLY", "").strip()
    if not url:
        return "unset"
    try:
        urllib.request.urlopen(url if ok else url.rstrip("/") + "/fail", timeout=15)
        return "pinged"
    except Exception as e:  # a heartbeat failing to send must never crash the weekly session
        return f"err:{type(e).__name__}"


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
    # 5. futility clause (constitution): on/after the pre-registered date, auto-file the mandatory
    #    project-kill gate. Runs AFTER the sweep so an expired-undecided prior futility gate re-files
    #    this week (it is mandatory — inaction must not silently retire it).
    futility = maybe_file_futility_gate(root, today, bus=bus)
    # 6. pulse: report ready
    bus.pulse(f"Weekly report W{week_num:02d} ready", report_path, today=today)
    # 7. weekly-session dead-man heartbeat (inert until HC_WEEKLY is set — see _ping_weekly_heartbeat)
    heartbeat = _ping_weekly_heartbeat(ok=True)
    return {"report": report_path, "gate_actions": actions,
            "executed": [a for a in actions if a["executes"]],
            "gates_filed": filed, "alarm_budget_breach": breach,
            "futility_gate_filed": futility, "weekly_heartbeat": heartbeat}


if __name__ == "__main__":  # invoked by the weekly R2 session (SPEC-02 §2)
    from datetime import date
    _t = date.today()
    _res = run_weekly(".", _t, _t.isocalendar().week)
    print(json.dumps({k: v for k, v in _res.items() if k != "gate_actions"}, indent=2, default=str))
