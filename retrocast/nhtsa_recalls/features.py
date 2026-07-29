"""Signal construction for the NHTSA Shadow Recalls retrocast v1.

Implements PRE-REGISTRATION-v1 §3 verbatim: for each (make, model, model-year, component-group)
cell and each week t, five features computed ONLY from complaints received <= t.

    1 n_trailing     complaints in the trailing W = 12 weeks
    2 rate_ratio     n_trailing / the cell's own trailing-52-week baseline (self-normalized)
    3 accel          week-over-week change in n_trailing
    4 severity_frac  fraction of trailing complaints flagged crash OR fire OR injury/death
    5 hazard_lang    fraction of trailing narratives matching the frozen hazard lexicon

Leak control is structural, not a promise: the rolling windows only ever read week buckets at or
before t, and a unit test plants a complaint at t+1 and asserts the features at t do not move.

Stdlib-only. Streams the archived flat files straight out of their zips — nothing is fetched live
(constitution: government-continuity posture; the archived vintage is the retrocast-of-record).
"""
from __future__ import annotations

import datetime as _dt
import io
import zipfile
from array import array as _array

from . import lexicon as L

EPOCH = _dt.date(1970, 1, 1)
FEATURE_NAMES = ("n_trailing", "rate_ratio", "accel", "severity_frac", "hazard_lang")
NFEAT = len(FEATURE_NAMES)

# 1-indexed field positions, pinned to the archived layouts (see WORKBOOK §1).
C_MAKE, C_MODEL, C_YEAR = 4, 5, 6
C_CRASH, C_FIRE, C_INJURED, C_DEATHS = 7, 9, 10, 11
C_COMPDESC, C_DATEA, C_LDATE, C_CDESCR = 12, 16, 17, 20
R_MAKE, R_MODEL, R_YEAR, R_COMPNAME, R_CAMPNO, R_RCDATE = 3, 4, 5, 7, 2, 16


def week_of(yyyymmdd: str):
    """Integer week index (days since 1970-01-01 // 7) — the harness's `t`. None if unparseable."""
    s = yyyymmdd.strip()
    if len(s) != 8 or not s.isdigit():
        return None
    try:
        d = _dt.date(int(s[:4]), int(s[4:6]), int(s[6:]))
    except ValueError:
        return None
    return (d - EPOCH).days // 7


def week_start(week: int) -> _dt.date:
    """First day of a week bucket — used only to print human dates in the receipts."""
    return EPOCH + _dt.timedelta(days=7 * week)


def week_of_date(iso: str) -> int:
    return week_of(iso.replace("-", ""))


def calendar_week(week: int) -> int:
    """ISO week number of the bucket — the seasonality-only dumb baseline's only input."""
    return week_start(week).isocalendar()[1]


# --------------------------------------------------------------------------- streaming readers
def _rows(zip_path, expect_fields):
    z = zipfile.ZipFile(zip_path)
    member = [i.filename for i in z.infolist() if i.filename.lower().endswith(".txt")][0]
    with z.open(member) as fh:
        for line in io.TextIOWrapper(fh, encoding="utf-8", errors="replace"):
            parts = line.rstrip("\n").split("\t")
            if len(parts) == expect_fields:
                yield parts


def read_complaints(zip_path, lo_week, hi_week):
    """-> {cell: {week: [n, severe, hazard]}}. A complaint enters the week of
    max(DATEA, LDATE) — the more conservative of the two as-known-then dates (WORKBOOK §1)."""
    cells = {}
    kept = skipped = 0
    for p in _rows(zip_path, 51):
        w = week_of(max(p[C_DATEA - 1], p[C_LDATE - 1]))
        if w is None or w < lo_week or w > hi_week:
            skipped += 1
            continue
        key = L.cell_key(p[C_MAKE - 1], p[C_MODEL - 1], p[C_YEAR - 1], p[C_COMPDESC - 1])
        severe = (p[C_CRASH - 1].strip().upper() == "Y" or p[C_FIRE - 1].strip().upper() == "Y"
                  or _nonzero(p[C_INJURED - 1]) or _nonzero(p[C_DEATHS - 1]))
        hazard = L.hazard_hit(p[C_CDESCR - 1])
        bucket = cells.setdefault(key, {})
        row = bucket.get(w)
        if row is None:
            bucket[w] = [1, int(severe), int(hazard)]
        else:
            row[0] += 1
            row[1] += int(severe)
            row[2] += int(hazard)
        kept += 1
    return cells, kept, skipped


def _nonzero(v):
    v = v.strip()
    return v.isdigit() and int(v) > 0


