"""Retrocast harness (SPEC-08) — the generic credibility engine.

One falsification protocol, reused by every index. Given a scored signal and a named labels set,
it computes the full precision/recall curve, the lead-time distribution, calibration, and a
scorecard graded against PRE-REGISTERED bars — plus a mandatory dumb-baseline comparison and a
leakage guard. Data-shape-agnostic: an index feeds (entity, t, score) observations and
(entity, event_t) labels; t is an integer period index (e.g., week number).

Doctrine enforced here: never predict, only measure · the pre-registered bars decide publish ·
failing is publishable (autopsy) · the signature must beat a naive baseline · no feature may
peek past the moment of measurement (the leakage guard makes that auditable).
Stdlib-only for portability (R1 Actions + R2 box).
"""
from __future__ import annotations

import json
import math
import statistics


# --------------------------------------------------------------------- labeling
def label_cells(observations, labels, horizon):
    """observations: iterable of (entity, t:int, score:float). labels: iterable of (entity, event_t:int).
    A cell (entity, t) is POSITIVE iff an event for that entity falls in (t, t+horizon]
    (strictly future — no peeking at t's own or past events). Returns list of dicts."""
    ev = {}
    for e, et in labels:
        ev.setdefault(e, []).append(et)
    out = []
    for e, t, s in observations:
        pos = any(t < et <= t + horizon for et in ev.get(e, []))
        out.append({"entity": e, "t": t, "score": float(s), "y": 1 if pos else 0})
    return out


# --------------------------------------------------------------------- PR curve
def pr_curve(scored):
    """scored: list of {'score','y'}. Returns (curve, base_rate) where curve is a list of
    (threshold, precision, recall) at every distinct score threshold (full curve, not one point)."""
    items = sorted(scored, key=lambda r: r["score"], reverse=True)
    P = sum(r["y"] for r in items)
    n = len(items)
    curve = []
    tp = fp = 0
    prev = None
    for r in items:
        if prev is not None and r["score"] != prev:
            curve.append((prev, tp / (tp + fp) if (tp + fp) else 1.0, tp / P if P else 0.0))
        tp += r["y"]
        fp += 1 - r["y"]
        prev = r["score"]
    if prev is not None:
        curve.append((prev, tp / (tp + fp) if (tp + fp) else 1.0, tp / P if P else 0.0))
    return curve, (P / n if n else 0.0)


def pr_auc(curve):
    """Area under the PR curve, trapezoid on ascending recall."""
    pts = sorted((rec, prec) for (_t, prec, rec) in curve)
    if not pts:
        return 0.0
    area, prev_r, prev_p = 0.0, 0.0, pts[0][1]
    for r, p in pts:
        area += (r - prev_r) * (p + prev_p) / 2.0
        prev_r, prev_p = r, p
    return area


def operating_threshold(curve, target_recall):
    """Highest score threshold that still achieves recall >= target_recall (train-chosen op point).
    Returns (threshold, precision, recall). If the target is never reached, the max-recall point."""
    best = None
    for t, p, r in sorted(curve, key=lambda x: x[0], reverse=True):  # high thr -> low recall
        if r >= target_recall:
            return (t, p, r)
        best = (t, p, r)
    return best


def precision_recall_at(scored, threshold):
    tp = sum(1 for r in scored if r["score"] >= threshold and r["y"] == 1)
    fp = sum(1 for r in scored if r["score"] >= threshold and r["y"] == 0)
    fn = sum(1 for r in scored if r["score"] < threshold and r["y"] == 1)
    prec = tp / (tp + fp) if (tp + fp) else 1.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    return {"threshold": threshold, "precision": prec, "recall": rec, "tp": tp, "fp": fp, "fn": fn}


