"""Tests for the Hospital/Care v1 retrocast machinery (offline, no R2, no network).

Covers the things that would silently corrupt a published number: the as-known-then publication
lag, the drop-and-count admissibility rules, distinct-event labelling, the pre-committed lead-time
degeneracy rule, and — SPEC-08 §7 criterion 2 — that a deliberately planted leak is CAUGHT. Run:
    python -m retrocast.tests.test_hospital_care_v1
"""
from __future__ import annotations

import io
from datetime import date, timedelta

from retrocast import harness
from retrocast.hospital_care import features as F
from retrocast.hospital_care import spec as S


# --------------------------------------------------------------------------- fixtures
HEAD = ("PROVNUM,PROVNAME,CITY,STATE,COUNTY_NAME,COUNTY_FIPS,CY_Qtr,WorkDate,MDScensus,"
        "Hrs_RNDON,Hrs_RNDON_emp,Hrs_RNDON_ctr,Hrs_RNadmin,Hrs_RNadmin_emp,Hrs_RNadmin_ctr,"
        "Hrs_RN,Hrs_RN_emp,Hrs_RN_ctr,Hrs_LPNadmin,Hrs_LPNadmin_emp,Hrs_LPNadmin_ctr,"
        "Hrs_LPN,Hrs_LPN_emp,Hrs_LPN_ctr,Hrs_CNA,Hrs_CNA_emp,Hrs_CNA_ctr,"
        "Hrs_NAtrn,Hrs_NAtrn_emp,Hrs_NAtrn_ctr,Hrs_MedAide,Hrs_MedAide_emp,Hrs_MedAide_ctr")


def pbj_row(prov, day, census, rn=10.0, cna=20.0, ctr=0.0, state="TX"):
    """One daily row: RN hours `rn` (of which `ctr` contract), CNA hours `cna`, rest zero."""
    v = {"Hrs_RN": rn, "Hrs_RN_ctr": ctr, "Hrs_CNA": cna}
    # The provider name deliberately contains a comma — real PROVNAMEs do ("BURNS NURSING HOME,
    # INC.") — so the fixture exercises quoted-field parsing rather than a naive split.
    cols = ['"HOME, INC."', "CITY", state, "County", "001", "2024Q1",
            day.strftime("%Y%m%d"), str(census)]
    for c in HEAD.split(",")[9:]:
        cols.append(str(v.get(c, 0)))
    return ",".join([prov, *cols])


def pbj_csv(rows):
    return (HEAD + "\n" + "\n".join(rows) + "\n").encode()


def quarter_days(y, m1, n=90):
    d0 = date(y, m1, 1)
    return [d0 + timedelta(days=i) for i in range(n)]


# --------------------------------------------------------------------------- publication lag
def test_publication_lag_never_lets_a_quarter_be_used_before_it_exists():
    """The as-known-then control (WORKBOOK §7). A quarter must not be usable on its own end date."""
    for q in ("2023Q2", "2024Q4", "2025Q1"):
        assert F.quarter_available_from(q) > F.quarter_end(q)
        assert (F.quarter_available_from(q) - F.quarter_end(q)).days == 135


def test_the_operative_quarter_for_a_week_is_always_already_published():
    """Walk every scored week and assert the chosen quarter ended >= 135 days earlier."""
    qs = F.quarters_between(S.PBJ_FIRST_QUARTER, S.PBJ_LAST_QUARTER)
    w = S.week(S.TRAIN_FIRST_WEEK_START)
    last = S.week(S.TEST_LAST_WEEK_START)
    seen = 0
    while w <= last:
        ws = S.week_start(w)
        cands = [q for q in qs if F.quarter_available_from(q) <= ws]
        if cands:
            q = max(cands, key=lambda x: (int(x[:4]), int(x[-1])))
            assert (ws - F.quarter_end(q)).days >= S.PBJ_AVAILABILITY_LAG_DAYS, (ws, q)
            seen += 1
        w += 1
    assert seen > 60


# --------------------------------------------------------------------------- feature rules
def test_hprd_is_summed_numerator_over_summed_denominator():
    """One odd day must not dominate, and a zero-census day must not divide by zero."""
    days = quarter_days(2024, 1)
    rows = [pbj_row("111111", d, 100 if i else 0, rn=10, cna=20) for i, d in enumerate(days)]
    aggs, short = F.load_pbj_quarter(pbj_csv(rows))
    a = aggs["111111"]
    assert short == 0 and a.zero_days == 1 and a.days == 89
    f = F.quarter_features(a, trend_base=0.30)
    assert abs(f["hprd_total"] - 0.30) < 1e-12          # (10+20)/100
    assert abs(f["hprd_rn"] - 0.10) < 1e-12
    assert abs(f["hprd_trend"] - 0.0) < 1e-12           # equal to its own baseline