def read_recalls(zip_path, lo_week, hi_week):
    """-> list of (cell, event_week, campno). Event date = RCDATE, the recall REPORT-RECEIVED
    date (registration §1). ODATE (owner notification) is deliberately not used — it post-dates
    the event and would inflate every lead time."""
    out = []
    for p in _rows(zip_path, 29):
        w = week_of(p[R_RCDATE - 1])
        if w is None or w < lo_week or w > hi_week:
            continue
        key = L.cell_key(p[R_MAKE - 1], p[R_MODEL - 1], p[R_YEAR - 1], p[R_COMPNAME - 1])
        out.append((key, w, p[R_CAMPNO - 1].strip()))
    return out


# ------------------------------------------------------------------------------- the five features
def cell_features(weeks, lo, hi, trailing=None, baseline=None):
    """weeks: {week: [n, severe, hazard]} for ONE cell. Yields
    (t, n_trailing, rate_ratio, accel, severity_frac, hazard_lang) for every week t in [lo, hi]
    with n_trailing >= 1 (a cell-week with no trailing complaints has no rate to speak of and
    cannot cross any positive threshold — WORKBOOK §4.2, disclosed in the report).

    Every window is [t-k+1, t] — closed at t, so no future bucket can ever be read."""
    trailing = L.TRAILING_WEEKS if trailing is None else trailing
    baseline = L.BASELINE_WEEKS if baseline is None else baseline
    if not weeks:
        return
    first, last = min(weeks), max(weeks)
    # Start one week early so accel at the first scored week is a true week-over-week delta.
    start = max(first, lo - 1)
    end = min(hi, last + trailing - 1)         # after this the trailing window is empty again
    if start > end:
        return
    get = weeks.get

    def _sum(a, b):                            # closed window [a, b], read once at the start
        n = sev = haz = 0
        for k in range(a, b + 1):
            r = get(k)
            if r:
                n += r[0]
                sev += r[1]
                haz += r[2]
        return n, sev, haz

    n, sev, haz = _sum(start - trailing + 1, start)
    c52 = _sum(start - baseline + 1, start)[0]
    n_prev = None
    for t in range(start, end + 1):
        if t > start:                          # slide the closed windows forward by one week
            enter, drop_t, drop_b = get(t), get(t - trailing), get(t - baseline)
            if enter:
                n += enter[0]; sev += enter[1]; haz += enter[2]; c52 += enter[0]
            if drop_t:
                n -= drop_t[0]; sev -= drop_t[1]; haz -= drop_t[2]
            if drop_b:
                c52 -= drop_b[0]
        if n == 0:
            n_prev = 0
            continue
        if t >= lo:
            base = c52 * (trailing / baseline)  # 52-week count scaled to a 12-week window
            rate_ratio = n / base if base else 0.0
            accel = float(n - n_prev) if n_prev is not None else float(n)
            yield (t, n, rate_ratio, accel, sev / n, haz / n)
        n_prev = n


def build(complaints_zip, recalls_zip, *, progress=None):
    """Full signal + label build over the archived vintages. Returns a dict of parallel lists."""
    lo_obs = week_of_date(L.WARMUP_START)
    w0, w1 = week_of_date(L.WINDOW_START), week_of_date(L.WINDOW_END)
    hi_events = w1 + L.HORIZON_WEEKS
    cells, kept, skipped = read_complaints(complaints_zip, lo_obs, w1)
    if progress:
        progress(f"complaints: {kept:,} in-window rows -> {len(cells):,} cells "
                 f"({skipped:,} outside {L.WARMUP_START}..{L.WINDOW_END})")
    events = read_recalls(recalls_zip, w0, hi_events)
    if progress:
        progress(f"recalls: {len(events):,} campaign rows in window")

    ent = {}                       # cell -> compact integer id (the harness's `entity`)
    obs_e, obs_t = _array("i"), _array("i")
    feats = _array("d")            # flat, 5 doubles per cell-week (millions of rows: no tuples)
    for key, weeks in cells.items():
        rows = list(cell_features(weeks, w0, w1))
        if not rows:
            continue
        e = ent.setdefault(key, len(ent))
        for (t, n, rr, acc, sf, hz) in rows:
            obs_e.append(e)
            obs_t.append(t)
            feats.extend((float(n), rr, acc, sf, hz))
    labels = [(ent[k], w) for (k, w, _c) in events if k in ent]
    campaigns = {}
    for (k, w, c) in events:
        if k in ent:
            campaigns.setdefault((ent[k], w), []).append(c)
    if progress:
        progress(f"scored cell-weeks: {len(obs_e):,}; labels joined to a complaint-bearing cell: "
                 f"{len(labels):,} / {len(events):,}")
    # `features` is a FLAT array: 5 doubles per cell-week, in FEATURE_NAMES order.
    return {"entity": obs_e, "t": obs_t, "features": feats, "labels": labels,
            "cells": {v: k for k, v in ent.items()}, "campaigns": campaigns,
            "window": (w0, w1), "n_cells_seen": len(cells), "n_events_seen": len(events)}
