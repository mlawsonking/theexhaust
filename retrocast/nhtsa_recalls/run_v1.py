"""Run the pre-registered NHTSA Shadow Recalls retrocast (v1) and emit `results/v1/`.

    python -m retrocast.nhtsa_recalls.run_v1 --complaints <zip> --recalls <zip>

Everything this script may decide was frozen before it was written: the signal is
PRE-REGISTRATION-v1 §3, the labels §4, the splits §5, the dumb baselines §6, the publish bars §7,
and the component crosswalk + hazard lexicon are the workbook freeze (commit predates this file).
The script's only job is to execute that and write down what happened — including a failure.

Inputs are the ARCHIVED vintages, pinned by sha256 below and pulled from R2 through
`archive.theexhaust.org`. If the bytes do not hash to the pin, the run aborts: a retrocast against
an unpinned file is not a retrocast. Nothing here touches a live NHTSA endpoint, and no LLM is
involved at any point (the signal must be rerunnable by a critic with no API key).

numpy is used for the logistic fit only (see retrocast/requirements.txt); everything else is
stdlib, and the fit's exact arithmetic is mirrored by a pure-Python reference in the tests.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as _dt
import hashlib
import json
import math
import os
import pathlib
import pickle
import subprocess
import sys
import time

from retrocast import harness
from retrocast.nhtsa_recalls import features as F
from retrocast.nhtsa_recalls import lexicon as L

REPO = pathlib.Path(__file__).resolve().parents[2]
RESULTS = REPO / "retrocast" / "nhtsa-recalls" / "results" / "v1"
REGISTRATION = "retrocast/nhtsa-recalls/PRE-REGISTRATION-v1.md"
FREEZE = "retrocast/nhtsa_recalls/lexicon.py"
ARCHIVE_BASE = "https://archive.theexhaust.org/"

# The retrocast-of-record. Both sides come from the same 2026-07-28 12:20 UTC collection cycle.
VINTAGES = {
    "complaints": {
        "r2_key": "raw/nhtsa-complaints/2026/07/28/1220-73acbdca6b6f.zip",
        "sha256": "73acbdca6b6fd8e9f4066d9e8e1c4b5afea2b656a17cc82624cba284d0bd344a",
        "source_url": "https://static.nhtsa.gov/odi/ffdd/cmpl/FLAT_CMPL.zip",
        "collected_at": "2026-07-28T12:21:41Z", "rows": 2229384,
    },
    "recalls": {
        "r2_key": "raw/nhtsa-recalls/2026/07/28/1220-efab48ed2da2.zip",
        "sha256": "efab48ed2da29531928c86d9391c7fabddea28479549025e1a166e516a98c444",
        "source_url": "https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip",
        "collected_at": "2026-07-28T12:20:58Z", "rows": 243126,
    },
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
        "dirty": bool(_git("status", "--porcelain")),
    }
    for label, c in (("registration", reg), ("workbook freeze", frz)):
        anc = subprocess.run(["git", "merge-base", "--is-ancestor", c, head], cwd=REPO)
        out[f"{label.replace(' ', '_')}_is_ancestor_of_code"] = anc.returncode == 0
    return out


def verify(path, which):
    """Hash-pin the input. A mismatch aborts — an unpinned vintage is not the record."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    got, want = h.hexdigest(), VINTAGES[which]["sha256"]
    if got != want:
        raise SystemExit(f"ABORT: {which} vintage hash mismatch\n  want {want}\n  got  {got}\n"
                         f"  expected object: {ARCHIVE_BASE}{VINTAGES[which]['r2_key']}")
    log(f"{which}: sha256 verified against the manifest pin ({got[:12]})")


# ------------------------------------------------------------------------------------ labeling
def label_y(entity, t, labels, horizon):
    """y[i] = 1 iff an event for that entity falls in (t, t+H]. Same rule as
    harness.label_cells, computed here over flat arrays (millions of rows); the harness recomputes
    it independently for the reported metrics and the two are cross-checked before publishing."""
    ev = {}
    for e, et in labels:
        ev.setdefault(e, []).append(et)
    for v in ev.values():
        v.sort()
    y = bytearray(len(entity))
    for i in range(len(entity)):
        v = ev.get(entity[i])
        if not v:
            continue
        lo = bisect.bisect_right(v, t[i])
        if lo < len(v) and v[lo] <= t[i] + horizon:
            y[i] = 1
    return y