def wilson_ci(k, n, z=1.96):
    """Wilson score interval for a proportion k/n (reported CI, base-rate honest)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


# --------------------------------------------------------------------- lead time & calibration
def lead_time_days(observations, labels, threshold, horizon, days_per_t=7):
    """For each labeled event, the lead of the FIRST pre-event threshold crossing within
    (event-horizon, event]. lead = (event_t - first_cross) * days_per_t. A crossing at/after the
    event yields lead <= 0 — the leakage tell. Returns (leads, n_flagged_nonpositive)."""
    by_ent = {}
    for e, t, s in observations:
        by_ent.setdefault(e, []).append((t, s))
    leads, nonpos = [], 0
    for e, et in labels:
        crosses = sorted(t for (t, s) in by_ent.get(e, []) if s >= threshold and et - horizon < t <= et)
        if crosses:
            lead = (et - crosses[0]) * days_per_t
            leads.append(lead)
            nonpos += 1 if lead <= 0 else 0
    return leads, nonpos


def event_recall_at(observations, labels, threshold, horizon):
    """Fraction of EVENTS led — an event is 'recalled' if the signal crosses threshold at least
    once in its pre-event window. This is the meaningful recall for a lead-time retrocast (a
    single 8-week-lead signal can never achieve high CELL recall over a 26-week horizon)."""
    leads, _ = lead_time_days(observations, labels, threshold, horizon)
    return (len(leads) / len(labels)) if labels else 0.0


def operating_threshold_event_naive(observations, labels, horizon, target_event_recall):
    """Reference implementation: walk every distinct score from the top and stop at the first
    that still reaches the target event-recall. O(distinct_scores x N) — correct but unusable at
    corpus scale (millions of cell-weeks). Kept as the oracle the fast path is tested against."""
    scores = sorted({s for (_e, _t, s) in observations}, reverse=True)
    best = scores[-1] if scores else 0.0
    for thr in scores:
        if event_recall_at(observations, labels, thr, horizon) >= target_event_recall:
            return thr
        best = thr
    return best


def operating_threshold_event(observations, labels, horizon, target_event_recall):
    """Highest score threshold (on the TRAIN data) still achieving the target event-recall.

    Exactly equivalent to `operating_threshold_event_naive`, in O(N log N): event-recall at a
    threshold is just the share of events whose pre-window MAXIMUM score clears it, so the answer
    is the k-th largest of those maxima. Equivalence is asserted by a randomized test."""
    by_ent = {}
    for e, t, s in observations:
        by_ent.setdefault(e, []).append((t, s))
    maxima = []
    for e, et in labels:
        window = [s for (t, s) in by_ent.get(e, []) if et - horizon < t <= et]
        if window:
            maxima.append(max(window))
    n = len(labels)
    lowest = min((s for (_e, _t, s) in observations), default=0.0)
    highest = max((s for (_e, _t, s) in observations), default=0.0)
    if not n:                       # no events: recall is 0 everywhere, mirroring the reference
        return highest if target_event_recall <= 0.0 else lowest
    maxima.sort(reverse=True)
    for k in range(0, len(maxima) + 1):          # k-th largest -> event-recall >= k/n
        if k / n >= target_event_recall:
            return highest if k == 0 else maxima[k - 1]
    return lowest                                # target unreachable at any observed score


def calibration_deciles(scored, bins=10):
    """Predicted (mean score) vs observed (mean y) per score decile — miscalibration is disclosed."""
    items = sorted(scored, key=lambda r: r["score"])
    if not items:
        return []
    out, size = [], max(1, len(items) // bins)
    for i in range(0, len(items), size):
        chunk = items[i:i + size]
        out.append({"n": len(chunk),
                    "predicted": sum(r["score"] for r in chunk) / len(chunk),
                    "observed": sum(r["y"] for r in chunk) / len(chunk)})
    return out


def leakage_scan(median_lead, n_nonpositive_leads, pr_auc_value, base_rate):
    """Automatable half of the SPEC-08 §5 leakage hunt. A signal that 'detects' at or after the
    event (nonpositive lead), or scores implausibly perfectly, is flagged for the hostile review."""
    flags = []
    if n_nonpositive_leads > 0:
        flags.append(f"{n_nonpositive_leads} label(s) 'detected' at/after the event (lead<=0) — possible leakage")
    if median_lead is not None and median_lead <= 0:
        flags.append("median lead-time <= 0 — the signal does not lead the event (leakage or degenerate)")
    if pr_auc_value >= 0.999 and base_rate < 0.5:
        flags.append("PR-AUC ~1.0 against a rare base rate — implausibly perfect, audit for leakage")
    return flags


# --------------------------------------------------------------------- evaluate & scorecard
def evaluate(*, signal_obs, baseline_obs, labels, horizon, train_end, bars, days_per_t=7,
             test_start=None, train_label_window=None, test_label_window=None):
    """Retrocast a signal against labels. Leak control: the operating threshold is chosen on the
    TRAIN split only (t <= train_end), then everything is scored on the held-out TEST split.
    bars keys: target_recall (train event-recall to set the op point), precision, recall (test
    event-recall bar), median_lead_days, auc_margin. Returns the full results dict.

    `test_start` (default train_end+1) opens a GAP between the splits, so cell-weeks whose horizon
    straddles the boundary can be excluded from scoring. `train_label_window` / `test_label_window`
    are inclusive (lo, hi) ranges on the EVENT week, used for the event-level metrics (event-recall
    and lead time) so an event whose pre-window is only half-observed inside its split is not
    counted as a miss. Labels are ALWAYS passed whole to the cell labeller — narrowing them there
    would mislabel true positives as negatives. Defaults reproduce the original behaviour exactly."""
    test_start = (train_end + 1) if test_start is None else test_start
    tr_lo, tr_hi = train_label_window or (-math.inf, train_end)
    te_lo, te_hi = test_label_window or (test_start, math.inf)
    te = label_cells([o for o in signal_obs if o[1] >= test_start], labels, horizon)
    te_base = label_cells([o for o in baseline_obs if o[1] >= test_start], labels, horizon)
    te_labels = [(e, et) for (e, et) in labels if te_lo <= et <= te_hi]
    te_obs = [o for o in signal_obs if o[1] >= test_start]
    tr_obs = [o for o in signal_obs if o[1] <= train_end]
    tr_labels = [(e, et) for (e, et) in labels if tr_lo <= et <= tr_hi]

    # Op threshold set on TRAIN by event-recall (never sees the test window) — the leak control.
    thr = operating_threshold_event(tr_obs, tr_labels, horizon, bars["target_recall"])
    curve, base_rate = pr_curve(te)
    auc, base_auc = pr_auc(curve), pr_auc(pr_curve(te_base)[0])
    pr_at = precision_recall_at(te, thr)
    ev_recall = event_recall_at(te_obs, te_labels, thr, horizon)
    leads, nonpos = lead_time_days(te_obs, te_labels, thr, horizon, days_per_t)
    med_lead = statistics.median(leads) if leads else None
    prec_ci = wilson_ci(pr_at["tp"], pr_at["tp"] + pr_at["fp"])

    detail = {
        "beats_baseline": auc >= base_auc + bars["auc_margin"],
        "precision_ok": pr_at["precision"] >= bars["precision"],
        "recall_ok": ev_recall >= bars["recall"],
        "lead_ok": med_lead is not None and med_lead >= bars["median_lead_days"],
    }
    return {
        "operating_threshold": thr,
        "metrics": {"base_rate": base_rate, "pr_auc": auc, "baseline_pr_auc": base_auc,
                    "precision": pr_at["precision"], "cell_recall": pr_at["recall"],
                    "event_recall": ev_recall, "precision_ci95": list(prec_ci),
                    "median_lead_days": med_lead, "n_test_labels": len(te_labels),
                    "lead_times_days": leads},
        "curve": curve, "calibration": calibration_deciles(te),
        "leakage_flags": leakage_scan(med_lead, nonpos, auc, base_rate),
        "bars": dict(bars), "pass": bool(all(detail.values())), "pass_detail": detail,
    }


def scorecard(*, index, version, registration_commit, generated, data_vintages, horizon, result):
    """Machine-readable scorecard (SPEC-08 §3). The Track Record page renders ONLY from these."""
    m = result["metrics"]
    return {
        "index": index, "version": version,
        "registration_commit": registration_commit, "generated": generated,
        "data_vintages": data_vintages, "horizon_periods": horizon,
        "operating_threshold": result["operating_threshold"],
        "metrics": {k: v for k, v in m.items() if k != "lead_times_days"},
        "bars": result["bars"], "pass": result["pass"], "pass_detail": result["pass_detail"],
        "leakage_flags": result["leakage_flags"],
    }


def write_scorecard(path, card):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(card, f, indent=2)
