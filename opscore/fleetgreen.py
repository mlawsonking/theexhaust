"""Fleet-green scoring (SPEC-01 §6 criterion 1) — the pure half of `ops/fleet_green.py`.

Kept here so the rule that decides whether BUILD-01's "green 7 consecutive days" criterion is met
is unit-tested rather than living only inside a CLI. Evidence gathering (gh / R2 / state files)
stays in the CLI; this module only judges the gathered records.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

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
    # W-007b: the staffing half of C1. Quarterly source, probed 2x/week — `score` judges an
    # unbroken window rather than a run per day, so a dedupe firing counts as green. Listing it
    # here is what makes it visible to the ⚑ #215 acceptance check; a collector outside FLEET is a
    # collector nobody is watching.
    "cms-pbj":           ("collect-cms-pbj.yml",           "raw/cms-pbj/"),
}


def day_of_manifest_key(key: str) -> str | None:
    """`raw/<...>/YYYY/MM/DD/manifest.json` -> `'YYYY-MM-DD'` (None if it isn't one)."""
    p = key.split("/")
    if len(p) < 5 or not p[-1].endswith("manifest.json"):
        return None
    y, m, d = p[-4], p[-3], p[-2]
    return f"{y}-{m}-{d}" if (len(y), len(m), len(d)) == (4, 2, 2) and (y + m + d).isdigit() else None


UNREADABLE = "_unreadable"


def committed_state(root: str, name: str) -> dict:
    """That collector's committed `ops/state/health/<c>.json` record.

    A file that exists but cannot be read is NOT an empty record (W-005c/F09): swallowing the error
    and returning {} made score() see no quarantine and no pause, so a truncated or conflict-marked
    state file produced a vacuous GREEN and closed the constitutional acceptance criterion in the
    lenient direction. Unreadable is its own state, and it is never green."""
    p = os.path.join(root, "ops", "state", "health", f"{name}.json")
    if not os.path.exists(p):
        return {}                                   # not yet committed — absence is not corruption
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        rec = (data.get("collectors") or {}).get(name)
        if rec is None:
            return {UNREADABLE: f"no 'collectors.{name}' record in {p}"}
        return rec
    except Exception as e:
        return {UNREADABLE: f"{type(e).__name__}: {e}"}


def run_rows(raw_runs) -> list[dict]:
    """Map `gh run list --json conclusion,createdAt,...` output to scoring rows.

    Runs that have not finished are DROPPED, not recorded as failures (W-005c/F10): an in-flight
    run has a null conclusion, and counting it as a failed day made a perfectly green collector read
    FAILED-RUN whenever the report ran shortly after a cron slot — the common case with 7 collectors
    firing up to 3x/day. A run with no conclusion is not evidence in either direction."""
    rows = []
    for r in raw_runs:
        concl = r.get("conclusion")
        if not concl:                               # queued / in_progress -> not evidence
            continue
        dt = datetime.fromisoformat(str(r["createdAt"]).replace("Z", "+00:00"))
        rows.append({"day": dt.date().isoformat(), "conclusion": concl,
                     "id": r.get("databaseId"), "event": r.get("event", "")})
    return rows


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
    # non-terminal conclusions are not evidence either way (F10 — also filtered in run_rows)
    terminal = [r for r in inwin if r["conclusion"] not in ("", None, "in_progress", "queued", "waiting")]
    failed = sorted({r["day"] for r in terminal if r["conclusion"] not in ("success", "skipped")})
    ok_days = sorted({r["day"] for r in terminal if r["conclusion"] == "success"})
    unreadable = state.get(UNREADABLE)
    quarantined = str(state.get("last_action", "")).startswith("quarantined")
    paused = bool(state.get("paused"))
    green = bool(ok_days) and not failed and not quarantined and not paused and not unreadable
    return {
        "green": green,
        "runs_in_window": len(terminal),
        "ok_days": ok_days,
        "failed_days": failed,
        "manifest_days": sorted(d for d in manifest_days if d in wdays),
        "quarantined": quarantined,
        "paused": paused,
        "state_unreadable": unreadable,
        # unreadable state outranks every other verdict: we cannot assert green off evidence we
        # could not read, and BUILD-01 acceptance hangs on this call.
        "verdict": ("GREEN" if green else
                    ("STATE-UNREADABLE" if unreadable else
                     "PAUSED" if paused else "QUARANTINED" if quarantined else
                     "FAILED-RUN" if failed else "NO-FIRING-IN-WINDOW")),
    }
