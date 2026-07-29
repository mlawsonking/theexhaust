"""ops-core tests (offline, deterministic). Run:
    python -m opscore.tests.test_opscore        # plain asserts, no pytest
    python -m pytest opscore/tests/test_opscore.py
"""
from __future__ import annotations

import json
import os
from datetime import date, timedelta

from opscore import gates, orphan, report, weekly
from opscore.alarms import AlarmBus, NullNtfySender
from opscore.budget import Budget, GatedRun, CapExceeded


# ------------------------------------------------------------------ gates
def test_gate_roundtrip_decide_sweep(tmp_path):
    pending = tmp_path / "pending"
    decided = tmp_path / "decided"
    g = gates.new_gate(str(pending), "test-source", "Onboard the FOO source", "source",
                       by="job:test", what="We want FOO.", options="A recommended / B",
                       created=date(2026, 7, 1))
    assert g.validate() == []
    # parse round-trips the fields
    parsed = gates.parse(open(g.path, encoding="utf-8").read(), g.path)
    assert parsed.title == "Onboard the FOO source"
    assert parsed.type == "source"
    assert parsed.by == "job:test"
    assert not parsed.is_decided

    # undecided before expiry -> stays pending on sweep
    assert gates.sweep(str(pending), str(decided), date(2026, 7, 10)) == []

    # operator decides approve-A -> sweep moves it and marks it executes
    parsed.decision = "approve-A"
    open(g.path, "w", encoding="utf-8").write(gates.to_text(parsed))
    actions = gates.sweep(str(pending), str(decided), date(2026, 7, 10))
    assert len(actions) == 1 and actions[0]["outcome"] == "approve-A" and actions[0]["executes"] is True
    assert not os.path.exists(g.path)  # moved out of pending


def test_gate_expiry_never_executes(tmp_path):
    pending = tmp_path / "pending"
    decided = tmp_path / "decided"
    g = gates.new_gate(str(pending), "stale-thing", "Something nobody decided", "other",
                       by="job:test", what="x", created=date(2026, 6, 1), expiry_days=28)
    actions = gates.sweep(str(pending), str(decided), date(2026, 7, 10))  # past expiry
    assert actions[0]["outcome"] == "expired-no-action"
    assert actions[0]["executes"] is False  # expiry NEVER executes (SPEC-04 §3)


def test_gate_unsafe_default_rejected(tmp_path):
    try:
        gates.new_gate(str(tmp_path), "bad", "Bad gate", "spend", by="x", what="y",
                       created=date(2026, 7, 1), estimate_usd=10, hard_cap_usd=20,
                       default_on_expiry="approve-A")
        assert False, "should have rejected an executing default_on_expiry"
    except ValueError:
        pass


def test_gate_priority_order():
    ranks = [gates.Gate(type=t).priority_rank() for t in ("legal", "spend", "comms")]
    assert ranks == sorted(ranks)
    assert gates.Gate(type="legal").priority_rank() < gates.Gate(type="comms").priority_rank()


# ------------------------------------------------------------------ budget
def test_budget_cap_aborts():
    run = GatedRun("r1", "GATE-x", estimate_usd=0.90, hard_cap_usd=1.00)
    run.charge(1_000_000, 100_000)  # $0.50 in + $0.25 out = $0.75
    try:
        run.charge(1_000_000, 100_000)  # would reach $1.50 > $1.00 cap
        assert False, "cap not enforced"
    except CapExceeded:
        pass
    assert run.actual_usd <= run.hard_cap_usd


def test_budget_storage_math():
    assert Budget.storage_cost(5) == 0.0            # inside 10 GB free
    assert abs(Budget.storage_cost(110) - (100 * 0.015)) < 1e-9  # 100 GB billable -> $1.50
    b = Budget({})
    b.set_storage(110)
    assert b.storage_alarm() is False               # $1.50 < $5 threshold
    b.set_storage(500)
    assert b.storage_alarm() is True                # ~$7.35 > $5