def test_quarter_below_the_day_floor_is_dropped_not_imputed():
    days = quarter_days(2024, 1, n=S.MIN_QUARTER_DAYS - 1)
    aggs, _ = F.load_pbj_quarter(pbj_csv([pbj_row("222222", d, 100) for d in days]))
    assert F.quarter_features(aggs["222222"], trend_base=0.30) is None


def test_zero_weekday_hours_makes_weekend_gap_undefined_and_drops_the_quarter():
    """A facility reporting a census but no weekday nursing hours has no weekday level to compare
    a weekend against. Real condition in the archive; must drop, never divide by zero."""
    rows = []
    for d in quarter_days(2024, 1):
        weekend = d.weekday() >= 5
        rows.append(pbj_row("333333", d, 100, rn=10 if weekend else 0, cna=20 if weekend else 0))
    aggs, _ = F.load_pbj_quarter(pbj_csv(rows))
    assert F.quarter_features(aggs["333333"], trend_base=0.30) is None


def test_low_days_frac_counts_against_the_external_cms_threshold():
    days = quarter_days(2024, 1)
    rows = []
    for i, d in enumerate(days):
        # odd days: (10+30)/10 = 4.00 HPRD, ABOVE the rule. even days: (10+5)/10 = 1.50, below.
        rows.append(pbj_row("444444", d, 10, rn=10, cna=(30 if i % 2 else 5)))
    aggs, _ = F.load_pbj_quarter(pbj_csv(rows))
    f = F.quarter_features(aggs["444444"], trend_base=2.75)
    assert abs(f["low_days_frac"] - 0.5) < 0.02
    assert S.CMS_MIN_HPRD == 3.48
    # and the threshold really is the discriminator: lift every day above it and the count goes to 0
    rows_hi = [pbj_row("444444", d, 10, rn=10, cna=30) for d in days]
    aggs_hi, _ = F.load_pbj_quarter(pbj_csv(rows_hi))
    assert F.quarter_features(aggs_hi["444444"], trend_base=4.0)["low_days_frac"] == 0.0


def test_contract_fraction_is_contract_over_all_nursing_hours():
    days = quarter_days(2024, 1)
    aggs, _ = F.load_pbj_quarter(
        pbj_csv([pbj_row("555555", d, 100, rn=10, cna=20, ctr=4) for d in days]))
    f = F.quarter_features(aggs["555555"], trend_base=0.30)
    assert abs(f["contract_frac"] - 4 / 30) < 1e-12


def test_short_rows_are_counted_not_swallowed():
    days = quarter_days(2024, 1, n=61)
    body = pbj_csv([pbj_row("666666", d, 100) for d in days]).decode() + "\n\n"
    aggs, short = F.load_pbj_quarter(body.encode())
    assert short == 2 and "666666" in aggs


def test_a_reshaped_release_aborts_rather_than_mis_indexing():
    bad = HEAD.replace("MDScensus", "mds_census").encode() + b"\n"
    try:
        F.load_pbj_quarter(bad)
    except SystemExit as e:
        assert "missing columns" in str(e)
    else:
        raise AssertionError("a missing required column must abort, not be guessed at")


# --------------------------------------------------------------------------- labels
def test_survey_events_are_distinct_ccn_date_pairs_not_rows():
    """WORKBOOK §4 — grading rows would count one inspection once per tag cited."""
    hdr = ("CMS Certification Number (CCN),Provider Name,State,Survey Date,Survey Type,"
           "Deficiency Tag Number,Deficiency Category,Scope Severity Code")
    rows = [hdr,
            "111111,A,TX,2024-03-01,Health,F600,Quality,D",
            "111111,A,TX,2024-03-01,Health,F689,Quality,G",     # same survey, harm tag
            "111111,A,TX,2024-03-01,Health,F690,Quality,D",
            "222222,B,TX,2024-05-02,Health,F600,Quality,D",
            "222222,B,TX,2023-01-04,Health,F600,Quality,J"]
    gt = F.load_deficiencies(("\n".join(rows) + "\n").encode())
    assert gt["rows"] == 5
    assert len(gt["all_events"]) == 3                          # 5 rows -> 3 survey events
    assert gt["harm_events"] == [("111111", date(2024, 3, 1)), ("222222", date(2023, 1, 4))]
    assert gt["ij_events"] == [("222222", date(2023, 1, 4))]   # J is IJ and also harm
    assert gt["first_observed"]["222222"] == date(2023, 1, 4)  # the earliest, not the first seen


