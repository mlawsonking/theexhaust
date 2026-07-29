"""Tests for the FROZEN NHTSA retrocast constants (workbook freeze, PRE-REGISTRATION §2/§3).

These are the guard rails on a document that must not drift: the crosswalk must be idempotent and
must actually repair the two vocabularies, the hazard match must be word-boundary (not substring),
and the bars must equal the pre-registered numbers verbatim. Run:
    python -m retrocast.tests.test_nhtsa_lexicon
"""
from __future__ import annotations

from retrocast.nhtsa_recalls import lexicon as L


def test_component_group_takes_top_level():
    assert L.component_group("POWER TRAIN:AUTOMATIC TRANSMISSION") == "POWER TRAIN"
    assert L.component_group("  power train : automatic  ") == "POWER TRAIN"
    assert L.component_group("STRUCTURE") == "STRUCTURE"


def test_crosswalk_repairs_the_two_vocabularies():
    """The recall-side and complaint-side labels for one physical system must canonicalize
    to the SAME group — otherwise the label join silently breaks for whole systems."""
    pairs = [
        ("SERVICE BRAKES, HYDRAULIC:FOUNDATION COMPONENTS", "SERVICE BRAKES:HYDRAULIC"),
        ("ENGINE AND ENGINE COOLING:ENGINE", "ENGINE"),
        ("FUEL SYSTEM, GASOLINE:DELIVERY", "FUEL/PROPULSION SYSTEM"),
        ("VISIBILITY/WIPER", "VISIBILITY"),
        ("COMMUNICATIONS", "COMMUNICATION"),
        ("ELECTRONIC STABILITY CONTROL", "ELECTRONIC STABILITY CONTROL (ESC)"),
        ("CHEST CLIP, BUCKLE, HARNESS", "CHILD SEAT"),
        ("OTHER", "UNKNOWN OR OTHER"),
        ("", "UNKNOWN OR OTHER"),
    ]
    for a, b in pairs:
        assert L.component_group(a) == L.component_group(b), (a, b)


def test_crosswalk_is_idempotent():
    for raw in L.CANONICALIZE:
        once = L.component_group(raw)
        assert L.component_group(once) == once, raw


def test_systems_deliberately_kept_separate_stay_separate():
    """Guard against an over-eager future merge: these are distinct systems in BOTH vocabularies."""
    distinct = ["SERVICE BRAKES", "PARKING BRAKE", "TIRES", "WHEELS", "ENGINE", "POWER TRAIN",
                "EQUIPMENT", "EQUIPMENT ADAPTIVE/MOBILITY", "LANE DEPARTURE",
                "FORWARD COLLISION AVOIDANCE", "TRACTION CONTROL SYSTEM"]
    groups = [L.component_group(x) for x in distinct]
    assert len(set(groups)) == len(distinct), groups


def test_hazard_match_is_word_boundary_not_substring():
    assert L.hazard_hit("VEHICLE CAUGHT FIRE WHILE PARKED")
    assert not L.hazard_hit("ENGINE MISFIRE AT IDLE")          # MISFIRE is not FIRE
    assert not L.hazard_hit("HEAT FROM THE FIREWALL")          # FIREWALL is not FIRE
    assert L.hazard_hit("the car stalled on the highway")      # case-insensitive
    assert not L.hazard_hit("PAINT IS PEELING ON THE HOOD")    # benign narrative


def test_hazard_terms_are_unique_and_uppercase():
    assert len(set(L.HAZARD_TERMS)) == len(L.HAZARD_TERMS)
    assert all(t == t.upper() and t.strip() == t for t in L.HAZARD_TERMS)


def test_cell_key_normalization_is_symmetric():
    a = L.cell_key(" ford ", "F-150  Lightning", "2022", "ENGINE AND ENGINE COOLING:ENGINE")
    b = L.cell_key("FORD", "F-150 LIGHTNING", "2022", "ENGINE")
    assert a == b == ("FORD", "F-150 LIGHTNING", "2022", "ENGINE")
    # unknown year collapses identically on both sides, so it can only match itself
    assert L.norm_year("") == L.norm_year("9999") == L.norm_year("20") == "9999"


def test_bars_match_the_pre_registration_verbatim():
    """PRE-REGISTRATION §7 — threshold archaeology guard (SPEC-08 §5)."""
    assert L.BARS == {"target_recall": 0.50, "precision": 0.30, "recall": 0.50,
                      "median_lead_days": 60.0, "auc_margin": 0.05}
    assert (L.TRAILING_WEEKS, L.BASELINE_WEEKS, L.HORIZON_WEEKS) == (12, 52, 26)
    assert (L.WINDOW_START, L.WINDOW_END) == ("2015-01-01", "2025-12-31")
    assert (L.TRAIN_HORIZON_END, L.TEST_START) == ("2020-12-31", "2021-01-01")


def _run_plain():
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok:", name)
            passed += 1
    print(f"ALL {passed} NHTSA LEXICON TESTS PASS "
          f"({len(L.HAZARD_TERMS)} hazard terms, {len(L.CANONICALIZE)} crosswalk entries, "
          f"frozen {L.FROZEN_AT})")


if __name__ == "__main__":
    _run_plain()