def test_budget_records_run():
    b = Budget({})
    run = GatedRun("r2", "GATE-y", 0.05, 0.20)
    run.charge(80_000, 20_000)
    b.record_run(run, date(2026, 7, 13))
    assert b.data["metered_runs"][0]["run_id"] == "r2"
    assert b.month_metered_usd("2026-07") == b.data["metered_runs"][0]["actual"]


# ------------------------------------------------------------------ orphan
def test_orphan_states():
    ack = date(2026, 7, 1)
    assert orphan.status(date(2026, 7, 8), ack).state == "active"    # 1 wk
    assert orphan.status(date(2026, 7, 22), ack).state == "warn"     # 3 wk
    st = orphan.status(date(2026, 7, 29), ack)                       # 4 wk
    assert st.state == "orphan" and st.is_orphaned and st.weeks_to_freeze == 0
    # a later gate DECISION resets the clock
    assert orphan.status(date(2026, 7, 29), ack, [date(2026, 7, 28)]).state == "active"
    # no signal at all -> treated as orphaned (safe)
    assert orphan.status(date(2026, 7, 29), None).state == "orphan"


def test_orphan_report_line():
    assert orphan.report_line(orphan.status(date(2026, 7, 8), date(2026, 7, 8))) is None  # 0 wk -> omit
    line = orphan.report_line(orphan.status(date(2026, 7, 22), date(2026, 7, 1)))
    assert "weeks to autonomous freeze" in line


# ------------------------------------------------------------------ report
def test_report_nothing_needed():
    md = report.compile_report(health={"collectors": {}}, pending_gates=[], budget_data={},
                               calendar_text="", ack_text="last-active: 2026-07-13",
                               today=date(2026, 7, 13), week_num=29)
    assert "Nothing needs you this week." in md
    assert md.count("\n") <= report.LENGTH_CAP


def test_report_decisions_headline_and_order():
    g_comms = gates.Gate(title="Send digest", type="comms", created="2026-07-01",
                         expires="2026-07-29", default_on_expiry="no-action", path="/q/GATE-c.md")
    g_legal = gates.Gate(title="Answer C&D", type="legal", created="2026-07-02",
                         expires="2026-07-30", default_on_expiry="no-action", path="/q/GATE-l.md")
    md = report.compile_report(health={"collectors": {"cms-deficiencies": {"last_action": "stored"}}},
                               pending_gates=[g_comms, g_legal], budget_data={"storage": {"r2_gb": 0.1}},
                               calendar_text="- 2026-07-20 something due", ack_text="last-active: 2026-07-13",
                               today=date(2026, 7, 13), week_num=29)
    assert "You need to decide 2 things" in md
    assert md.index("Answer C&D") < md.index("Send digest")   # legal before comms
    assert "something due" in md                               # calendar within 30 days
    assert "1/1 green" in md


def test_gate_defer_and_freetext(tmp_path):
    # 'defer <date>' is NOT terminal: stays pending, hidden until the date, and does not expire meanwhile
    g = gates.Gate(decision="defer 2026-09-01", expires="2026-07-20", created="2026-07-01")
    assert not g.is_decided
    assert g.is_deferred(date(2026, 7, 13)) and g.defer_until == date(2026, 9, 1)
    assert g.resolve(date(2026, 7, 13)).startswith("deferred until")
    assert not g.is_expired(date(2026, 7, 25))  # deferred gate doesn't expire in-window
    # free-text note leaves the gate pending (not swept out)
    fg = gates.Gate(decision="pending - need legal input")
    assert not fg.is_decided and fg.resolve(date(2026, 7, 13)) == "pending"
    # sweep leaves a deferred gate in pending
    pend, dec = tmp_path / "pending", tmp_path / "decided"
    dg = gates.new_gate(str(pend), "defer-me", "Defer me", "source", by="x", what="y", created=date(2026, 7, 1))
    p = gates.parse(open(dg.path, encoding="utf-8").read(), dg.path)
    p.decision = "defer 2026-09-01"
    open(dg.path, "w", encoding="utf-8").write(gates.to_text(p))
    assert gates.sweep(str(pend), str(dec), date(2026, 7, 13)) == []
    assert os.path.exists(dg.path)  # still pending


