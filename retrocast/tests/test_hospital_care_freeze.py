"""Tests for the FROZEN Hospital/Care constants (WORKBOOK + PRE-REGISTRATION v1).

Threshold archaeology (SPEC-08 §5) made mechanical: `spec.py`, the workbook prose and the
registration prose must agree, and the horizon-spillover guard must be exact arithmetic rather
than a claim. A quiet edit to any one of the three is a build failure. Run:
    python -m retrocast.tests.test_hospital_care_freeze
"""
from __future__ import annotations

import os
import re
from datetime import date, timedelta

from retrocast.hospital_care import spec as S

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKBOOK = open(os.path.join(ROOT, "indexes", "hospital-care", "WORKBOOK.md"),
                encoding="utf-8").read()
REG = open(os.path.join(ROOT, "retrocast", "hospital-care", "PRE-REGISTRATION-v1.md"),
           encoding="utf-8").read()


def test_bars_match_the_pre_registration_verbatim():
    assert S.BARS == {"target_recall": 0.50, "auc_margin": 0.05,
                      "precision": 0.35, "recall": 0.50, "median_lead_days": 60}
    assert "precision ≥ 0.35" in REG
    assert "event-recall ≥ 0.50" in REG
    assert "median lead-time ≥ 60 days" in REG
    assert "+ 0.05 absolute" in REG


def test_degeneracy_rule_is_frozen_and_documented():
    """The rule that stops a collapsed threshold from buying a lead-time 'pass' (W-006's lesson)."""
    assert S.LEAD_DEGENERACY_SHARE == 0.50
    assert S.LEAD_EDGE_DAYS == 175                       # within one week of the 182-day edge
    assert "degenerate" in REG.lower()
    assert "≥50% of true-positive" in REG


def test_horizon_spillover_guard_is_exact():
    """Train and test horizons must not overlap by a single day — arithmetic, not assertion."""
    # horizon of cell w covers weeks w+1..w+26 => days [w_start+7, w_start+7*26+6]
    last_train_horizon_end = S.TRAIN_LAST_WEEK_START + timedelta(days=7 * S.HORIZON_WEEKS + 6)
    first_test_horizon_start = S.TEST_FIRST_WEEK_START + timedelta(days=7)
    assert last_train_horizon_end == date(2025, 3, 30), last_train_horizon_end
    assert first_test_horizon_start == date(2025, 3, 31), first_test_horizon_start
    assert last_train_horizon_end < first_test_horizon_start
    assert "2025-03-30" in WORKBOOK and "2025-03-31" in WORKBOOK


def test_every_scored_horizon_lies_inside_the_label_window():
    """Cells whose horizon runs past the usable label window would collect manufactured negatives."""
    for w_start in (S.TRAIN_FIRST_WEEK_START, S.TEST_LAST_WEEK_START):
        assert w_start + timedelta(days=7) >= S.LABEL_WINDOW_START, w_start
        assert w_start + timedelta(days=7 * S.HORIZON_WEEKS + 6) <= S.LABEL_WINDOW_END, w_start


def test_splits_are_mondays_and_ordered():
    for d in (S.WEEK_EPOCH, S.TRAIN_FIRST_WEEK_START, S.TRAIN_LAST_WEEK_START,
              S.TEST_FIRST_WEEK_START, S.TEST_LAST_WEEK_START):
        assert d.weekday() == 0, d
    assert (S.TRAIN_FIRST_WEEK_START < S.TRAIN_LAST_WEEK_START
            < S.TEST_FIRST_WEEK_START < S.TEST_LAST_WEEK_START)
    assert S.week(S.WEEK_EPOCH) == 0
    assert S.week_start(S.week(S.TEST_FIRST_WEEK_START)) == S.TEST_FIRST_WEEK_START


def test_label_window_matches_the_workbook_prose():
    assert S.LABEL_WINDOW_START == date(2024, 1, 1)
    assert S.LABEL_WINDOW_END == date(2026, 3, 31)
    assert "`2024-01-01 .. 2026-03-31`" in WORKBOOK
    assert "2024-01-01 … 2026-03-31" in REG