# ------------------------------------------------------------------------------ logistic model
def fit_logreg(X, y, *, epochs=2000, lr=0.5):
    """Deterministic full-batch gradient descent on mean log-loss. Zero-initialized weights and a
    base-rate intercept; no randomness, no early stopping, no held-out tuning — the coefficients
    are a function of the train split alone and are published so a critic can rerun them."""
    import numpy as np
    n, k = X.shape
    base = float(y.mean())
    w = np.zeros(k, dtype=np.float64)
    b = math.log(base / (1 - base)) if 0 < base < 1 else 0.0
    for _ in range(epochs):
        p = 1.0 / (1.0 + np.exp(-(X @ w + b)))
        g = p - y
        w -= lr * (X.T @ g) / n
        b -= lr * float(g.mean())
    return w, b


def logloss(X, y, w, b):
    import numpy as np
    z = X @ w + b
    return float(np.mean(np.logaddexp(0.0, z) - y * z))


# ------------------------------------------------------------------------------------ the run
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--complaints", required=True, help="archived FLAT_CMPL zip (hash-pinned)")
    ap.add_argument("--recalls", required=True, help="archived FLAT_RCL_POST_2010 zip (hash-pinned)")
    ap.add_argument("--cache", default=None, help="optional pickle cache for the feature build")
    ap.add_argument("--out", default=str(RESULTS))
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    prov = provenance()
    log(f"registration {prov['registration_commit'][:12]} ({prov['registration_committed']}) "
        f"-> freeze {prov['workbook_freeze_commit'][:12]} ({prov['workbook_freeze_committed']}) "
        f"-> code {prov['code_commit'][:12]}")
    if not prov["registration_is_ancestor_of_code"]:
        raise SystemExit("ABORT: the registration commit is not an ancestor of HEAD")

    verify(a.complaints, "complaints")
    verify(a.recalls, "recalls")

    if a.cache and os.path.exists(a.cache):
        log(f"loading feature cache {a.cache}")
        with open(a.cache, "rb") as fh:
            d = pickle.load(fh)
    else:
        d = F.build(a.complaints, a.recalls, progress=log)
        if a.cache:
            with open(a.cache, "wb") as fh:
                pickle.dump(d, fh, protocol=5)
            log(f"cached feature build -> {a.cache}")

    import numpy as np
    ent = np.frombuffer(d["entity"], dtype=np.int32)
    tt = np.frombuffer(d["t"], dtype=np.int32)
    X = np.frombuffer(d["features"], dtype=np.float64).reshape(-1, F.NFEAT)
    labels, H = d["labels"], L.HORIZON_WEEKS
    w0, w1 = d["window"]
    log(f"{len(ent):,} scored cell-weeks over {len(d['cells']):,} cells; {len(labels):,} labels")

    # ---- splits (registration §5, with the horizon-spillover guard of §5d)
    train_end = F.week_of_date(L.TRAIN_HORIZON_END) - H
    test_start = F.week_of_date(L.TEST_START)
    train_mask = tt <= train_end
    test_mask = tt >= test_start
    gap = int(len(tt) - int(train_mask.sum()) - int(test_mask.sum()))
    tr_labels_window = (w0 + H, train_end)
    te_labels_window = (test_start + H, w1)
    log(f"weeks: window [{w0},{w1}] train<= {train_end} ({F.week_start(train_end)}) "
        f"test>= {test_start} ({F.week_start(test_start)}); {gap:,} straddling cell-weeks dropped")

    y = np.frombuffer(bytes(label_y(d["entity"], d["t"], labels, H)), dtype=np.uint8).astype(np.float64)
    log(f"positives: {int(y.sum()):,} of {len(y):,} cell-weeks (raw base rate {y.mean():.6f})")

    # ---- the signature: logistic regression, standardized and fit on TRAIN ONLY
    Xtr, ytr = X[train_mask], y[train_mask]
    mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    coef, intercept = fit_logreg((Xtr - mu) / sd, ytr)
    score = 1.0 / (1.0 + np.exp(-(((X - mu) / sd) @ coef + intercept)))
    model = {
        "kind": "logistic regression (full-batch GD, 2000 epochs, lr 0.5, zero init, "
                "base-rate intercept)",
        "features": list(F.FEATURE_NAMES),
        "standardization": {"mean": mu.tolist(), "std": sd.tolist()},
        "coefficients": dict(zip(F.FEATURE_NAMES, coef.tolist())),
        "intercept": float(intercept),
        "train_rows": int(train_mask.sum()), "train_positives": int(ytr.sum()),
        "train_logloss": logloss((Xtr - mu) / sd, ytr, coef, intercept),
        "interpretable_rule": dict(L.INTERPRETABLE_RULE),
    }
    log("coefficients " + ", ".join(f"{k}={v:+.3f}" for k, v in model["coefficients"].items())
        + f", intercept={intercept:+.3f}")

    # ---- the two pre-registered dumb baselines (registration §6) and the interpretable rule
    volume = X[:, 0]                                                     # (i) volume-only
    seas_rate = {}                                                       # (ii) seasonality-only
    cw = np.array([F.calendar_week(int(v)) for v in tt], dtype=np.int32)
    for wk in range(1, 54):
        m = train_mask & (cw == wk)
        seas_rate[wk] = float(ytr.mean()) if not m.any() else float(y[m].mean())
    seasonality = np.array([seas_rate[int(v)] for v in cw], dtype=np.float64)
    rule = ((X[:, 1] >= L.INTERPRETABLE_RULE["rate_ratio_min"]).astype(np.float64)
            + (X[:, 2] > L.INTERPRETABLE_RULE["accel_min"]).astype(np.float64)
            + (X[:, 3] >= L.INTERPRETABLE_RULE["severity_frac_min"]).astype(np.float64))

    def obs(sc):
        return list(zip(ent.tolist(), tt.tolist(), sc.tolist()))

    kw = dict(labels=labels, horizon=H, train_end=train_end, bars=L.BARS,
              test_start=test_start, train_label_window=tr_labels_window,
              test_label_window=te_labels_window)
    log("evaluating signature vs volume-only baseline (the graded comparison, §7)")
    res = harness.evaluate(signal_obs=obs(score), baseline_obs=obs(volume), **kw)
    log(f"  pass={res['pass']} {res['pass_detail']}")
    log("evaluating the interpretable rule and the seasonality-only baseline")
    res_rule = harness.evaluate(signal_obs=obs(rule), baseline_obs=obs(volume), **kw)
    res_seas = harness.evaluate(signal_obs=obs(seasonality), baseline_obs=obs(volume), **kw)
    res_vol = harness.evaluate(signal_obs=obs(volume), baseline_obs=obs(seasonality), **kw)

    # ---- independent cross-check of the labelling used for the fit vs the harness's own
    chk = harness.label_cells(list(zip(ent[:200000].tolist(), tt[:200000].tolist(),
                                       score[:200000].tolist())), labels, H)
    mism = int(sum(1 for i, r in enumerate(chk) if r["y"] != int(y[i])))
    log(f"label cross-check on 200k rows: {mism} mismatches vs the harness")

    # ---- write the results bundle
    thr = res["operating_threshold"]
    card = harness.scorecard(index="nhtsa-recalls", version="v1",
                             registration_commit=prov["registration_commit"],
                             generated=_dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                             data_vintages=VINTAGES, horizon=H, result=res)
    card["provenance"] = prov
    card["label_crosscheck_mismatches"] = mism
    card["universe"] = {
        "cells_with_complaints": d["n_cells_seen"], "scored_cells": len(d["cells"]),
        "scored_cell_weeks": int(len(ent)), "train_cell_weeks": int(train_mask.sum()),
        "test_cell_weeks": int(test_mask.sum()), "straddle_dropped_cell_weeks": gap,
        "recall_campaign_rows_in_window": d["n_events_seen"],
        "labels_joined_to_a_complaint_bearing_cell": len(labels),
        "test_events_evaluated": int(res["metrics"]["n_test_labels"]),
        "unscorable_zero_trailing_cell_weeks": _unscorable(d, len(ent)),
    }
    card["comparators"] = {
        "volume_only": _slim(res_vol), "seasonality_only": _slim(res_seas),
        "interpretable_rule": _slim(res_rule),
    }
    card["model"] = model
    harness.write_scorecard(out / "scorecard.json", card)

    _write_curve(out / "pr_curve.csv", res["curve"])
    _write_rows(out / "calibration.csv", ["bin", "n", "predicted", "observed"],
                [[i, c["n"], c["predicted"], c["observed"]] for i, c in enumerate(res["calibration"])])
    leads = res["metrics"]["lead_times_days"]
    _write_rows(out / "lead_times.csv", ["lead_days"], [[v] for v in sorted(leads)])
    _cases(out / "cases.csv", d, ent, tt, X, score, thr, test_start, w1, te_labels_window)
    with open(out / "metrics.json", "w", encoding="utf-8") as fh:
        json.dump({"signature": _slim(res), "volume_only": _slim(res_vol),
                   "seasonality_only": _slim(res_seas), "interpretable_rule": _slim(res_rule),
                   "lead_time_distribution": _dist(leads)}, fh, indent=2)

    m = res["metrics"]
    log(f"RESULT pass={res['pass']}  pr_auc={m['pr_auc']:.4f} vs volume {m['baseline_pr_auc']:.4f} "
        f"| precision={m['precision']:.4f} (bar .30) | event_recall={m['event_recall']:.4f} "
        f"(bar .50) | median_lead={m['median_lead_days']}d (bar 60) | base_rate={m['base_rate']:.6f}")
    if res["leakage_flags"]:
        log("LEAKAGE FLAGS: " + " | ".join(res["leakage_flags"]))
    log(f"wrote {out}")
    return 0


