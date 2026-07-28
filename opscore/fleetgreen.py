"""Fleet-green scoring (SPEC-01 §6 criterion 1) — the pure half of `ops/fleet_green.py`.

Kept here so the rule that decides whether BUILD-01's "green 7 consecutive days" criterion is met
is unit-tested rather than living only inside a CLI. Evidence gathering (gh / R2 / state files)
stays in the CLI; this module only judges the gathered records.
"""
from __future__ import annotations

# Enabled collectors: name -> (workflow file, R2 raw/ prefix). SPEC-01 §2 roster minus what is not
# yet built; C7 kroger is deliberately ABSENT — it stays dark until its ToS gate clears.
FLEET = {
    "cms-deficiencies":  ("collect-cms-deficiencies.yml",  "raw/cms-deficiencies/"),
    "cpsc-recalls":      ("collect-cpsc-recalls.yml",      "raw/cpsc-recalls/"),
    "nhtsa-recalls":     ("collect-nhtsa-recalls.yml",     "raw/nhtsa-recalls/"),
    "nhtsa-complaints":  ("collect-nhtsa-complaints.yml",  "raw/nhtsa-complaints/"),
    "fdic-failures":     ("collect-fdic-failures.yml",     "raw/fdic-failures/"),
    "ats-boards":        ("collect-ats-boards.yml",        "raw/ats-boards/"),
    "warn":              ("collect-warn.yml",              "raw/warn/"),
}


def day_of_manifest_key(key: str) -> str | None:
    """`raw/<...>/YYYY/MM/DD/manifest.json` -> `'YYYY-MM-DD'` (None if it isn't one)."""
    p = key.split("/")
    if len(p) < 5 or not p[-1].endswith("manifest.json"):
        return None
    y, m, d = p[-4], p[-3], p[-2]
    return f"{y}-{m}-{d}" if (len(y), len(m), len(d)) == (4, 2, 2) and (y + m + d).isdigit() else None


def score(runs, manifest_days, state, window):
    """Judge one collector over a window.

    runs:          [{"day": "YYYY-MM-DD", "conclusion": str}] from Actions history
    manifest_days: set of "YYYY-MM-DD" that have a manifest in R2 (corroborating evidence only —
                   a dedupe firing is perfectly green and writes no manifest)
    state:         that collector's committed `ops/state/health/<c>.json` record
    window:        [date, ...] oldest -> newest

    Green = every firing in the window succeeded, at least one did, and the committed state shows
    neither a quarantine nor a pause. Cadences run daily..weekly, so "7 green days" can never mean
    "a run every day" — it means an unbroken window.
    """
    wdays = {d.isoformat() for d in window}
    inwin = [r for r in runs if r["day"] in wdays]
    failed = sorted({r["day"] for r in inwin if r["conclusion"] not in ("success", "skipped")})
    ok_days = sorted({r["day"] for r in inwin if r["conclusion"] == "success"})
    quarantined = str(state.get("last_action", "")).startswith("quarantined")
    paused = bool(state.get("paused"))
    green = bool(ok_days) and not failed and not quarantined and not paused
    return {
        "green": green,
        "runs_in_window": len(inwin),
        "ok_days": ok_days,
        "failed_days": failed,
        "manifest_days": sorted(d for d in manifest_days if d in wdays),
        "quarantined": quarantined,
        "paused": paused,
        "verdict": ("GREEN" if green else
                    ("PAUSED" if paused else "QUARANTINED" if quarantined else
                     "FAILED-RUN" if failed else "NO-FIRING-IN-WINDOW")),
    }