def test_prior_rate_is_per_observed_year_and_never_peeks():
    events = [("A", date(2023, 1, 1)), ("A", date(2024, 1, 1)), ("A", date(2025, 6, 1))]
    f = F.prior_rate_fn(events)
    # at 2025-01-01 only the first two have happened; 2 years observed
    assert abs(f("A", date(2025, 1, 1), 2.0) - 1.0) < 1e-12
    assert f("A", date(2022, 1, 1), 1.0) == 0.0                # nothing before the first event
    assert f("B", date(2025, 1, 1), 2.0) == 0.0                # unknown facility


# --------------------------------------------------------------------------- the leak plant
def _grid(n_ent=60, n_wk=60):
    return [(e, w) for e in range(n_ent) for w in range(n_wk)]


def test_planted_label_oracle_is_caught_by_the_leakage_scan():
    """SPEC-08 §7 criterion 2. This plant was NOT caught before 2026-07-30: a binary oracle's
    PR-AUC is low (two-point curve) and a horizon label makes an oracle *lead* the event, so
    neither the PR-AUC rule nor the nonpositive-lead rule fired. Precision does catch it."""
    cells = _grid()
    labels = sorted({(e, 30) for e in range(0, 60, 4)})        # every 4th facility, week 30
    truth = harness.label_cells([(e, w, 0.0) for e, w in cells], labels, 26)
    oracle = [(r["entity"], r["t"], 0.9 if r["y"] else 0.05) for r in truth]
    res = harness.evaluate(signal_obs=oracle, baseline_obs=oracle, labels=labels, horizon=26,
                           train_end=20, test_start=0,
                           bars=dict(S.BARS), train_label_window=(0, 46),
                           test_label_window=(0, 86))
    assert res["metrics"]["precision"] >= 0.99
    assert res["leakage_flags"], "a label oracle must not pass the leakage scan silently"
    assert any("implausibly perfect" in f for f in res["leakage_flags"])


def test_planted_coincident_signal_is_caught_by_the_nonpositive_lead_rule():
    """The other shape of plant — a feature that lights up AT the event rather than before it."""
    flags = harness.leakage_scan(median_lead=0, n_nonpositive_leads=12, pr_auc_value=0.4,
                                 base_rate=0.1, precision=0.4)
    assert len(flags) == 2 and any("lead<=0" in f for f in flags)


def test_an_honest_signal_raises_no_leakage_flag():
    """The guard must not cry wolf on a normal, imperfect signal."""
    assert harness.leakage_scan(median_lead=154, n_nonpositive_leads=0, pr_auc_value=0.177,
                                base_rate=0.136, precision=0.179) == []


# --------------------------------------------------------------------------- the degeneracy rule
def _lead_degenerate(leads):
    at_edge = sum(1 for v in leads if v >= S.LEAD_EDGE_DAYS)
    return bool(leads) and (at_edge / len(leads)) >= S.LEAD_DEGENERACY_SHARE


def test_degeneracy_rule_fires_when_leads_pile_on_the_horizon_edge():
    """Pre-committed in registration §7 so a collapsed threshold cannot buy a lead-time pass."""
    assert _lead_degenerate([175] * 6 + [10] * 4)              # 60% at the edge
    assert _lead_degenerate([182, 175, 176, 7])                # 75%
    assert not _lead_degenerate([175] * 4 + [10] * 6)          # 40%
    assert not _lead_degenerate([])                            # no leads is not degeneracy


def test_the_published_v1_lead_distribution_is_not_degenerate_on_this_rule():
    """The rule is only credible because it did not fire on the run it was written for: 925 of
    2,138 held-out leads sit at the 175-day edge, which is 43.3% — under the 50% bar."""
    assert not _lead_degenerate([175] * 925 + [1] * (2138 - 925))
    assert abs(925 / 2138 - 0.4326) < 0.001


def _run_plain():
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok:", name)
            passed += 1
    print(f"ALL {passed} HOSPITAL-CARE V1 TESTS PASS")


if __name__ == "__main__":
    _run_plain()
