"""Feature construction for the Hospital/Care Distress retrocast v1.

Executes WORKBOOK §6 (staffing features), §4/§5 (labels and their censoring), §7 (the
as-known-then publication lag) and §3 (CCN identity). It decides nothing: every constant comes
from `spec.py`, which was committed and pushed before this file existed.

Reads archived, hash-pinned bytes only. There is deliberately no HTTP client imported anywhere in
this module or its caller, so "no live endpoint" is a property of the code rather than a promise.

One reading the workbook left implicit, recorded here and in the report because a hostile reviewer
should check it rather than discover it: **a "reported day" is a daily PBJ row with
`MDScensus > 0`.** A zero-census day contributes no hours-per-resident-day and cannot enter a mean,
a standard deviation or a below-threshold count, so it is excluded from the daily series and from
the `MIN_QUARTER_DAYS` count. Zero-census days are counted and published.
"""
from __future__ import annotations

import csv
import io
import math
from datetime import date, timedelta

from . import spec as S

csv.field_size_limit(1 << 24)


# --------------------------------------------------------------------------- calendar helpers
def quarter_of(d: date) -> str:
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


def quarter_end(q: str) -> date:
    y, n = int(q[:4]), int(q[-1])
    return {1: date(y, 3, 31), 2: date(y, 6, 30), 3: date(y, 9, 30), 4: date(y, 12, 31)}[n]


def quarter_available_from(q: str) -> date:
    """WORKBOOK §7: quarter Q may only be used for weeks starting at/after Q_end + 135 days."""
    return quarter_end(q) + timedelta(days=S.PBJ_AVAILABILITY_LAG_DAYS)


def prev_quarter(q: str, n: int = 1) -> str:
    y, k = int(q[:4]), int(q[-1])
    k -= n
    while k <= 0:
        k += 4
        y -= 1
    return f"{y}Q{k}"


def quarters_between(lo: str, hi: str):
    out, q = [], lo
    while True:
        out.append(q)
        if q == hi:
            return out
        y, k = int(q[:4]), int(q[-1])
        k += 1
        if k > 4:
            k, y = 1, y + 1
        q = f"{y}Q{k}"
        if y > 2100:                                    # never loop forever on a bad argument
            raise ValueError(f"quarters_between({lo!r}, {hi!r}) did not terminate")


# --------------------------------------------------------------------------- ground truth
def load_deficiencies(raw: bytes):
    """-> (harm_events, all_events, first_observed, states)

    harm_events / all_events: sorted lists of (ccn, date) DISTINCT SURVEY EVENTS (WORKBOOK §4 --
    418,479 rows collapse to ~90,760 events; grading rows would count one inspection dozens of
    times). first_observed[ccn] is that facility's earliest citation date, which is where its
    observed window begins (WORKBOOK §5, the per-facility left truncation).
    """
    rdr = csv.reader(io.StringIO(raw.decode("utf-8-sig", errors="replace")))
    head = next(rdr)
    ix = {name: head.index(name) for name in
          ("CMS Certification Number (CCN)", "Survey Date", "Scope Severity Code", "State")}
    i_ccn, i_dt, i_sev, i_st = (ix["CMS Certification Number (CCN)"], ix["Survey Date"],
                                ix["Scope Severity Code"], ix["State"])
    sev_by_event, states, n_rows, bad_date = {}, {}, 0, 0
    for row in rdr:
        n_rows += 1
        ccn = row[i_ccn].strip()
        ds = row[i_dt].strip()
        if not ccn or not ds:
            bad_date += 1
            continue
        try:
            d = date(int(ds[:4]), int(ds[5:7]), int(ds[8:10]))
        except (ValueError, IndexError):
            bad_date += 1
            continue
        sev_by_event.setdefault((ccn, d), set()).add(row[i_sev].strip().upper())
        states.setdefault(ccn, row[i_st].strip())

    all_events, harm_events, ij_events, first = [], [], [], {}
    for (ccn, d), sevs in sev_by_event.items():
        all_events.append((ccn, d))
        if sevs & S.HARM_SEVERITY:
            harm_events.append((ccn, d))
        if sevs & S.IMMEDIATE_JEOPARDY:
            ij_events.append((ccn, d))
        if ccn not in first or d < first[ccn]:
            first[ccn] = d
    all_events.sort()
    harm_events.sort()
    ij_events.sort()
    return {"all_events": all_events, "harm_events": harm_events, "ij_events": ij_events,
            "first_observed": first, "states": states, "rows": n_rows,
            "unparseable_rows": bad_date}


# --------------------------------------------------------------------------- signal
class QuarterAgg:
    """Running aggregate for one (CCN, quarter). Sums of numerators over sums of denominators, so
    one odd day can neither divide by zero nor dominate (WORKBOOK §6)."""
    __slots__ = ("hours", "rn_hours", "ctr_hours", "census", "days", "zero_days",
                 "wd_h", "wd_c", "we_h", "we_c", "daily", "state", "county", "county_fips", "name")

    def __init__(self):
        self.hours = self.rn_hours = self.ctr_hours = self.census = 0.0
        self.days = self.zero_days = 0
        self.wd_h = self.wd_c = self.we_h = self.we_c = 0.0
        self.daily = []
        self.state = self.county = self.county_fips = self.name = ""