def test_orphan_future_signal_ignored():
    # a future-dated decision (e.g. a defer date) must NOT reset a stale clock (fail-safe)
    st = orphan.status(date(2026, 7, 13), date(2026, 6, 1), [date(2026, 9, 1)])
    assert st.state == "orphan"


def test_report_orphan_survives_truncation():
    many = [gates.Gate(title=f"Decide thing {i}", type="source", created="2026-07-01",
                       expires="2026-08-01", default_on_expiry="no-action", path=f"/q/GATE-{i}.md")
            for i in range(200)]
    md = report.compile_report(health={"collectors": {}}, pending_gates=many, budget_data={},
                               calendar_text="", ack_text="last-active: 2026-06-01",
                               today=date(2026, 7, 13), week_num=29)
    assert "## 6) Orphan clock" in md                 # safety line survived the truncation
    assert "truncated at length cap" in md
    assert len(md.splitlines()) <= report.LENGTH_CAP + 3


# ------------------------------------------------------------------ alarms + weekly
def test_alarm_routing_and_budget(tmp_path):
    s = NullNtfySender()
    bus = AlarmBus(sender=s, topics={"alarm": "A", "gate": "G", "pulse": "P"},
                   ledger_path=str(tmp_path / "ALARMS.jsonl"))
    bus.alarm("boom", today=date(2026, 7, 13))
    bus.gate("decide", today=date(2026, 7, 13))
    bus.pulse("report", today=date(2026, 7, 13))
    assert s.sent[0]["topic"] == "A" and s.sent[0]["priority"] == "high"
    assert s.sent[1]["topic"] == "G"
    assert s.sent[2]["topic"] == "P" and s.sent[2]["priority"] == "low"
    # >5 alarms in BOTH recent weeks -> budget breach (SPEC-03 §4)
    for d in (date(2026, 7, 10), date(2026, 7, 3)):
        for _ in range(6):
            bus.alarm("x", today=d)
    assert bus.budget_breach(date(2026, 7, 13))["breached"] is True
    # a quiet ledger -> no breach
    q = AlarmBus(sender=NullNtfySender(), topics={}, ledger_path=str(tmp_path / "q.jsonl"))
    q.alarm("one", today=date(2026, 7, 13))
    assert q.budget_breach(date(2026, 7, 13)) is None


def test_alarmbus_inert_without_topics():
    # no topics configured -> defaults to the null (no-network) sender, silently inert
    bus = AlarmBus(topics={})
    assert isinstance(bus.sender, NullNtfySender)
    bus.alarm("nothing happens")  # must not raise


def test_weekly_run_compiles_and_files_collector_gate(tmp_path):
    state = tmp_path / "ops" / "state"
    (state / "QUEUE" / "pending").mkdir(parents=True)
    (state / "QUEUE" / "decided").mkdir(parents=True)
    (state / "HEALTH.json").write_text(json.dumps({"collectors": {
        "cms-deficiencies": {"last_action": "quarantined-drift", "needs_gate": "schema-drift-3x", "paused": True}}}),
        encoding="utf-8")
    (state / "BUDGET.json").write_text(json.dumps({"storage": {"r2_gb": 0.0, "projection_usd_mo": 0.0}}), encoding="utf-8")
    (state / "CALENDAR.md").write_text("# cal\n", encoding="utf-8")
    (state / "ACK").write_text("last-active: 2026-07-13\n", encoding="utf-8")
    bus = AlarmBus(sender=NullNtfySender(), topics={"alarm": "A", "gate": "G", "pulse": "P"},
                   ledger_path=str(state / "ALARMS.jsonl"))
    res = weekly.run_weekly(str(tmp_path), date(2026, 7, 13), 29, bus=bus)
    assert os.path.exists(res["report"])
    assert res["gates_filed"] == ["collector-cms-deficiencies-schema-drift-3x"]
    # a second run must NOT double-file the same collector gate
    res2 = weekly.run_weekly(str(tmp_path), date(2026, 7, 13), 29, bus=bus)
    assert res2["gates_filed"] == []