def _unscorable(d, scored):
    """Cell-weeks in the window with zero trailing complaints — excluded by construction
    (WORKBOOK §4.2). Reported so the base rate can be restated over the full grid."""
    w0, w1 = d["window"]
    return len(d["cells"]) * (w1 - w0 + 1) - scored


def _slim(res):
    m = {k: v for k, v in res["metrics"].items() if k != "lead_times_days"}
    return {"operating_threshold": res["operating_threshold"], "metrics": m,
            "pass": res["pass"], "pass_detail": res["pass_detail"],
            "leakage_flags": res["leakage_flags"]}


def _dist(leads):
    if not leads:
        return {}
    s = sorted(leads)
    q = lambda f: s[min(len(s) - 1, int(f * (len(s) - 1)))]
    return {"n": len(s), "min": s[0], "p10": q(.1), "p25": q(.25), "median": q(.5),
            "p75": q(.75), "p90": q(.9), "max": s[-1],
            "mean": sum(s) / len(s), "share_nonpositive": sum(1 for v in s if v <= 0) / len(s)}


def _write_rows(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def _write_curve(path, curve, cap=2000):
    """The full curve is computed; the published CSV is thinned to <=`cap` evenly spaced points
    (a curve with one point per distinct score is millions of rows). Thinning is disclosed."""
    step = max(1, len(curve) // cap)
    rows = [[t, p, r] for i, (t, p, r) in enumerate(curve) if i % step == 0]
    _write_rows(path, ["threshold", "precision", "recall"], rows)
    return len(rows)


def _cases(path, d, ent, tt, X, score, thr, test_start, w1, label_window):
    """Per-case receipts (SPEC-08 §3): every recall campaign in the held-out window, whether the
    signature flagged it, when it first crossed, and the features at that crossing — plus matched
    controls (registration §6: same make, model-year band +/-1, that did not cross)."""
    lo, hi = label_window
    cells = d["cells"]
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
    # index cells by (make, year) for the control match
    by_make_year = {}
    for e, (mk, mdl, yr, comp) in cells.items():
        if yr.isdigit():
            by_make_year.setdefault((mk, int(yr)), []).append(e)

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
    for (e, ev_t), camps in sorted(d["campaigns"].items()):
        if not (lo <= ev_t <= hi):
            continue
        mk, mdl, yr, comp = cells[e]
        a, b = ev_t - L.HORIZON_WEEKS + 1, ev_t
        v = by_ent_cross.get(e, [])
        i = bisect.bisect_left(v, (a, -1))
        first = v[i] if (i < len(v) and v[i][0] <= b) else None
        controls = ctrl_clean = 0
        if yr.isdigit():
            for dy in (-1, 0, 1):
                for c in by_make_year.get((mk, int(yr) + dy), ()):
                    if c == e or not observed_in(c, a, b):
                        continue
                    controls += 1
                    ctrl_clean += 0 if crossed_in(c, a, b) else 1
        r = [mk, mdl, yr, comp, str(F.week_start(ev_t)), ";".join(sorted(set(camps))),
             1 if first else 0]
        if first:
            t_cross, idx = first
            r += [str(F.week_start(t_cross)), (ev_t - t_cross) * 7, round(s_l[idx], 6)]
            r += [round(float(X[idx][j]), 6) for j in range(F.NFEAT)]
        else:
            r += ["", "", ""] + [""] * F.NFEAT
        r += [controls, ctrl_clean]
        rows.append(r)
    _write_rows(path, ["make", "model", "model_year", "component_group", "recall_report_week",
                       "campaign_numbers", "flagged", "first_crossing_week", "lead_days",
                       "score_at_crossing", *[f"{n}_at_crossing" for n in F.FEATURE_NAMES],
                       "matched_controls", "matched_controls_not_flagged"], rows)
    return len(rows)


if __name__ == "__main__":
    sys.exit(main())
