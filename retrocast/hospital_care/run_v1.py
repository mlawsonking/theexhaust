"""Run the pre-registered Hospital/Care Distress retrocast (v1) and emit `results/v1/`.

    python -m retrocast.hospital_care.run_v1 [--cache <dir>] [--out <dir>]

Everything this script may decide was frozen before it was written: the signal is WORKBOOK §6, the
labels §4/§5, the publication lag §7, the splits §9, and the pass bars are PRE-REGISTRATION §7.
The registration commit is asserted to be an ancestor of HEAD and the run **aborts** otherwise.
This script's only job is to execute that and write down what happened — including a failure.

Inputs are ARCHIVED vintages pinned by sha256 below, pulled from R2. If the bytes do not hash to
the pin the run aborts: a retrocast against an unpinned file is not a retrocast. No HTTP client is
imported anywhere in this module or in `features`, and no LLM is involved at any point — a critic
with no API key must be able to rerun every number.

numpy is used for the logistic fit only; everything else is stdlib.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import os
import pathlib
import pickle
import statistics
import subprocess
import sys
import time
from datetime import date, timedelta

from retrocast import harness
from retrocast.hospital_care import features as F
from retrocast.hospital_care import spec as S

REPO = pathlib.Path(__file__).resolve().parents[2]
RESULTS = REPO / "retrocast" / "hospital-care" / "results" / "v1"
REGISTRATION = "retrocast/hospital-care/PRE-REGISTRATION-v1.md"
FREEZE = "retrocast/hospital_care/spec.py"
ARCHIVE_BASE = "https://archive.theexhaust.org/"

# The retrocast-of-record. Feature quarters 2022Q2..2025Q1 (WORKBOOK §9); the later quarters are
# read for the WORKBOOK §3/R3 closure check ONLY (presence of the facility at horizon end) and
# contribute no feature value anywhere.
PBJ_VINTAGES = {
    "2022Q2": {"r2_key": "raw/cms-pbj/2022Q2/2026/07/30/0429-6aaadd46bcb6.csv.zst",
               "sha256": "6aaadd46bcb6a722bb84133cbb7941c247de8e0a36b3e37687705aa1a8264582",
               "rows": 1337155,
               "source_url": "https://data.cms.gov/sites/default/files/2022-10/e60c6df7-34d7-4239-b601-86c91e874029/PBJ_dailynursestaffing_CY2022Q2.csv"},
    "2022Q3": {"r2_key": "raw/cms-pbj/2022Q3/2026/07/30/0429-d1b6d195f6a9.csv.zst",
               "sha256": "d1b6d195f6a950843b25c981957fb8a32ed602c3a86b8b6d44d5696789c1cf12",
               "rows": 1351297,
               "source_url": "https://data.cms.gov/sites/default/files/2023-01/893d09c1-df09-41ef-b7b9-b47e9dbb6e05/PBJ_dailynursestaffing_CY2022Q3.csv"},
    "2022Q4": {"r2_key": "raw/cms-pbj/2022Q4/2026/07/30/0429-4676ae6f863c.csv.zst",
               "sha256": "4676ae6f863c4b30cf9596a5ba9f706a603cfab346891dc7829caaafbb068cce",
               "rows": 1352677,
               "source_url": "https://data.cms.gov/sites/default/files/2023-04/8ca96e0e-89f3-4457-a3c0-8a0957297f5b/PBJ_dailynursestaffing_CY2022Q4.csv"},
    "2023Q1": {"r2_key": "raw/cms-pbj/2023Q1/2026/07/30/0429-3d90a766a57f.csv.zst",
               "sha256": "3d90a766a57f24d7fec9ccef723cca0f21d16683deddd1b4b9b0cc8cdd17ea42",
               "rows": 1322910,
               "source_url": "https://data.cms.gov/sites/default/files/2023-06/034ca96a-0dde-471f-acac-7750532e8edb/PBJ_dailynursestaffing_CY2023Q1.csv"},
    "2023Q2": {"r2_key": "raw/cms-pbj/2023Q2/2026/07/30/0429-909a041d2d9e.csv.zst",
               "sha256": "909a041d2d9e97c5a5958820da0d2777a3cbf3e672b0d2c210caa728ba136949",
               "rows": 1328145,
               "source_url": "https://data.cms.gov/sites/default/files/2023-10/5bd71a45-b092-4072-88b8-d40d54704d8c/PBJ_dailynursestaffing_CY2023Q2.csv"},
    "2023Q3": {"r2_key": "raw/cms-pbj/2023Q3/2026/07/30/0429-c949dbb937ec.csv.zst",
               "sha256": "c949dbb937ec4cca1ce9db5ebf25f965464bae789513334b855c93732c9877cc",
               "rows": 1344212,
               "source_url": "https://data.cms.gov/sites/default/files/2024-01/8e987728-d824-48a0-b041-2d3c7a0ee2e8/PBJ_dailynursestaffing_CY2023Q3.csv"},
    "2023Q4": {"r2_key": "raw/cms-pbj/2023Q4/2026/07/30/0429-089657aef15b.csv.zst",
               "sha256": "089657aef15b7e51d160214dc95d5960f556aa0625e59dddd73727b944f136e5",
               "rows": 1344028,
               "source_url": "https://data.cms.gov/sites/default/files/2024-04/0cd535dd-4611-4b0b-8380-65444c2f6236/PBJ_dailynursestaffing_CY2023Q4.csv"},
    "2024Q1": {"r2_key": "raw/cms-pbj/2024Q1/2026/07/30/0429-0486a24359e7.csv.zst",
               "sha256": "0486a24359e7e8d92d056f4abdbe6a0e922d0ba4f198e4d3f9d9d328b8a42dc5",
               "rows": 1330966,
               "source_url": "https://data.cms.gov/sites/default/files/2024-07/5273cb88-fb7c-4ea7-821a-2e1453044c64/PBJ_dailynursestaffing_CY2024Q1.csv"},
    "2024Q2": {"r2_key": "raw/cms-pbj/2024Q2/2026/07/30/0429-c8c01316cde7.csv.zst",
               "sha256": "c8c01316cde7ab80a9ba244a851a58f9128b98e7407a7576e439e1c27bc1350c",
               "rows": 1325324,
               "source_url": "https://data.cms.gov/sites/default/files/2024-10/79f8602d-e17a-4ba3-9182-3287ccff9d3c/PBJ_dailynursestaffing_CY2024Q2.csv"},
    "2024Q3": {"r2_key": "raw/cms-pbj/2024Q3/2026/07/30/0429-267f9fbf46f1.csv.zst",
               "sha256": "267f9fbf46f1db4b1ad0e2af36b16f126d748ff4848eaeae2bcb4f37869a8590",
               "rows": 1338416,
               "source_url": "https://data.cms.gov/sites/default/files/2025-01/0e5403bd-0ae6-4177-b2fa-ecd9e0944316/PBJ_dailynursestaffing_CY2024Q3.csv"},
    "2024Q4": {"r2_key": "raw/cms-pbj/2024Q4/2026/07/30/0429-1a2245928d0e.csv.zst",
               "sha256": "1a2245928d0e71602cb4720970e76610635b48312ccb827a3bc19e649f507a65",
               "rows": 1340716,
               "source_url": "https://data.cms.gov/sites/default/files/2025-04/4f8bee34-7c03-4bda-9ed9-756db4200310/PBJ_dailynursestaffing_CY2024Q4.csv"},
    "2025Q1": {"r2_key": "raw/cms-pbj/2025Q1/2026/07/30/0429-2c3df765aeb6.csv.zst",
               "sha256": "2c3df765aeb672de1db178a2594dd79f0d0297e8268eaebfaff8c4f519c4bf96",
               "rows": 1309590,
               "source_url": "https://data.cms.gov/sites/default/files/2025-07/e8e9efa9-9498-4286-a31c-ed4e5548a30c/PBJ_dailynursestaffing_CY2025Q1.csv"},
    # ---- presence-only (WORKBOOK §3/R3 closure censoring). These contribute NO feature value:
    # `load_pbj_quarter(..., want_features=False)` reads their PROVNUM column and nothing else.
    # Using a later release to establish that a facility still existed at horizon end conditions
    # the universe on a post-t fact; it drops cells that are almost all negatives, which RAISES
    # the base rate and makes the precision bar easier. Both the count and that direction are
    # published (`exclusions.closed_before_horizon_end`, and the full-grid base rate).
    "2025Q2": {"r2_key": "raw/cms-pbj/2025Q2/2026/07/30/0429-5c1965fc3136.csv.zst",
               "sha256": "5c1965fc3136a30f9472bc443a30a59c237e8dd143f11e9af7eddec398d1cdf5",
               "rows": 1322867, "presence_only": True,
               "source_url": "https://data.cms.gov/sites/default/files/2025-10/0fd38f13-e99e-4b2f-8162-50603c89966d/PBJ_dailynursestaffing_CY2025Q2.csv"},
    "2025Q3": {"r2_key": "raw/cms-pbj/2025Q3/2026/07/30/0429-9cc063f19283.csv.zst",
               "sha256": "9cc063f19283f110e6184cb2fee124fa76a2b89f646c4d90db4976139c28f3c8",
               "rows": 1332804, "presence_only": True,
               "source_url": "https://data.cms.gov/sites/default/files/2026-01/13db0b58-0df6-4288-8567-fc2a4f6ba415/PBJ_dailynursestaffing_CY2025Q3.csv"},
    "2025Q4": {"r2_key": "raw/cms-pbj/2025Q4/2026/07/29/2118-d0423869d1e0.csv.zst",
               "sha256": "d0423869d1e07227270d323c26e2b29fecec50a1c55f2291d0325f00c2e18571",
               "rows": 1321304, "presence_only": True,
               "source_url": "https://data.cms.gov/sites/default/files/2026-04/8f85c7d4-a1f6-4b36-ad20-17abc8aa57d2/PBJ_dailynursestaffing_CY2025Q4.csv"},
    "2026Q1": {"r2_key": "raw/cms-pbj/2026Q1/2026/07/29/2108-32873501edc3.csv.zst",
               "sha256": "32873501edc3383edc2177f4ada29e5f055b0d1459bea4cd0c0190e581236e1e",
               "rows": 1303830, "presence_only": True,
               "source_url": "https://data.cms.gov/sites/default/files/2026-06/5c2f045b-7246-457a-9fac-c7fb92f7c352/PBJ_dailynursestaffing_CY2026Q1.csv"},
}

FEATURE_QUARTER_PINS = {q: v for q, v in PBJ_VINTAGES.items() if not v.get("presence_only")}

DEFICIENCIES = {
    "r2_key": "raw/cms-deficiencies/2026/07/28/0552-d70b67207315.csv.zst",
    "sha256": "d70b67207315d0e638fa5f27166bbda35880800ee24083a8f59139131be224f4",
    "rows": 418479, "collected_at": "2026-07-28T05:52:30Z",
    "source_url": "https://data.cms.gov/provider-data/sites/default/files/resources/"
                  "a10af81bcb17bd0ae040383b3da50d10_1781194536/NH_HealthCitations_Jun2026.csv",
}

_T0 = time.time()


def log(msg):
    print(f"[{time.time() - _T0:7.1f}s] {msg}", flush=True)


# --------------------------------------------------------------------------------- provenance
def _git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True).stdout.strip()


def provenance():
    """Registration commit + the git ordering proof (SPEC-08 §2 / §7 criterion 1)."""
    reg = _git("log", "-1", "--format=%H", "--", REGISTRATION)
    frz = _git("log", "-1", "--format=%H", "--", FREEZE)
    head = _git("rev-parse", "HEAD")
    out = {
        "registration_commit": reg,
        "registration_committed": _git("log", "-1", "--format=%cI", reg),
        "workbook_freeze_commit": frz,
        "workbook_freeze_committed": _git("log", "-1", "--format=%cI", frz),
        "code_commit": head,
        "code_committed": _git("log", "-1", "--format=%cI", head),
        "dirty": bool(_git("status", "--porcelain", "--untracked-files=no")),
    }
    for label, c in (("registration", reg), ("workbook_freeze", frz)):
        out[f"{label}_is_ancestor_of_code"] = subprocess.run(
            ["git", "merge-base", "--is-ancestor", c, head], cwd=REPO).returncode == 0
    # BUILD-PROTOCOL §2.7: a hash must be in PUSHED history. `git cat-file -e` passes on a hash
    # that only ever existed locally (e.g. before a rebase), which is a false provenance receipt.
    out["registration_is_ancestor_of_origin_main"] = subprocess.run(
        ["git", "merge-base", "--is-ancestor", reg, "origin/main"], cwd=REPO).returncode == 0
    return out


# --------------------------------------------------------------------------------- archived IO
def fetch_archived(key, sha256, cache_dir):
    """Return the DECOMPRESSED bytes of an archived object, verifying the pin first.

    boto3 is imported lazily and only here, so `features` stays import-clean; the archive is
    content-addressed, so a cached file is re-hashed on every run rather than trusted by name.
    """
    import zstandard as zstd
    cache = pathlib.Path(cache_dir) / (sha256[:16] + ".zst")
    if cache.exists():
        blob = cache.read_bytes()
    else:
        import boto3
        s3 = boto3.client("s3", endpoint_url=os.environ["R2_ENDPOINT"],
                          aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                          aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
                          region_name="auto")
        blob = s3.get_object(Bucket=os.environ["R2_BUCKET"], Key=key)["Body"].read()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(blob)
    raw = zstd.ZstdDecompressor().decompress(blob, max_output_size=1 << 31)
    got = hashlib.sha256(raw).hexdigest()
    if got != sha256:
        raise SystemExit(f"ABORT: archived vintage hash mismatch for {key}\n"
                         f"  want {sha256}\n  got  {got}\n"
                         f"  expected object: {ARCHIVE_BASE}{key}")
    return raw


def assert_publication_lag_is_conservative():
    """Independent evidence for the WORKBOOK §7 as-known-then rule.

    CMS puts the publication month in the download URL path (`.../files/YYYY-MM/<uuid>/...`). For
    every feature quarter, the file was published no earlier than that month — so if
    `Q_end + 135 days` lands on or after the END of that month, the 135-day rule cannot have let
    the run see a quarter before it was public. Checked, not assumed; a violation aborts.
    """
    import re
    rows = []
    for q, v in sorted(PBJ_VINTAGES.items()):
        m = re.search(r"/files/(\d{4})-(\d{2})/", v["source_url"])
        if not m:
            raise SystemExit(f"ABORT: cannot read a publication month out of {q}'s source URL")
        y, mo = int(m.group(1)), int(m.group(2))
        nxt = date(y + (mo == 12), (mo % 12) + 1, 1)
        pub_month_end = nxt - timedelta(days=1)
        usable = F.quarter_available_from(q)
        rows.append({"quarter": q, "quarter_end": str(F.quarter_end(q)),
                     "url_publication_month": f"{y}-{mo:02d}",
                     "usable_from_under_rule": str(usable),
                     "ok": usable >= pub_month_end})
        if usable < pub_month_end:
            raise SystemExit(
                f"ABORT: the {S.PBJ_AVAILABILITY_LAG_DAYS}-day availability rule would have used "
                f"{q} from {usable}, but its URL says it was published in {y}-{mo:02d}. The "
                f"as-known-then control is violated; the run must not proceed.")
    return rows


# --------------------------------------------------------------------------------- the build
def build(cache_dir, progress=log):
    """Everything up to (but not including) the model: features, labels, the scored universe."""
    progress("verifying the as-known-then publication-lag rule against the source URLs")
    lag_rows = assert_publication_lag_is_conservative()
    progress(f"  {len(lag_rows)}/{len(lag_rows)} feature quarters publish no earlier than the "
             f"{S.PBJ_AVAILABILITY_LAG_DAYS}-day rule allows them to be used")

    raw = fetch_archived(DEFICIENCIES["r2_key"], DEFICIENCIES["sha256"], cache_dir)
    gt = F.load_deficiencies(raw)
    del raw
    progress(f"ground truth: {gt['rows']:,} rows -> {len(gt['all_events']):,} distinct survey "
             f"events, {len(gt['harm_events']):,} harm, {len(gt['ij_events']):,} IJ, "
             f"{len(gt['first_observed']):,} CCNs")

    feature_qs = F.quarters_between(S.PBJ_FIRST_QUARTER, S.PBJ_LAST_QUARTER)
    # WORKBOOK §3/R3: presence at the END of the label horizon. Derived from the frozen splits,
    # not a new frozen constant.
    last_horizon_end = S.TEST_LAST_WEEK_START + timedelta(days=7 * S.HORIZON_WEEKS + 6)
    presence_qs = F.quarters_between(F.quarter_of(S.TRAIN_FIRST_WEEK_START),
                                     F.quarter_of(last_horizon_end))
    all_qs = sorted(set(feature_qs) | set(presence_qs), key=lambda q: (int(q[:4]), int(q[-1])))
    missing_pins = [q for q in all_qs if q not in PBJ_VINTAGES and q in feature_qs]
    if missing_pins:
        raise SystemExit(f"ABORT: no archived pin for feature quarter(s) {missing_pins}")

    # Quarters are walked oldest-first so the four-quarter trend baseline is already in hand when
    # a quarter's features are computed. Each release's daily series is discarded as soon as its
    # features exist — holding 16 quarters of per-facility daily HPRD at once is ~0.5 GB for no
    # reason.
    hprd, feats_by_q, present, states, names, geo = {}, {}, {}, {}, {}, {}
    zero_days_total = dropped_trend = dropped_admis = short_rows_total = 0
    for q in all_qs:
        v = PBJ_VINTAGES.get(q)
        if v is None:
            raise SystemExit(f"ABORT: quarter {q} is needed (feature or §3/R3 presence check) but "
                             f"has no archived pin — the run must not silently skip a check")
        wants_features = q in feature_qs
        rawq = fetch_archived(v["r2_key"], v["sha256"], cache_dir)
        aggs, short_rows = F.load_pbj_quarter(rawq, want_features=wants_features)
        del rawq
        short_rows_total += short_rows
        if short_rows > 1:
            progress(f"  !! {q}: {short_rows:,} rows narrower than the header — inspect before "
                     f"trusting this quarter")
        present[q] = set(aggs)
        n_adm = 0
        for p, a in aggs.items():
            states.setdefault(p, set()).add(a.state)
            geo[p] = (a.state, a.county, a.county_fips, a.name)
            if not wants_features:
                continue
            names.setdefault(p, set()).add(a.name)
            if a.days < S.MIN_QUARTER_DAYS or a.census <= 0:
                continue
            n_adm += 1
            zero_days_total += a.zero_days
            hprd[(p, q)] = a.hours / a.census
            base = [hprd.get((p, F.prev_quarter(q, k)))
                    for k in range(1, S.TREND_LOOKBACK_QUARTERS + 1)]
            if any(x is None or x <= 0 for x in base):
                dropped_trend += 1
                continue
            f = F.quarter_features(a, sum(base) / len(base))
            if f is None:
                dropped_admis += 1
                continue
            feats_by_q.setdefault(q, {})[p] = f
        progress(f"  {q}: {len(aggs):,} CCNs"
                 + (f", {n_adm:,} admissible, {len(feats_by_q.get(q, {})):,} featurised"
                    if wants_features else " (presence only)"))
        del aggs

    n_feats = sum(len(v) for v in feats_by_q.values())
    progress(f"features: {n_feats:,} (CCN, quarter) cells "
             f"({dropped_trend:,} lacked a full 4-quarter trend baseline, "
             f"{dropped_admis:,} failed a §6 admissibility rule)")

    # --- WORKBOOK §3/R2: a CCN whose STATE ever moves is dropped entirely
    moved = {p for p, s in states.items() if len(s) > 1}
    progress(f"CCN identity: {len(moved)} CCN(s) changed STATE across quarters (R2 => dropped)")

    # --- name-change sensitivity set (WORKBOOK §3/R1, mandatory re-run)
    renamed = {p for p, s in names.items() if len(s) > 1}
    progress(f"CCN identity: {len(renamed):,} CCN(s) changed PROVNAME inside the study window "
             f"(R1 => kept, with a mandatory sensitivity re-run)")

    return {"gt": gt, "feats_by_q": feats_by_q, "present": present, "geo": geo, "moved": moved,
            "renamed": renamed, "feature_quarters": feature_qs, "presence_quarters": presence_qs,
            "lag_rows": lag_rows, "zero_census_days": zero_days_total,
            "short_rows": short_rows_total, "n_feature_cells": n_feats}


def assemble(d, progress=log):
    """Cells -> (entity, week, feature vector). Applies every §3/§5 exclusion, counting each."""
    gt, feats_by_q, present, moved = d["gt"], d["feats_by_q"], d["present"], d["moved"]
    first_obs = gt["first_observed"]
    prior_harm = F.prior_rate_fn(gt["harm_events"])
    prior_cited = F.prior_rate_fn(gt["all_events"])

    train_w = (S.week(S.TRAIN_FIRST_WEEK_START), S.week(S.TRAIN_LAST_WEEK_START))
    test_w = (S.week(S.TEST_FIRST_WEEK_START), S.week(S.TEST_LAST_WEEK_START))
    weeks = list(range(train_w[0], train_w[1] + 1)) + list(range(test_w[0], test_w[1] + 1))
    gap_weeks = test_w[0] - train_w[1] - 1

    # For each week, the newest quarter usable under the 135-day rule.
    usable_q = {}
    for w in weeks:
        ws = S.week_start(w)
        cands = [q for q in d["feature_quarters"] if F.quarter_available_from(q) <= ws]
        usable_q[w] = max(cands, key=lambda q: (int(q[:4]), int(q[-1]))) if cands else None

    # A quarter that is 'usable' but carries no featurised facility would drop all of its weeks
    # with no counter moving — a hole the drop tally cannot show. Refuse to run instead.
    used = sorted({q for q in usable_q.values() if q})
    empty = [q for q in used if not feats_by_q.get(q)]
    if empty:
        raise SystemExit(f"ABORT: quarter(s) {empty} are the operative feature quarter for scored "
                         f"weeks but produced no features. Every cell in those weeks would vanish "
                         f"silently.")
    progress(f"operative feature quarters: {used} "
             + ", ".join(f"{q}:{len(feats_by_q[q]):,}" for q in used))

    ent_ix, cells = {}, []
    obs_entity, obs_t, obs_X = [], [], []
    prior_h, prior_c = [], []
    drop = {"no_usable_quarter": 0, "quarter_inadmissible": 0, "state_moved": 0,
            "too_little_observed_history": 0, "closed_before_horizon_end": 0, "no_citation_record": 0}
    for w in weeks:
        q = usable_q[w]
        if q is None:
            drop["no_usable_quarter"] += 1
            continue
        ws = S.week_start(w)
        horizon_end = ws + timedelta(days=7 * S.HORIZON_WEEKS + 6)
        pq = F.quarter_of(horizon_end)
        if pq not in present:
            raise SystemExit(f"ABORT: no PBJ release for {pq}, so the §3/R3 closure check for "
                             f"week {ws} cannot run. A silently skipped check is worse than a stop.")
        present_at_end = present[pq]
        obs_cut = ws - timedelta(days=S.MIN_OBSERVED_DAYS)
        for p, f in feats_by_q.get(q, {}).items():
            if p in moved:
                drop["state_moved"] += 1
                continue
            fo = first_obs.get(p)
            if fo is None:
                drop["no_citation_record"] += 1
                continue
            if fo > obs_cut:
                drop["too_little_observed_history"] += 1
                continue
            if p not in present_at_end:
                drop["closed_before_horizon_end"] += 1
                continue
            e = ent_ix.get(p)
            if e is None:
                e = ent_ix[p] = len(cells)
                cells.append(p)
            obs_entity.append(e)
            obs_t.append(w)
            obs_X.append([f[k] for k in S.FEATURES])
            years = max((ws - fo).days / 365.25, 0.0)
            prior_h.append(prior_harm(p, ws, years))
            prior_c.append(prior_cited(p, ws, years))
    progress(f"scored universe: {len(obs_entity):,} cell-weeks over {len(cells):,} facilities "
             f"({gap_weeks} gap weeks never generated); drops {drop}")
    return {"entity": obs_entity, "t": obs_t, "X": obs_X, "prior_harm": prior_h,
            "prior_cited": prior_c, "cells": cells, "ent_ix": ent_ix, "drops": drop,
            "train_w": train_w, "test_w": test_w, "gap_weeks": gap_weeks, "usable_q": usable_q}


# ------------------------------------------------------------------------------ logistic model
def fit_logreg(X, y, *, epochs=2000, lr=0.5):
    """Deterministic full-batch gradient descent on mean log-loss. Zero-initialized weights and a
    base-rate intercept; no randomness, no early stopping, no held-out tuning — the coefficients
    are a function of the train split alone and are published so a critic can rerun them."""
    import numpy as np
    import math as _m
    n, k = X.shape
    base = float(y.mean())
    w = np.zeros(k, dtype=np.float64)
    b = _m.log(base / (1 - base)) if 0 < base < 1 else 0.0
    for _ in range(epochs):
        p = 1.0 / (1.0 + np.exp(-(X @ w + b)))
        g = p - y
        w -= lr * (X.T @ g) / n
        b -= lr * float(g.mean())
    return w, b


def grad_norm(X, y, w, b):
    """||mean gradient|| at the fitted point — the receipt that the published coefficients are the
    pre-registered regression and not a half-converged optimizer artefact."""
    import numpy as np
    g = 1.0 / (1.0 + np.exp(-(X @ w + b))) - y
    return float(np.linalg.norm(np.concatenate([(X.T @ g) / len(y), [g.mean()]])))


def logloss(X, y, w, b):
    import numpy as np
    z = X @ w + b
    return float(np.mean(np.logaddexp(0.0, z) - y * z))


# --------------------------------------------------------------------------------- the run
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", default=str(REPO / ".cache" / "hospital-care"),
                    help="local cache for archived objects (content-addressed, re-hashed each run)")
    ap.add_argument("--build-cache", default=None, help="optional pickle of the feature build")
    ap.add_argument("--out", default=str(RESULTS))
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    prov = provenance()
    log(f"registration {prov['registration_commit'][:12]} ({prov['registration_committed']}) "
        f"-> freeze {prov['workbook_freeze_commit'][:12]} -> code {prov['code_commit'][:12]}")
    if not prov["registration_is_ancestor_of_code"]:
        raise SystemExit("ABORT: the registration commit is not an ancestor of HEAD")
    if not prov["registration_is_ancestor_of_origin_main"]:
        raise SystemExit("ABORT: the registration commit is not in pushed history "
                         "(BUILD-PROTOCOL §2.7) — a local-only hash is not a provenance receipt")

    if a.build_cache and os.path.exists(a.build_cache):
        log(f"loading feature build cache {a.build_cache}")
        with open(a.build_cache, "rb") as fh:
            d, asm = pickle.load(fh)
    else:
        d = build(a.cache)
        asm = assemble(d)
        if a.build_cache:
            with open(a.build_cache, "wb") as fh:
                pickle.dump((d, asm), fh, protocol=5)
            log(f"cached feature build -> {a.build_cache}")

    import numpy as np
    ent = np.array(asm["entity"], dtype=np.int32)
    tt = np.array(asm["t"], dtype=np.int32)
    X = np.array(asm["X"], dtype=np.float64)
    ph = np.array(asm["prior_harm"], dtype=np.float64)
    H = S.HORIZON_WEEKS
    gt = d["gt"]
    keep = set(asm["cells"])

    # ---- labels: harm survey EVENTS at scored facilities, as (entity, event_week).
    # DEDUPED to distinct (entity, week): two surveys of the same facility in one week are one
    # cell-week event, and leaving the duplicate in would inflate the event-recall denominator.
    # This is the W-006 correction (74,636 rows -> 21,093 events) applied before the first run.
    def to_cellweeks(events):
        return sorted({(asm["ent_ix"][p], S.week(dt)) for (p, dt) in events
                       if p in keep and S.LABEL_WINDOW_START <= dt <= S.LABEL_WINDOW_END})

    raw_harm = [e for e in gt["harm_events"]
                if e[0] in keep and S.LABEL_WINDOW_START <= e[1] <= S.LABEL_WINDOW_END]
    labels = to_cellweeks(gt["harm_events"])
    ij_labels = to_cellweeks(gt["ij_events"])
    all_labels = to_cellweeks(gt["all_events"])
    log(f"labels in window: {len(raw_harm):,} harm survey events collapse to {len(labels):,} "
        f"distinct (facility, week) events ({len(ij_labels):,} IJ) at {len(keep):,} scored "
        f"facilities; {len(all_labels):,} cited-survey cell-weeks of any severity")

    train_end, test_start = asm["train_w"][1], asm["test_w"][0]
    test_last = asm["test_w"][1]
    # An event is counted for the event-level metrics only if some cell in its split can actually
    # reach it. The furthest a test cell's horizon reaches is `test_last + H`; the label window
    # itself ends two days later, and counting events in that extra week would have booked ~0.7%
    # of held-out harm events as automatic misses that no threshold could ever have caught.
    tr_label_window = (asm["train_w"][0] + 1, train_end + H)
    te_label_window = (test_start + 1, test_last + H)
    train_mask = tt <= train_end
    test_mask = tt >= test_start
    log(f"splits: train weeks <= {train_end} ({S.week_start(train_end)}) = "
        f"{int(train_mask.sum()):,} cell-weeks; test >= {test_start} "
        f"({S.week_start(test_start)}) = {int(test_mask.sum()):,}")

    y = np.array([r["y"] for r in harness.label_cells(
        list(zip(ent.tolist(), tt.tolist(), [0.0] * len(ent))), labels, H)], dtype=np.float64)
    log(f"positives: {int(y.sum()):,} of {len(y):,} cell-weeks (base rate {y.mean():.6f})")

    # ---- the signature: logistic regression, standardized and fit on TRAIN ONLY
    Xtr, ytr = X[train_mask], y[train_mask]
    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    coef, intercept = fit_logreg((Xtr - mu) / sd, ytr)
    score = 1.0 / (1.0 + np.exp(-(((X - mu) / sd) @ coef + intercept)))
    model = {
        "kind": "logistic regression (full-batch GD, 2000 epochs, lr 0.5, zero init, "
                "base-rate intercept)",
        "features": list(S.FEATURES),
        "standardization": {"mean": mu.tolist(), "std": sd.tolist()},
        "coefficients": dict(zip(S.FEATURES, coef.tolist())),
        "intercept": float(intercept),
        "train_rows": int(train_mask.sum()), "train_positives": int(ytr.sum()),
        "train_logloss": logloss((Xtr - mu) / sd, ytr, coef, intercept),
        "train_grad_norm": grad_norm((Xtr - mu) / sd, ytr, coef, intercept),
    }
    log("coefficients " + ", ".join(f"{k}={v:+.3f}" for k, v in model["coefficients"].items())
        + f", intercept={intercept:+.3f}")

    # ---- the two pre-registered dumb baselines (registration §6)
    level_only = -X[:, S.FEATURES.index("hprd_total")]      # lower staffing = higher risk
    prior_harm_only = ph

    def obs(sc):
        return list(zip(ent.tolist(), tt.tolist(), sc.tolist()))

    kw = dict(labels=labels, horizon=H, train_end=train_end, bars=S.BARS,
              test_start=test_start, train_label_window=tr_label_window,
              test_label_window=te_label_window)

    log("scoring the two dumb baselines to decide which one the bar is set against (§6)")
    res_prior = harness.evaluate(signal_obs=obs(prior_harm_only), baseline_obs=obs(level_only), **kw)
    res_level = harness.evaluate(signal_obs=obs(level_only), baseline_obs=obs(prior_harm_only), **kw)
    auc_prior = res_prior["metrics"]["pr_auc"]
    auc_level = res_level["metrics"]["pr_auc"]
    stronger = "prior_harm_rate" if auc_prior >= auc_level else "level_only"
    baseline_obs = obs(prior_harm_only if stronger == "prior_harm_rate" else level_only)
    log(f"  prior-harm PR-AUC {auc_prior:.4f} vs level-only {auc_level:.4f} "
        f"-> graded against {stronger}")

    log("evaluating the signature (the graded comparison, §7)")
    res = harness.evaluate(signal_obs=obs(score), baseline_obs=baseline_obs, **kw)

    # ---- the pre-committed lead-time degeneracy rule (registration §7)
    leads = res["metrics"]["lead_times_days"]
    at_edge = sum(1 for v in leads if v >= S.LEAD_EDGE_DAYS)
    edge_share = (at_edge / len(leads)) if leads else 0.0
    degenerate = bool(leads) and edge_share >= S.LEAD_DEGENERACY_SHARE
    if degenerate:
        res["pass_detail"]["lead_ok"] = False
        res["pass"] = bool(all(res["pass_detail"].values()))
    res["pass_detail"]["lead_degenerate"] = degenerate
    log(f"lead-time: n={len(leads):,} median="
        f"{statistics.median(leads) if leads else None} at-edge={at_edge:,} "
        f"({edge_share:.1%}) -> degenerate={degenerate}")

    # ---- reported but NOT graded (registration §8)
    log("evaluating the reported-not-graded variants (§8)")
    res_ij = harness.evaluate(signal_obs=obs(score), baseline_obs=baseline_obs,
                              **{**kw, "labels": ij_labels,
                                 "train_label_window": tr_label_window,
                                 "test_label_window": te_label_window})
    surveyed = _survey_conditional_mask(ent, tt, all_labels, H)
    res_cond = harness.evaluate(signal_obs=[o for o, m in zip(obs(score), surveyed) if m],
                                baseline_obs=[o for o, m in zip(baseline_obs, surveyed) if m], **kw)
    keep_rename = np.array([asm["cells"][e] not in d["renamed"] for e in ent.tolist()])
    res_rename = harness.evaluate(
        signal_obs=[o for o, m in zip(obs(score), keep_rename) if m],
        baseline_obs=[o for o, m in zip(baseline_obs, keep_rename) if m], **kw)
    log(f"  IJ-only pass={res_ij['pass']} | survey-conditional "
        f"({int(surveyed.sum()):,} cell-weeks) pass={res_cond['pass']} | "
        f"name-change sensitivity ({int(keep_rename.sum()):,}) pass={res_rename['pass']}")

    # ---- diagnostics the hostile review will ask for anyway
    te_obs = [o for o in obs(score) if o[1] >= test_start]
    te_labels = [(e, et) for (e, et) in labels
                 if te_label_window[0] <= et <= te_label_window[1]]
    floor = float(score.min()) - 1.0
    ceiling = harness.event_recall_at(te_obs, te_labels, floor, H)
    thr = res["operating_threshold"]

    # The harness flags any lead <= 0 as possible leakage. Here a zero lead means only that the
    # crossing WEEK equals the event week — it cannot mean the signal saw the event, because the
    # score at week w is built from a PBJ quarter that ended at least PBJ_AVAILABILITY_LAG_DAYS
    # before w starts. Measure that gap directly over every scored test cell-week that carries a
    # harm event in its own week, so the flag is answered with a number instead of an argument.
    ev_weeks = {}
    for e, et in te_labels:
        ev_weeks.setdefault(e, set()).add(et)
    min_gap = None
    same_week = 0
    for e, w, _s in te_obs:
        if w in ev_weeks.get(e, ()):
            same_week += 1
            q = asm["usable_q"][w]
            gap = (S.week_start(w) - F.quarter_end(q)).days
            min_gap = gap if min_gap is None or gap < min_gap else min_gap
    diagnostics = {
        # The hard ceiling on event-recall: an event at a facility with NO scored cell-week in its
        # 26-week pre-window cannot be flagged at any threshold. A property of the corpus and the
        # registration's unit of analysis, not of the signature.
        "event_recall_ceiling": ceiling,
        "test_events_evaluated": len(te_labels),
        "operating_threshold": float(thr),
        "operating_point_is_degenerate": bool(thr <= float(score[test_mask].min())),
        "test_cell_weeks_flagged": int((score[test_mask] >= thr).sum()),
        "test_flag_rate": float((score[test_mask] >= thr).mean()),
        "lead_at_edge": at_edge, "lead_edge_share": edge_share, "lead_degenerate": degenerate,
        # Answers the harness's lead<=0 leakage flag with arithmetic: the smallest number of days
        # between the END of the staffing quarter a cell was scored from and the cell's own week,
        # over every test cell-week that shares its week with a harm survey. >= 135 makes leakage
        # impossible by construction; a zero LEAD is then a week-bucket artefact, not a peek.
        "same_week_cell_weeks": same_week,
        "min_days_feature_quarter_end_to_same_week_event": min_gap,
        "zero_census_days_excluded": d["zero_census_days"],
        "short_rows_skipped": d["short_rows"],
        "ccns_state_moved": len(d["moved"]), "ccns_renamed": len(d["renamed"]),
        "publication_lag_check": d["lag_rows"],
    }
    diagnostics.update(_full_grid_base_rate(labels, len(asm["cells"]),
                                            test_start, asm["test_w"][1], H))
    log(f"event-recall ceiling {ceiling:.4f} over {len(te_labels):,} held-out harm events; "
        f"flag rate {diagnostics['test_flag_rate']:.4f}")

    # ---- write the results bundle
    card = harness.scorecard(
        index="hospital-care", version="v1",
        registration_commit=prov["registration_commit"],
        generated=_dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        data_vintages={"deficiencies": DEFICIENCIES, "pbj": PBJ_VINTAGES}, horizon=H, result=res)
    card["provenance"] = prov
    card["universe"] = {
        "scored_facilities": len(asm["cells"]),
        "scored_cell_weeks": int(len(ent)),
        "train_cell_weeks": int(train_mask.sum()),
        "test_cell_weeks": int(test_mask.sum()),
        "gap_weeks_never_generated": asm["gap_weeks"],
        "deficiency_rows": gt["rows"],
        "distinct_survey_events": len(gt["all_events"]),
        "harm_events_total": len(gt["harm_events"]),
        "harm_events_in_label_window_at_scored_facilities": len(labels),
        "ij_events_in_label_window_at_scored_facilities": len(ij_labels),
        "test_events_evaluated": int(res["metrics"]["n_test_labels"]),
        "exclusions": asm["drops"],
    }
    card["comparators"] = {
        "prior_harm_rate": _slim(res_prior), "level_only": _slim(res_level),
        "graded_against": stronger,
        "immediate_jeopardy_only": _slim(res_ij),
        "survey_conditional": _slim(res_cond),
        "name_change_sensitivity": _slim(res_rename),
    }
    card["model"] = model
    card["diagnostics"] = diagnostics
    harness.write_scorecard(out / "scorecard.json", card)

    _write_curve(out / "pr_curve.csv", res["curve"])
    _write_rows(out / "calibration.csv", ["bin", "n", "predicted", "observed"],
                [[i, c["n"], c["predicted"], c["observed"]]
                 for i, c in enumerate(res["calibration"])])
    _write_rows(out / "lead_times.csv", ["lead_days"], [[v] for v in sorted(leads)])
    n_cases = _cases(out / "cases.csv", asm, d, ent, tt, X, score, ph, thr,
                     test_start, te_label_window, labels)
    with open(out / "metrics.json", "w", encoding="utf-8") as fh:
        json.dump({"signature": _slim(res), "prior_harm_rate": _slim(res_prior),
                   "level_only": _slim(res_level), "immediate_jeopardy_only": _slim(res_ij),
                   "survey_conditional": _slim(res_cond),
                   "name_change_sensitivity": _slim(res_rename),
                   "lead_time_distribution": _dist(leads)}, fh, indent=2)

    m = res["metrics"]
    log(f"RESULT pass={res['pass']}  pr_auc={m['pr_auc']:.4f} vs {stronger} "
        f"{m['baseline_pr_auc']:.4f} (bar +{S.BARS['auc_margin']}) | "
        f"precision={m['precision']:.4f} (bar {S.BARS['precision']}) | "
        f"event_recall={m['event_recall']:.4f} (bar {S.BARS['recall']}) | "
        f"median_lead={m['median_lead_days']}d (bar {S.BARS['median_lead_days']}, "
        f"degenerate={degenerate}) | base_rate={m['base_rate']:.6f}")
    log(f"pass_detail {res['pass_detail']}")
    if res["leakage_flags"]:
        log("LEAKAGE FLAGS: " + " | ".join(res["leakage_flags"]))
    log(f"wrote {out} ({n_cases:,} per-case receipts)")
    return 0


def _survey_conditional_mask(ent, tt, all_labels, horizon):
    """§8: the universe restricted to cells with a cited survey of ANY severity in the horizon.
    Controls the surveillance confound; conditions the universe on a post-t fact, which is why it
    is reported and never graded."""
    import numpy as np
    by = {}
    for e, et in all_labels:
        by.setdefault(e, []).append(et)
    for v in by.values():
        v.sort()
    import bisect
    out = np.zeros(len(ent), dtype=bool)
    e_l, t_l = ent.tolist(), tt.tolist()
    for i in range(len(e_l)):
        v = by.get(e_l[i])
        if not v:
            continue
        j = bisect.bisect_right(v, t_l[i])
        if j < len(v) and v[j] <= t_l[i] + horizon:
            out[i] = True
    return out


def _full_grid_base_rate(labels, n_cells, lo, hi, horizon):
    """Base-rate honesty (SPEC-08 §5). The reported precision is computed over the SCORED universe,
    which excludes cells dropped by §3/§5. This states the prevalence over the whole
    (facility x week) grid in the test window under the same §3 positivity rule, so the reader can
    see which way the exclusions cut."""
    per_cell = {}
    for e, et in labels:
        if et < lo or et - horizon > hi:
            continue
        a, b = max(lo, et - horizon), min(hi, et - 1)
        if a <= b:
            per_cell.setdefault(e, []).append((a, b))
    pos = 0
    for spans in per_cell.values():
        spans.sort()
        cur_a, cur_b = spans[0]
        for a, b in spans[1:]:
            if a > cur_b + 1:
                pos += cur_b - cur_a + 1
                cur_a, cur_b = a, b
            else:
                cur_b = max(cur_b, b)
        pos += cur_b - cur_a + 1
    grid = n_cells * (hi - lo + 1)
    return {"full_grid_test_cell_weeks": grid, "full_grid_test_positives": pos,
            "full_grid_test_base_rate": (pos / grid) if grid else 0.0}


def _slim(res):
    m = {k: v for k, v in res["metrics"].items() if k != "lead_times_days"}
    return {"operating_threshold": res["operating_threshold"], "metrics": m,
            "pass": res["pass"], "pass_detail": res["pass_detail"],
            "leakage_flags": res["leakage_flags"]}


def _dist(leads):
    if not leads:
        return {}
    s = sorted(leads)
    def q(f):
        return s[min(len(s) - 1, int(f * (len(s) - 1)))]
    return {"n": len(s), "min": s[0], "p10": q(.1), "p25": q(.25), "median": q(.5),
            "p75": q(.75), "p90": q(.9), "max": s[-1], "mean": sum(s) / len(s),
            "share_nonpositive": sum(1 for v in s if v <= 0) / len(s),
            "share_at_horizon_edge": sum(1 for v in s if v >= S.LEAD_EDGE_DAYS) / len(s)}


def _write_rows(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def _write_curve(path, curve, cap=2000):
    """The full curve is computed; the published CSV is thinned to <=`cap` evenly spaced points.
    Thinning is disclosed rather than silent."""
    step = max(1, len(curve) // cap)
    rows = [[t, p, r] for i, (t, p, r) in enumerate(curve) if i % step == 0]
    _write_rows(path, ["threshold", "precision", "recall"], rows)
    return len(rows)


def _cases(path, asm, d, ent, tt, X, score, ph, thr, test_start, label_window, labels):
    """Per-case receipts (SPEC-08 §3): every held-out harm event, whether the signature flagged it,
    when it first crossed, the features at that crossing, and matched controls (registration §6:
    same state and census band, that did not cross).

    NOTE: this file names facilities only by CCN and county. The naming gate (covenant 2) governs
    what may be PUBLISHED as a claim; the evidence bundle behind a scorecard must be checkable.
    """
    import bisect
    lo, hi = label_window
    cells = asm["cells"]
    geo = d["geo"]
    i_census = S.FEATURES.index("census")
    by_ent_obs, by_ent_cross = {}, {}
    e_l, t_l, s_l = ent.tolist(), tt.tolist(), score.tolist()
    for i in range(len(e_l)):
        if t_l[i] < test_start:
            continue
        by_ent_obs.setdefault(e_l[i], []).append(t_l[i])
        if s_l[i] >= thr:
            by_ent_cross.setdefault(e_l[i], []).append((t_l[i], i))
    for v in by_ent_obs.values():
        v.sort()
    for v in by_ent_cross.values():
        v.sort()

    band = {}
    for i in range(len(e_l)):
        if t_l[i] >= test_start:
            e = e_l[i]
            if e not in band:
                st = geo.get(cells[e], ("", "", "", ""))[0]
                band[e] = (st, int(X[i][i_census] // 25))

    by_band = {}
    for e, k in band.items():
        by_band.setdefault(k, []).append(e)

    def crossed_in(e, a, b):
        v = by_ent_cross.get(e)
        if not v:
            return False
        i = bisect.bisect_left(v, (a, -1))
        return i < len(v) and v[i][0] <= b

    def observed_in(e, a, b):
        v = by_ent_obs.get(e)
        if not v:
            return False
        i = bisect.bisect_left(v, a)
        return i < len(v) and v[i] <= b

    rows = []
    for e, ev_t in sorted(set(labels)):
        if not (lo <= ev_t <= hi):
            continue
        ccn = cells[e]
        st, county, fips, name = geo.get(ccn, ("", "", "", ""))
        a, b = ev_t - S.HORIZON_WEEKS + 1, ev_t
        v = by_ent_cross.get(e, [])
        i = bisect.bisect_left(v, (a, -1))
        first = v[i] if (i < len(v) and v[i][0] <= b) else None
        controls = ctrl_clean = 0
        for c in by_band.get(band.get(e), ()):
            if c == e or not observed_in(c, a, b):
                continue
            controls += 1
            ctrl_clean += 0 if crossed_in(c, a, b) else 1
        r = [ccn, st, county, fips, str(S.week_start(ev_t)), 1 if first else 0]
        if first:
            t_cross, idx = first
            r += [str(S.week_start(t_cross)), (ev_t - t_cross) * 7, round(s_l[idx], 6),
                  round(float(ph[idx]), 6)]
            r += [round(float(X[idx][j]), 6) for j in range(len(S.FEATURES))]
        else:
            r += ["", "", "", ""] + [""] * len(S.FEATURES)
        r += [controls, ctrl_clean]
        rows.append(r)
    _write_rows(path, ["ccn", "state", "county", "county_fips", "harm_survey_week", "flagged",
                       "first_crossing_week", "lead_days", "score_at_crossing",
                       "prior_harm_rate_at_crossing",
                       *[f"{n}_at_crossing" for n in S.FEATURES],
                       "matched_controls", "matched_controls_not_flagged"], rows)
    return len(rows)


if __name__ == "__main__":
    sys.exit(main())