def test_merged_health_per_collector_plus_legacy(tmp_path):
    """W-002b: per-collector `ops/state/health/*.json` are authoritative; legacy HEALTH.json only
    fills gaps for collectors not yet split out; `generated` is the max across all sources."""
    hdir = tmp_path / "ops" / "state" / "health"
    hdir.mkdir(parents=True)
    (hdir / "cms-deficiencies.json").write_text(json.dumps(
        {"generated": "2026-07-28T10:00:00Z",
         "collectors": {"cms-deficiencies": {"last_action": "stored", "last_hash": "aaa"}}}))
    (hdir / "nhtsa-recalls.json").write_text(json.dumps(
        {"generated": "2026-07-28T11:00:00Z",
         "collectors": {"nhtsa-recalls": {"last_action": "unchanged", "last_hash": "bbb"}}}))
    # legacy: a STALE cms record (must be overridden) + a collector present only in legacy (fallback)
    (tmp_path / "ops" / "state" / "HEALTH.json").write_text(json.dumps(
        {"generated": "2026-07-27T00:00:00Z",
         "collectors": {"cms-deficiencies": {"last_action": "stored", "last_hash": "STALE"},
                        "fdic-failures": {"last_action": "stored", "last_hash": "ccc"}}}))
    m = report.merged_health(str(tmp_path))
    cols = m["collectors"]
    assert set(cols) == {"cms-deficiencies", "nhtsa-recalls", "fdic-failures"}
    assert cols["cms-deficiencies"]["last_hash"] == "aaa"     # per-collector file wins over STALE
    assert cols["nhtsa-recalls"]["last_hash"] == "bbb"
    assert cols["fdic-failures"]["last_hash"] == "ccc"        # legacy-only collector filled in
    assert m["generated"] == "2026-07-28T11:00:00Z"           # max across sources
    b = report._collector_board(m)
    assert b["total"] == 3 and b["green"] == 3


# ------------------------------------------------------------------ healthchecks provisioning
def test_healthchecks_cron_gap_and_grace():
    from opscore import healthchecks as hc
    # ats 3x/day (01/09/17): 8h max gap -> grace 12h
    assert abs(hc._cron_max_gap_hours("13 1,9,17 * * *") - 8.0) < 1e-6
    assert hc._grace_seconds(8.0) == 12 * 3600
    # Mon+Thu (recalls/cms): Thu->Mon is the 4d (96h) gap -> grace 6d
    assert abs(hc._cron_max_gap_hours("29 6 * * 1,4") - 96.0) < 1e-6
    assert hc._grace_seconds(96.0) == 144 * 3600
    # weekly single (fdic Sat / complaints Wed): 7d (168h) gap -> grace 252h (10.5d)
    assert abs(hc._cron_max_gap_hours("43 8 * * 6") - 168.0) < 1e-6
    assert hc._grace_seconds(168.0) == 252 * 3600
    # a day-of-month cron is unsupported and must fail loud (never a silently-wrong grace)
    try:
        hc._cron_max_gap_hours("0 0 1 * *")
        assert False, "day-of-month cron should raise"
    except ValueError:
        pass


def test_healthchecks_collector_specs_match_workflows():
    from opscore import healthchecks as hc
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    specs = {s["collector"]: s for s in hc.collector_specs(os.path.join(repo_root, ".github", "workflows"))}
    # every live collector workflow yields exactly one check bound to the secret the runner consumes
    # (8 since W-007b added cms-pbj — this set is what ⚑ #212 provisions, so it is pinned on purpose)
    assert set(specs) == {"ats-boards", "cms-deficiencies", "cms-pbj", "cpsc-recalls",
                          "fdic-failures", "nhtsa-complaints", "nhtsa-recalls", "warn"}
    assert specs["nhtsa-recalls"]["secret"] == "HC_NHTSA_RECALLS"
    assert specs["warn"]["secret"] == "HC_WARN"                # C2 WARN fleet = one shared logical check
    assert specs["cms-pbj"]["secret"] == "HC_CMS_PBJ"          # C1 staffing fleet = one shared check
    assert specs["ats-boards"]["grace"] == 12 * 3600           # 8h firing gap -> 12h grace
    assert specs["warn"]["grace"] == 18 * 3600                 # 12h firing gap (2x/day) -> 18h grace
    assert specs["fdic-failures"]["grace"] == 252 * 3600       # weekly -> 10.5d grace
    for s in specs.values():
        assert s["channels"] == "*" and s["name"].startswith("exhaust-collect-")
        assert s["grace"] > s["max_gap_hours"] * 3600          # grace strictly exceeds one firing gap


