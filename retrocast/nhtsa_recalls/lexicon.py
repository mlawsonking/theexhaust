"""FROZEN constants for the NHTSA Shadow Recalls retrocast v1.

This module is the executable half of `indexes/nhtsa-recalls/WORKBOOK.md`. It is committed
BEFORE any result is computed (SPEC-08 §2; PRE-REGISTRATION-v1 §3 requires the hazard lexicon
and the component grouping to be frozen in the workbook). Git history is the receipt: the commit
that adds this file predates the commit that adds `results/v1/`.

Nothing here may be edited in response to a result. A change after results are seen is a v2
pre-registration with disclosure in `retrocast/DEAD-REGISTRATIONS.md`.

Stdlib-only, deterministic, no LLM (constitution: no metered API in the core signal).
"""
from __future__ import annotations

import re

FROZEN_AT = "2026-07-28"
LEXICON_VERSION = "v1"

# --------------------------------------------------------------- component taxonomy crosswalk
# PRE-REGISTRATION §2: "Component grouping uses the NHTSA component taxonomy at its top level
# ... frozen in the workbook." The top level is the text before the first ':' in COMPDESC
# (complaints, field 12) / COMPNAME (recalls, field 7).
#
# The two files do NOT share one vocabulary — the W-006 order's named catch. Measured on the
# archived 2026-07-28 vintages: 40 top-level values appear in both, 1 only in recalls, 13 only in
# complaints, and several pairs are the same physical system under old (recall) vs modern
# (complaint) labels — e.g. complaints file 71,981 rows to "SERVICE BRAKES" and 7,844 to
# "SERVICE BRAKES, HYDRAULIC" while recalls file 6,578 to "SERVICE BRAKES, HYDRAULIC" and 576 to
# "SERVICE BRAKES". Joining raw top levels would silently break the label join for whole systems.
# This crosswalk maps both vocabularies onto one canonical set. It is authored from vocabulary
# semantics and corpus structure only — never from which mapping scores better.
CANONICALIZE = {
    # --- brake vocabulary drift (old recall labels -> modern consumer label)
    "SERVICE BRAKES, HYDRAULIC": "SERVICE BRAKES",
    "SERVICE BRAKES, AIR": "SERVICE BRAKES",
    "SERVICE BRAKES, ELECTRIC": "SERVICE BRAKES",
    "SERVICE BRAKES, HYDRAULIC; AUTOHOLD BRAKE SYSTEM/BRAKE HOLD": "SERVICE BRAKES",
    # --- engine
    "ENGINE AND ENGINE COOLING": "ENGINE",
    # --- fuel / propulsion (modern umbrella; recalls still use the fuel-type split)
    "FUEL SYSTEM, GASOLINE": "FUEL/PROPULSION SYSTEM",
    "FUEL SYSTEM, DIESEL": "FUEL/PROPULSION SYSTEM",
    "FUEL SYSTEM, OTHER": "FUEL/PROPULSION SYSTEM",
    "HYBRID PROPULSION SYSTEM": "FUEL/PROPULSION SYSTEM",
    # --- visibility
    "VISIBILITY/WIPER": "VISIBILITY",
    # --- spelling / label variants
    "COMMUNICATIONS": "COMMUNICATION",
    "ELECTRONIC STABILITY CONTROL": "ELECTRONIC STABILITY CONTROL (ESC)",
    # --- child-seat sub-components (complaint vocabulary) -> the recall-side umbrella
    "CARRY HANDLE, SHELL, BASE": "CHILD SEAT",
    "CHEST CLIP, BUCKLE, HARNESS": "CHILD SEAT",
    "INSERT, PADDING": "CHILD SEAT",
    "TETHER, LOWER ANCHOR (ON CAR SEAT OR VEHICLE)": "CHILD SEAT",
    "I SUSPECT THE CAR SEAT IS COUNTERFEIT": "CHILD SEAT",
    # --- residual buckets (no recall-side counterpart; kept matchable rather than orphaned)
    "OTHER": "UNKNOWN OR OTHER",
    "OTHER/I AM NOT SURE": "UNKNOWN OR OTHER",
    "OTHER/UNKNOWN": "UNKNOWN OR OTHER",
    "NONE": "UNKNOWN OR OTHER",
    "": "UNKNOWN OR OTHER",
    "FIRERELATED": "UNKNOWN OR OTHER",
    "ROLLOVER": "UNKNOWN OR OTHER",
}

# Systems deliberately kept SEPARATE (both vocabularies use them consistently, so no drift to
# repair): PARKING BRAKE, TRACTION CONTROL SYSTEM, WHEELS vs TIRES, EQUIPMENT vs
# EQUIPMENT ADAPTIVE/MOBILITY, LANE DEPARTURE / FORWARD COLLISION AVOIDANCE / BACK OVER
# PREVENTION, POWER TRAIN vs ENGINE, INTERIOR vs EXTERIOR LIGHTING, STRUCTURE, SEATS, SEAT BELTS.

_WS = re.compile(r"\s+")


def component_group(raw: str) -> str:
    """Top level of the NHTSA component string, canonicalized. Deterministic, total."""
    top = _WS.sub(" ", raw.split(":", 1)[0].strip().upper())
    return CANONICALIZE.get(top, top)


def norm_text(raw: str) -> str:
    """Make/model normalization for the cell key: upper, trimmed, internal runs collapsed."""
    return _WS.sub(" ", raw.strip().upper())


def norm_year(raw: str) -> str:
    """Model-year token. Missing/unknown collapses to '9999' on BOTH sides so the join is
    symmetric — an unknown-year complaint can only ever match an unknown-year recall."""
    y = raw.strip()
    return y if (len(y) == 4 and y.isdigit() and y != "9999") else "9999"