def test_harm_definition_is_frozen():
    assert S.HARM_SEVERITY == frozenset("GHIJKL")
    assert S.IMMEDIATE_JEOPARDY == frozenset("JKL")
    assert S.IMMEDIATE_JEOPARDY < S.HARM_SEVERITY
    assert '{"G", "H", "I", "J", "K", "L"}' in WORKBOOK


def test_cms_threshold_is_the_external_regulatory_one_not_ours():
    """3.48 is the CMS 2024 final rule's total nurse HPRD. If this ever becomes a tuned number the
    index loses its only untunable threshold."""
    assert S.CMS_MIN_HPRD == 3.48
    assert "3.48" in WORKBOOK and "3.48" in REG
    assert "0.55" in WORKBOOK and "2.45" in WORKBOOK and "0.48" in WORKBOOK


def test_publication_lag_exceeds_every_observed_lag():
    """The as-known-then control. Observed 91 d (2026Q1) and 106 d (2025Q4)."""
    assert S.PBJ_AVAILABILITY_LAG_DAYS == 135
    assert S.PBJ_AVAILABILITY_LAG_DAYS > 106
    assert "135" in WORKBOOK and "135 days" in REG


def test_feature_list_matches_the_workbook_table():
    assert S.FEATURES == ("hprd_total", "hprd_rn", "rn_share", "contract_frac",
                          "weekend_gap", "hprd_cv", "hprd_trend", "low_days_frac", "census")
    for f in S.FEATURES:
        assert f"`{f}`" in WORKBOOK, f
    assert len(S.FEATURES) == len(set(S.FEATURES)) == 9


def test_hour_columns_are_disjoint_and_rn_is_a_subset():
    assert set(S.RN_HOURS) < set(S.NURSE_HOURS)
    assert len(S.NURSE_HOURS) == len(set(S.NURSE_HOURS)) == 8
    for c in S.NURSE_HOURS:
        assert c in WORKBOOK, c


def test_required_pbj_quarters_cover_the_trend_lookback():
    """Feature quarters must reach TREND_LOOKBACK_QUARTERS behind the earliest usable quarter."""
    def qend(q):
        y, n = int(q[:4]), int(q[-1])
        return date(y, 3 * n, 1) + timedelta(days=31) - timedelta(days=(date(y, 3 * n, 1)
                                                                        + timedelta(days=31)).day)
    # earliest quarter usable for the first train cell under the 135-day availability rule
    cutoff = S.TRAIN_FIRST_WEEK_START - timedelta(days=S.PBJ_AVAILABILITY_LAG_DAYS)
    assert qend("2023Q2") <= cutoff < qend("2023Q3"), cutoff
    # ... minus four quarters of trend baseline lands on the frozen first quarter
    assert S.PBJ_FIRST_QUARTER == "2022Q2"
    assert S.TREND_LOOKBACK_QUARTERS == 4
    # latest quarter usable for the last test cell
    cutoff_hi = S.TEST_LAST_WEEK_START - timedelta(days=S.PBJ_AVAILABILITY_LAG_DAYS)
    assert qend("2025Q1") <= cutoff_hi < qend("2025Q2"), cutoff_hi
    assert S.PBJ_LAST_QUARTER == "2025Q1"


def test_registration_keeps_the_naming_gate_shut():
    """Covenant 2 + the work order: a passing retrocast does not name a facility."""
    assert "no named facility publishes" in REG.lower()
    assert "county-level" in REG
    assert "#219" in REG


def test_registration_declares_the_join_is_not_novel():
    """Constitution's prior-art rule: replicate-then-run, stated out loud."""
    assert "not novel" in REG.lower()
    assert os.path.exists(os.path.join(ROOT, "retrocast", "hospital-care", "prior-art-scan.md"))


def _run_plain():
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok:", name)
            passed += 1
    print(f"ALL {passed} HOSPITAL-CARE FREEZE TESTS PASS "
          f"({len(S.FEATURES)} features, horizon {S.HORIZON_WEEKS}w, "
          f"lag {S.PBJ_AVAILABILITY_LAG_DAYS}d)")


if __name__ == "__main__":
    _run_plain()