def test_weekly_heartbeat_inert_without_env():
    # HC_WEEKLY unset -> the SPEC-03 §1 weekly dead-man ping is inert and never raises
    os.environ.pop("HC_WEEKLY", None)
    assert weekly._ping_weekly_heartbeat() == "unset"


def _futility_state(root, calendar_text):
    state = root / "ops" / "state"
    (state / "QUEUE" / "pending").mkdir(parents=True)
    (state / "QUEUE" / "decided").mkdir(parents=True)
    (state / "CALENDAR.md").write_text(calendar_text, encoding="utf-8")
    return state / "QUEUE" / "pending", state / "QUEUE" / "decided"


def test_futility_date_parse_and_fallback(tmp_path):
    (tmp_path / "ops" / "state").mkdir(parents=True)
    # no calendar -> the pre-registered constant
    assert weekly._futility_date(str(tmp_path)) == date(2027, 12, 31)
    # a re-armed date on the CALENDAR futility line is honored
    (tmp_path / "ops" / "state" / "CALENDAR.md").write_text(
        "- 2029-06-30 — THE FUTILITY CLAUSE fires (re-armed)\n", encoding="utf-8")
    assert weekly._futility_date(str(tmp_path)) == date(2029, 6, 30)


def test_futility_gate_fires_on_and_after_date(tmp_path):
    pend, _dec = _futility_state(tmp_path, "- 2027-12-31 — THE FUTILITY CLAUSE fires\n")
    # before the date: nothing
    assert weekly.maybe_file_futility_gate(str(tmp_path), date(2027, 12, 30)) is None
    assert gates.load_pending(str(pend)) == []
    # on the date: exactly one mandatory futility gate, carrying the bar + archive-mode default
    # (the slug carries the ARMED DATE since W-005c/F08, so each arming is its own gate)
    assert weekly.maybe_file_futility_gate(str(tmp_path), date(2027, 12, 31)) == "futility-clause-2027-12-31"
    filed = gates.load_pending(str(pend))
    assert len(filed) == 1 and filed[0].slug == "futility-clause-2027-12-31"
    body = (filed[0].what + filed[0].options).lower()
    assert "archive-mode" in body and "override" in body and "citation" in body
    assert filed[0].validate() == []
    # idempotent while pending: a later call does NOT double-file
    assert weekly.maybe_file_futility_gate(str(tmp_path), date(2028, 1, 7)) is None
    assert len(gates.load_pending(str(pend))) == 1


def test_futility_gate_refiles_on_expiry_but_stops_after_decision(tmp_path):
    pend, dec = _futility_state(tmp_path, "- 2027-12-31 FUTILITY CLAUSE\n")
    weekly.maybe_file_futility_gate(str(tmp_path), date(2027, 12, 31))
    # let it expire UNDECIDED -> sweep files it away as expired-no-action (never executes)
    gates.sweep(str(pend), str(dec), date(2028, 2, 1))
    assert gates.load_pending(str(pend)) == []
    # mandatory: an ignored futility gate re-files (inaction may not silently retire the kill review)
    assert weekly.maybe_file_futility_gate(str(tmp_path), date(2028, 2, 1)) == "futility-clause-2027-12-31"
    # operator records a REAL decision -> it must stop re-filing
    g = gates.load_pending(str(pend))[0]
    parsed = gates.parse(open(g.path, encoding="utf-8").read(), g.path)
    parsed.decision = "approve-override"
    open(g.path, "w", encoding="utf-8").write(gates.to_text(parsed))
    gates.sweep(str(pend), str(dec), date(2028, 2, 8))     # moves the decided gate to decided/
    assert weekly.maybe_file_futility_gate(str(tmp_path), date(2028, 2, 15)) is None


