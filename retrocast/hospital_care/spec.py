"""FROZEN constants for the Hospital/Care Distress retrocast v1.

Every value here is committed and pushed BEFORE the runner exists and before any staffing value is
compared to any citation. `indexes/hospital-care/WORKBOOK.md` states the same numbers in prose and
`retrocast/tests/test_hospital_care_freeze.py` fails the suite if the two ever disagree — so a
quiet edit to either side is a build failure, not a silent re-registration.

Changing a number here after results are seen is a v2 pre-registration, not an edit
(SPEC-08 §2; constitution: the retrocast gate).
"""
from __future__ import annotations

from datetime import date

INDEX = "hospital-care"
VERSION = "v1"
REGISTRATION = "retrocast/hospital-care/PRE-REGISTRATION-v1.md"
WORKBOOK = "indexes/hospital-care/WORKBOOK.md"

# --------------------------------------------------------------------------- time base (§8)
WEEK_EPOCH = date(2017, 1, 2)          # a Monday
HORIZON_WEEKS = 26


def week(d: date) -> int:
    """Week index; week w spans [WEEK_EPOCH + 7w, WEEK_EPOCH + 7w + 6]."""
    return (d - WEEK_EPOCH).days // 7


def week_start(w: int) -> date:
    from datetime import timedelta
    return WEEK_EPOCH + timedelta(days=7 * w)


# --------------------------------------------------------------------------- labels (§4, §5)
HARM_SEVERITY = frozenset("GHIJKL")        # actual harm (G,H,I) + immediate jeopardy (J,K,L)
IMMEDIATE_JEOPARDY = frozenset("JKL")      # reported separately, never a second bar

LABEL_WINDOW_START = date(2024, 1, 1)      # global; where facility coverage reaches 92.4%
LABEL_WINDOW_END = date(2026, 3, 31)       # drops the 2% -reported month and the one before it
MIN_OBSERVED_DAYS = 182                    # per-facility left truncation

# --------------------------------------------------------------------------- signal (§6)
NURSE_HOURS = ("Hrs_RNDON", "Hrs_RNadmin", "Hrs_RN",
               "Hrs_LPNadmin", "Hrs_LPN",
               "Hrs_CNA", "Hrs_NAtrn", "Hrs_MedAide")
RN_HOURS = ("Hrs_RNDON", "Hrs_RNadmin", "Hrs_RN")
CONTRACT_SUFFIX = "_ctr"

# The CMS 2024 minimum-staffing final rule's total nurse HPRD (0.55 RN + 2.45 NA + 0.48 flexible).
# Externally fixed on purpose: no threshold in this index was chosen by us against this data.
CMS_MIN_HPRD = 3.48

MIN_QUARTER_DAYS = 60                      # a (CCN, quarter) below this is inadmissible
TREND_LOOKBACK_QUARTERS = 4

FEATURES = ("hprd_total", "hprd_rn", "rn_share", "contract_frac",
            "weekend_gap", "hprd_cv", "hprd_trend", "low_days_frac", "census")

# --------------------------------------------------------------------------- as-known-then (§7)
# Observed: 2026Q1 (ends 03-31) Last-Modified 2026-06-30 = 91 d; 2025Q4 (ends 12-31) 2026-04-16
# = 106 d. The margin is deliberate. Without this rule the run would assume knowledge ~3 months
# before it was public and every lead-time number would be fiction.
PBJ_AVAILABILITY_LAG_DAYS = 135

# --------------------------------------------------------------------------- splits (§9)
TRAIN_FIRST_WEEK_START = date(2023, 12, 25)
TRAIN_LAST_WEEK_START = date(2024, 9, 23)
TEST_FIRST_WEEK_START = date(2025, 3, 24)
TEST_LAST_WEEK_START = date(2025, 9, 22)
# Last train horizon ends 2025-03-30; first test horizon begins 2025-03-31. Exact, not approximate.

PBJ_FIRST_QUARTER = "2022Q2"
PBJ_LAST_QUARTER = "2025Q1"

# --------------------------------------------------------------------------- bars (§7 of the reg)
BARS = {
    "target_recall": 0.50,       # train event-recall used to set the operating point
    "auc_margin": 0.05,          # over the BETTER of the two dumb baselines
    "precision": 0.35,           # ~2x the pre-measured label-side prior, deliberately
    "recall": 0.50,              # held-out event-recall
    "median_lead_days": 60,
}

# If >= this share of true-positive leads sit within one week of the horizon edge, the lead-time
# result is DEGENERATE and lead_ok is False regardless of the median. Pre-committed because
# NHTSA v1's median lead "passed" only because its threshold had collapsed.
LEAD_DEGENERACY_SHARE = 0.50
LEAD_EDGE_DAYS = HORIZON_WEEKS * 7 - 7     # within one week of the 182-day edge => >= 175 days
