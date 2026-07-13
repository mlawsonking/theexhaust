"""ops-core tests (offline, deterministic). Run:
    python -m opscore.tests.test_opscore        # plain asserts, no pytest
    python -m pytest opscore/tests/test_opscore.py
"""
from __future__ import annotations

import os
from datetime import date

from opscore import gates, orphan, report
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