def test_weekly_run_files_futility_after_date(tmp_path):
    state = tmp_path / "ops" / "state"
    (state / "QUEUE" / "pending").mkdir(parents=True)
    (state / "QUEUE" / "decided").mkdir(parents=True)
    (state / "HEALTH.json").write_text(json.dumps({"collectors": {}}), encoding="utf-8")
    (state / "BUDGET.json").write_text(json.dumps({"storage": {}}), encoding="utf-8")
    (state / "CALENDAR.md").write_text("- 2027-12-31 — THE FUTILITY CLAUSE fires\n", encoding="utf-8")
    (state / "ACK").write_text("last-active: 2027-12-31\n", encoding="utf-8")
    bus = AlarmBus(sender=NullNtfySender(), topics={"alarm": "A", "gate": "G", "pulse": "P"},
                   ledger_path=str(state / "ALARMS.jsonl"))
    res = weekly.run_weekly(str(tmp_path), date(2027, 12, 31), 52, bus=bus)
    assert res["futility_gate_filed"] == "futility-clause-2027-12-31"
    assert any("FUTILITY" in s["title"].upper() and s["topic"] == "G" for s in bus.sender.sent)
    # before the date, the same driver files no futility gate
    state2 = tmp_path / "before" / "ops" / "state"
    (state2 / "QUEUE" / "pending").mkdir(parents=True)
    (state2 / "QUEUE" / "decided").mkdir(parents=True)
    (state2 / "HEALTH.json").write_text(json.dumps({"collectors": {}}), encoding="utf-8")
    (state2 / "BUDGET.json").write_text(json.dumps({"storage": {}}), encoding="utf-8")
    (state2 / "CALENDAR.md").write_text("- 2027-12-31 — THE FUTILITY CLAUSE fires\n", encoding="utf-8")
    (state2 / "ACK").write_text("last-active: 2026-07-13\n", encoding="utf-8")
    res2 = weekly.run_weekly(str(tmp_path / "before"), date(2026, 7, 13), 29,
                             bus=AlarmBus(sender=NullNtfySender(), topics={}, ledger_path=str(state2 / "A.jsonl")))
    assert res2["futility_gate_filed"] is None


# ------------------------------------------------------------------ fleet-green (SPEC-01 §6)
def test_fleet_green_scoring():
    """W-005: the rule that decides BUILD-01's 'green 7 consecutive days' criterion. A window is
    green only if every firing in it succeeded and the committed state is neither quarantined nor
    paused; cadences run daily..weekly, so a green window is NOT 'a run every day'."""
    from opscore.fleetgreen import FLEET, day_of_manifest_key, score
    window = [date(2026, 7, 29) + timedelta(days=i) for i in range(7)]      # 07-29 .. 08-04

    runs = [{"day": "2026-07-30", "conclusion": "success"},
            {"day": "2026-08-03", "conclusion": "success"}]
    s = score(runs, {"2026-07-30"}, {"last_action": "stored", "paused": False}, window)
    assert s["green"] and s["verdict"] == "GREEN" and s["ok_days"] == ["2026-07-30", "2026-08-03"]
    assert s["manifest_days"] == ["2026-07-30"]          # weekly collector, one manifest — still green

    # one failed firing anywhere in the window breaks it (the real nhtsa-recalls startup_failure case)
    bad = score(runs + [{"day": "2026-08-01", "conclusion": "startup_failure"}], set(),
                {"last_action": "stored"}, window)
    assert not bad["green"] and bad["verdict"] == "FAILED-RUN" and bad["failed_days"] == ["2026-08-01"]

    # runs OUTSIDE the window neither help nor hurt
    assert score([{"day": "2026-07-28", "conclusion": "success"}], set(), {}, window)["verdict"] \
        == "NO-FIRING-IN-WINDOW"
    # quarantine / pause in committed state override successful runs
    assert score(runs, set(), {"last_action": "quarantined-drift"}, window)["verdict"] == "QUARANTINED"
    assert score(runs, set(), {"last_action": "stored", "paused": True}, window)["verdict"] == "PAUSED"

    assert day_of_manifest_key("raw/warn/CA/2026/07/28/manifest.json") == "2026-07-28"
    assert day_of_manifest_key("raw/cms-deficiencies/2026/07/28/0552-abc.csv.zst") is None
    assert "kroger" not in FLEET                          # C7 stays dark (SPEC-01 §2 C7)