def load_pbj_quarter(raw: bytes, want_features: bool = True):
    """-> ({provnum: QuarterAgg}, short_row_count). Column indices are resolved from the header of
    the archived bytes, never assumed: a reshaped release must fail loudly, not silently
    mis-index."""
    txt = io.StringIO(raw.decode("utf-8-sig", errors="replace"))
    rdr = csv.reader(txt)
    head = [h.strip() for h in next(rdr)]
    need = ["PROVNUM", "PROVNAME", "STATE", "COUNTY_NAME", "COUNTY_FIPS", "WorkDate", "MDScensus",
            *S.NURSE_HOURS]
    missing = [c for c in need if c not in head]
    if missing:
        raise SystemExit(f"ABORT: archived PBJ release is missing columns {missing} "
                         f"(schema drift — the run must not guess)")
    ix = {c: head.index(c) for c in head}
    i_p, i_n, i_s = ix["PROVNUM"], ix["PROVNAME"], ix["STATE"]
    i_cn, i_cf, i_wd, i_mc = ix["COUNTY_NAME"], ix["COUNTY_FIPS"], ix["WorkDate"], ix["MDScensus"]
    hour_ix = [ix[c] for c in S.NURSE_HOURS]
    rn_ix = [ix[c] for c in S.RN_HOURS]
    ctr_ix = [ix[c + S.CONTRACT_SUFFIX] for c in S.NURSE_HOURS if c + S.CONTRACT_SUFFIX in ix]

    ncol = len(head)
    out, short_rows = {}, 0
    for row in rdr:
        if len(row) < ncol:
            # Observed: exactly one trailing empty line per release. Counted rather than swallowed
            # so that a release which genuinely changed width shows up as a number, not a silence.
            short_rows += 1
            continue
        p = row[i_p].strip()
        if not p:
            continue
        a = out.get(p)
        if a is None:
            a = out[p] = QuarterAgg()
            a.state, a.name = row[i_s].strip(), row[i_n].strip()
            a.county, a.county_fips = row[i_cn].strip(), row[i_cf].strip()
        if not want_features:
            continue
        try:
            census = float(row[i_mc] or 0)
        except ValueError:
            census = 0.0
        if census <= 0:
            a.zero_days += 1
            continue
        tot = 0.0
        for j in hour_ix:
            v = row[j]
            if v:
                try:
                    tot += float(v)
                except ValueError:
                    pass
        rn = 0.0
        for j in rn_ix:
            v = row[j]
            if v:
                try:
                    rn += float(v)
                except ValueError:
                    pass
        ctr = 0.0
        for j in ctr_ix:
            v = row[j]
            if v:
                try:
                    ctr += float(v)
                except ValueError:
                    pass
        a.hours += tot
        a.rn_hours += rn
        a.ctr_hours += ctr
        a.census += census
        a.days += 1
        a.daily.append(tot / census)
        ws = row[i_wd].strip()
        try:
            wd = date(int(ws[:4]), int(ws[4:6]), int(ws[6:8])).weekday()
        except (ValueError, IndexError):
            continue
        if wd >= 5:
            a.we_h += tot
            a.we_c += census
        else:
            a.wd_h += tot
            a.wd_c += census
    return out, short_rows


def quarter_features(agg: QuarterAgg, trend_base: float | None):
    """WORKBOOK §6. Returns None when the (CCN, quarter) is inadmissible — never an imputed row."""
    if agg.days < S.MIN_QUARTER_DAYS or agg.census <= 0:
        return None
    if agg.we_c <= 0 or agg.wd_c <= 0:                  # features 5-8 need both day kinds
        return None
    # Some facility-quarters report a resident census but ZERO nursing hours on every weekday.
    # `weekend_gap` is then undefined, not zero: there is no weekday staffing level to compare a
    # weekend against. The workbook's rule for an inadmissible quarter is drop-and-count, never an
    # imputed value, so that is what happens — the count is published.
    if agg.wd_h <= 0 or agg.hours <= 0:
        return None
    if trend_base is None or trend_base <= 0:
        return None
    hprd_total = agg.hours / agg.census
    hprd_rn = agg.rn_hours / agg.census
    mean_daily = sum(agg.daily) / len(agg.daily)
    if mean_daily <= 0:
        return None
    var = sum((x - mean_daily) ** 2 for x in agg.daily) / len(agg.daily)
    return {
        "hprd_total": hprd_total,
        "hprd_rn": hprd_rn,
        "rn_share": (hprd_rn / hprd_total) if hprd_total > 0 else 0.0,
        "contract_frac": (agg.ctr_hours / agg.hours) if agg.hours > 0 else 0.0,
        "weekend_gap": 1.0 - ((agg.we_h / agg.we_c) / (agg.wd_h / agg.wd_c)),
        "hprd_cv": math.sqrt(var) / mean_daily,
        "hprd_trend": hprd_total / trend_base - 1.0,
        "low_days_frac": sum(1 for x in agg.daily if x < S.CMS_MIN_HPRD) / len(agg.daily),
        "census": agg.census / agg.days,
    }


# --------------------------------------------------------------------------- prior-harm baseline
def prior_rate_fn(events):
    """-> f(ccn, cutoff_date, observed_years) = events at that CCN strictly before the cutoff,
    per observed year. A RATE, not a fixed-window count: a fixed window would have required a
    facility to have been observed for its whole length, which excludes the frequently-surveyed
    (short-window) facilities — exactly the censoring bias WORKBOOK §5 exists to avoid."""
    by = {}
    for ccn, d in events:
        by.setdefault(ccn, []).append(d)
    for v in by.values():
        v.sort()
    import bisect

    def f(ccn, cutoff, observed_years):
        v = by.get(ccn)
        if not v or observed_years <= 0:
            return 0.0
        return bisect.bisect_left(v, cutoff) / observed_years

    return f