def cell_key(make: str, model: str, year: str, component: str) -> tuple:
    """(make, model, model-year, component-group) — the PRE-REGISTRATION §2 unit of analysis."""
    return (norm_text(make), norm_text(model), norm_year(year), component_group(component))


# --------------------------------------------------------------------- hazard lexicon (frozen)
# PRE-REGISTRATION §3 feature 5: "fraction of trailing complaint narratives matching a frozen
# hazard-term lexicon ... Deterministic n-gram match, no LLM in the core signal."
#
# Authored from domain priors about acute vehicle hazards as a consumer would describe them in
# CDESCR (complaints field 20, ALL CAPS free text). Terms are matched with word boundaries, so
# "MISFIRE" and "FIREWALL" do not count as FIRE. Inflections are listed explicitly rather than
# stemmed — a frozen list is auditable, a stemmer is not.
HAZARD_TERMS = (
    # fire / thermal
    "FIRE", "FIRES", "CAUGHT FIRE", "ON FIRE", "FLAMES", "SMOKE", "SMOKING", "BURNING SMELL",
    "BURNED", "BURNT", "MELTED", "MELTING", "SPARKS", "SPARKING", "OVERHEATED", "OVERHEATING",
    # loss of motive power
    "STALL", "STALLS", "STALLED", "STALLING", "LOST POWER", "LOSS OF POWER", "SHUT OFF",
    "SHUT DOWN", "SHUTS OFF", "SHUT OFF WHILE DRIVING", "DIED WHILE DRIVING", "WOULD NOT START",
    # braking
    "BRAKE FAILURE", "BRAKES FAILED", "BRAKE FAILED", "NO BRAKES", "BRAKES WENT OUT",
    "PEDAL WENT TO THE FLOOR", "FAILED TO STOP", "WOULD NOT STOP", "BRAKES LOCKED",
    # steering / control
    "LOSS OF STEERING", "STEERING FAILED", "STEERING LOCKED", "LOST CONTROL", "LOST STEERING",
    "VEERED", "SWERVED", "JERKED",
    # unintended acceleration
    "SUDDEN ACCELERATION", "UNINTENDED ACCELERATION", "ACCELERATED ON ITS OWN", "SURGED",
    "TOOK OFF ON ITS OWN",
    # structural / wheels / tires
    "WHEEL CAME OFF", "CAME OFF", "BLEW OUT", "BLOWOUT", "BLEW", "SEPARATED", "BROKE OFF",
    "SNAPPED", "CRACKED", "FELL OFF",
    # restraints
    "DID NOT DEPLOY", "FAILED TO DEPLOY", "DEPLOYED WITHOUT", "SEAT BELT FAILED",
    "AIRBAG FAILED",
    # crash / harm outcome language
    "CRASH", "CRASHED", "COLLISION", "ACCIDENT", "INJURED", "INJURY", "HOSPITAL", "NEAR MISS",
    "ALMOST HIT",
    # electrical
    "SHORT CIRCUIT", "SHORTED OUT", "ELECTRICAL FIRE",
    # rollaway / closures
    "ROLLED AWAY", "ROLLED BACK", "DOOR OPENED WHILE DRIVING", "HOOD FLEW", "TRUNK OPENED",
)

_HAZARD_RE = re.compile(
    r"\b(?:" + "|".join(sorted((re.escape(t) for t in HAZARD_TERMS), key=len, reverse=True)) + r")\b"
)


def hazard_hit(narrative: str) -> bool:
    """True iff the narrative matches >=1 frozen hazard term (word-boundary n-gram match)."""
    return bool(_HAZARD_RE.search(narrative.upper()))


# ------------------------------------------------------------------ frozen window / split knobs
# PRE-REGISTRATION §3 / §5, restated here as executable constants so the run cannot drift from
# the registration. Dates are converted to integer week indices by the runner
# (week = days_since_epoch // 7), which is the harness's `t`.
TRAILING_WEEKS = 12          # §3.1  W
BASELINE_WEEKS = 52          # §3.2  self-normalizing baseline
HORIZON_WEEKS = 26           # §4    H
WINDOW_START = "2015-01-01"  # §2    first scored week
WINDOW_END = "2025-12-31"    # §2    last scored week
TRAIN_HORIZON_END = "2020-12-31"  # §5  train = cell-weeks whose horizon ends on/before this
TEST_START = "2021-01-01"    # §5    held-out window opens
WARMUP_START = "2013-01-01"  # complaints ingested earlier than WINDOW_START purely to fill the
                             # 52-week baseline of the first scored weeks (no labels, no scoring)

# PRE-REGISTRATION §3 also pre-registers a "transparent threshold rule on rate_ratio + accel +
# severity_frac ... as the fallback/interpretable model". Frozen here as a 0-3 count of conditions
# met, so the whole model fits in one sentence a critic can check by hand: how many of
# (running at >=2x its own recent normal) (still accelerating) (>=20% of trailing complaints
# involve crash, fire, injury or death) are true this week. Chosen from domain priors, before any
# result, and never re-tuned: a re-tune after seeing results would be a v2 pre-registration.
INTERPRETABLE_RULE = {"rate_ratio_min": 2.0, "accel_min": 0.0, "severity_frac_min": 0.20}

# PRE-REGISTRATION §7 — the publish bars, frozen. Consumed by the harness verbatim.
BARS = {
    "target_recall": 0.50,     # train event-recall used to CHOOSE the operating point
    "precision": 0.30,         # test precision at that point
    "recall": 0.50,            # test event-recall
    "median_lead_days": 60.0,  # median lead of first crossing -> recall report-received date
    "auc_margin": 0.05,        # PR-AUC must beat volume-only by this absolute margin
}