def test_fleet_green_state_and_run_evidence(tmp_path):
    """W-005c/F09+F10 — the two evidence bugs sitting under the BUILD-01 acceptance check.
    A synthetic 7-day window over a real repo layout: unreadable committed state must never read
    GREEN (lenient direction), and an in-flight run must never read FAILED (strict direction)."""
    from opscore.fleetgreen import UNREADABLE, committed_state, run_rows, score
    window = [date(2026, 7, 29) + timedelta(days=i) for i in range(7)]      # 07-29 .. 08-04
    hdir = tmp_path / "ops" / "state" / "health"
    hdir.mkdir(parents=True)
    runs = [{"day": "2026-07-30", "conclusion": "success"}]

    # (a) truncated / conflict-marked state file -> STATE-UNREADABLE, never a vacuous GREEN
    (hdir / "warn.json").write_text('{"collectors": {"warn": {"last_act')
    st = committed_state(str(tmp_path), "warn")
    assert UNREADABLE in st
    s = score(runs, set(), st, window)
    assert s["green"] is False and s["verdict"] == "STATE-UNREADABLE" and s["state_unreadable"]

    # (b) a state file whose collector record is missing entirely is also unreadable, not empty
    (hdir / "warn.json").write_text(json.dumps({"collectors": {"something-else": {}}}))
    assert UNREADABLE in committed_state(str(tmp_path), "warn")

    # (c) a healthy committed record reads GREEN
    (hdir / "warn.json").write_text(json.dumps(
        {"collectors": {"warn": {"last_action": "stored", "paused": False}}}))
    assert score(runs, set(), committed_state(str(tmp_path), "warn"), window)["verdict"] == "GREEN"

    # (d) a quarantined record now REACHES this check (F01 makes fleets write it) and is not green
    (hdir / "warn.json").write_text(json.dumps(
        {"collectors": {"warn": {"last_action": "quarantined", "quarantined": 1}}}))
    assert score(runs, set(), committed_state(str(tmp_path), "warn"), window)["verdict"] == "QUARANTINED"

    # (e) absent file = not yet committed, which is not corruption
    assert committed_state(str(tmp_path), "cpsc-recalls") == {}

    # (f) in-flight runs are dropped by run_rows and ignored by score -> no false FAILED-RUN
    raw = [{"conclusion": "success", "createdAt": "2026-07-30T04:17:00Z", "databaseId": 1, "event": "schedule"},
           {"conclusion": None, "createdAt": "2026-08-04T04:17:00Z", "databaseId": 2, "event": "schedule"}]
    rows = run_rows(raw)
    assert [r["day"] for r in rows] == ["2026-07-30"]
    good = score(rows, set(), {"last_action": "stored"}, window)
    assert good["verdict"] == "GREEN" and good["runs_in_window"] == 1
    # even if a non-terminal row reaches score() directly, it is not counted as a failure
    assert score(rows + [{"day": "2026-08-04", "conclusion": "in_progress"}], set(),
                 {"last_action": "stored"}, window)["verdict"] == "GREEN"


def test_futility_rearm_can_fire_again(tmp_path):
    """W-005c/F08 (constitutional): after option B's approve-override + a re-armed CALENDAR date,
    the new date passing must file a NEW mandatory gate. With a constant slug the decided 2027 gate
    matched forever, so the re-armed clause could never fire — silent continuation."""
    root = tmp_path
    state = root / "ops" / "state"
    (state / "QUEUE" / "pending").mkdir(parents=True)
    (state / "QUEUE" / "decided").mkdir(parents=True)
    cal = state / "CALENDAR.md"
    cal.write_text("- 2027-12-31 — FUTILITY clause: mandatory project-scoring gate\n", encoding="utf-8")

    # the original arming files once, and is idempotent while pending
    slug1 = weekly.maybe_file_futility_gate(str(root), date(2027, 12, 31))
    assert slug1 == "futility-clause-2027-12-31"
    assert weekly.maybe_file_futility_gate(str(root), date(2027, 12, 31)) is None

    # operator decides option B (approve-override) and re-arms the clause to 2029
    g = gates.load_pending(str(state / "QUEUE" / "pending"))[0]
    txt = open(g.path, encoding="utf-8").read().replace("DECISION:", "DECISION: approve-override")
    open(g.path, "w", encoding="utf-8").write(txt)
    weekly.gates.sweep(str(state / "QUEUE" / "pending"), str(state / "QUEUE" / "decided"), date(2027, 12, 31))
    cal.write_text("- 2027-12-31 — FUTILITY clause: original arming (overridden)\n"
                   "- 2029-06-30 — FUTILITY clause re-armed per approve-override\n", encoding="utf-8")

    # the re-armed date is now the armed one, and it FIRES when it passes
    assert weekly._futility_date(str(root)) == date(2029, 6, 30)
    assert weekly.maybe_file_futility_gate(str(root), date(2029, 6, 29)) is None      # not yet
    assert weekly.maybe_file_futility_gate(str(root), date(2029, 6, 30)) == "futility-clause-2029-06-30"


def test_futility_date_parsing_is_hardened(tmp_path):
    """W-005c/F08 second half: the old parser took the first date on the first FUTILITY line, so a
    stray earlier mention silently re-dated the kill review and a malformed date silently disarmed
    it back to the 2027 constant. max() over all valid dates on all futility lines fixes both."""
    state = tmp_path / "ops" / "state"
    state.mkdir(parents=True)
    cal = state / "CALENDAR.md"

    # a stray earlier mention must not pull the review forward
    cal.write_text("- note: see the 2026-01-01 memo about the FUTILITY clause\n"
                   "- 2027-12-31 — FUTILITY clause: mandatory project-scoring gate\n", encoding="utf-8")
    assert weekly._futility_date(str(tmpiter := tmp_path)) == date(2027, 12, 31)

    # a malformed re-arm date is ignored, never silently disarming to the constant
    cal.write_text("- 2029-13-45 — FUTILITY clause re-armed (typo)\n"
                   "- 2030-03-01 — FUTILITY clause re-armed properly\n", encoding="utf-8")
    assert weekly._futility_date(str(tmp_path)) == date(2030, 3, 1)

    # no calendar line at all -> the original pre-registered constant
    cal.write_text("- nothing relevant here\n", encoding="utf-8")
    assert weekly._futility_date(str(tmp_path)) == weekly.FUTILITY_DATE


def test_gate_slug_must_be_filename_safe(tmp_path):
    """Found while wiring F05: new_gate drops the slug straight into a filename, so an unsafe slug
    failed SILENTLY (on Windows 'a:b' writes an NTFS alternate data stream that load_pending can
    never see — the operator's gate simply vanishes). It must raise instead."""
    pend = str(tmp_path / "pending")
    for bad in ("warn-fetch-3x:CA", "greenhouse/stripe", "", "../escape"):
        try:
            gates.new_gate(pend, bad, "T", "source", by="t", what="w", options="A / B",
                           created=date(2026, 7, 28))
            raise AssertionError(f"unsafe slug accepted: {bad!r}")
        except ValueError:
            pass
    g = gates.new_gate(pend, "warn-fetch-3x-CA", "T", "source", by="t", what="w", options="A / B",
                       created=date(2026, 7, 28))
    assert len(gates.load_pending(pend)) == 1 and g.slug == "warn-fetch-3x-CA"


def _run_plain():
    import tempfile, pathlib
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            if "tmp_path" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
                with tempfile.TemporaryDirectory() as d:
                    fn(pathlib.Path(d))
            else:
                fn()
            print("ok:", name)
            passed += 1
    print(f"ALL {passed} OPSCORE TESTS PASS")


if __name__ == "__main__":
    _run_plain()
