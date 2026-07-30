"""Tests for the NHTSA retrocast v1 signal construction and the harness fast paths.

The load-bearing ones are adversarial: a complaint planted in the FUTURE must not move any
feature at t (the leak control is structural, not a promise), the O(N log N) operating-threshold
search must return exactly what the brute-force reference returns, and the numpy fit must equal a
pure-Python reference to 1e-9 so the published coefficients are not an artefact of a library.

    python -m retrocast.tests.test_nhtsa_v1
"""
from __future__ import annotations

import math
import random

from retrocast import harness
from retrocast.nhtsa_recalls import features as F
from retrocast.nhtsa_recalls import lexicon as L
from retrocast.nhtsa_recalls import run_v1


def _weeks(spec):
    """{week: [n, severe, hazard]} from {week: (n, sev, haz)}."""
    return {w: list(v) for w, v in spec.items()}


def _naive_features(weeks, lo, hi, trailing=12, baseline=52):
    """Brute-force recompute of PRE-REGISTRATION §3 — the oracle for the sliding implementation."""
    out = []
    n_prev = None
    for t in range(lo - 1, hi + 1):
        n = sum(weeks.get(k, [0, 0, 0])[0] for k in range(t - trailing + 1, t + 1))
        sev = sum(weeks.get(k, [0, 0, 0])[1] for k in range(t - trailing + 1, t + 1))
        haz = sum(weeks.get(k, [0, 0, 0])[2] for k in range(t - trailing + 1, t + 1))
        c52 = sum(weeks.get(k, [0, 0, 0])[0] for k in range(t - baseline + 1, t + 1))
        if n == 0:
            n_prev = 0
            continue
        if t >= lo:
            base = c52 * (trailing / baseline)
            out.append((t, n, n / base if base else 0.0,
                        float(n - n_prev) if n_prev is not None else float(n), sev / n, haz / n))
        n_prev = n
    return out


def test_sliding_windows_match_brute_force():
    rng = random.Random(11)
    for _ in range(25):
        weeks = _weeks({rng.randint(0, 120): (rng.randint(1, 6), rng.randint(0, 2), rng.randint(0, 2))
                        for _ in range(rng.randint(1, 40))})
        for w, v in weeks.items():                       # keep sub-counts <= n
            v[1] = min(v[1], v[0]); v[2] = min(v[2], v[0])
        got = list(F.cell_features(weeks, 20, 130))
        want = _naive_features(weeks, 20, 130)
        assert got == want, (got[:3], want[:3])


def test_a_complaint_in_the_future_moves_nothing_at_t():
    """The leakage control, stated as a test: adding a complaint at t+1 (and at t+50) must leave
    every feature at every week <= t bit-identical."""
    base = _weeks({100: (3, 1, 2), 101: (1, 0, 1), 104: (5, 3, 4), 110: (2, 0, 0)})
    before = [r for r in F.cell_features(base, 60, 130) if r[0] <= 110]
    leaked = dict(base)
    leaked[111] = [40, 40, 40]
    leaked[160] = [99, 99, 99]
    after = [r for r in F.cell_features(leaked, 60, 130) if r[0] <= 110]
    assert before == after


def test_rate_ratio_is_one_at_steady_state():
    """A cell running at exactly its own recent normal scores 1.0 — the self-normalization the
    registration asks for ('models with more complaints' must not confound)."""
    weeks = _weeks({w: (1, 0, 0) for w in range(0, 200)})
    rows = {r[0]: r for r in F.cell_features(weeks, 100, 120)}
    t, n, rr, accel, sev, haz = rows[110]
    assert n == 12 and abs(rr - 1.0) < 1e-12 and accel == 0.0 and sev == 0.0 and haz == 0.0


def test_severity_and_hazard_are_fractions_of_the_trailing_window():
    weeks = _weeks({50: (4, 1, 3), 55: (4, 3, 0)})
    row = {r[0]: r for r in F.cell_features(weeks, 55, 60)}[55]
    assert row[1] == 8 and abs(row[4] - 4 / 8) < 1e-12 and abs(row[5] - 3 / 8) < 1e-12


def test_week_index_is_monotone_and_reversible():
    assert F.week_of("20150101") < F.week_of("20210101") < F.week_of("20251231")
    w = F.week_of_date("2021-01-01")
    assert F.week_start(w) <= __import__("datetime").date(2021, 1, 1) < F.week_start(w + 1)
    assert F.week_of("notadate") is None and F.week_of("20150230") is None


def test_operating_threshold_event_fast_matches_brute_force():
    """The O(N log N) search must be EXACTLY the reference answer — it chooses the operating
    point the publish bars are graded at, so 'close enough' is not acceptable."""
    rng = random.Random(7)
    for trial in range(20):
        obs, labels = [], []
        for e in range(12):
            for t in range(40):
                obs.append((e, t, round(rng.random(), 3)))
            if rng.random() < 0.7:
                labels.append((e, rng.randint(10, 39)))
        for target in (0.0, 0.25, 0.5, 0.75, 1.0):
            fast = harness.operating_threshold_event(obs, labels, 8, target)
            slow = harness.operating_threshold_event_naive(obs, labels, 8, target)
            assert fast == slow, (trial, target, fast, slow)


def test_operating_threshold_event_handles_empty_labels():
    obs = [(0, t, 0.1 * t) for t in range(5)]
    for target in (0.0, 0.5):
        assert (harness.operating_threshold_event(obs, [], 3, target)
                == harness.operating_threshold_event_naive(obs, [], 3, target))


def test_evaluate_defaults_are_unchanged_by_the_new_split_parameters():
    """Backward-compatibility guard: without test_start / label windows, evaluate must return
    exactly what it returned before they existed."""
    rng = random.Random(3)
    obs, base, labels = [], [], []
    for e in range(30):
        et = rng.randint(30, 90)
        labels.append((e, et))
        for t in range(100):
            obs.append((e, t, 0.9 if et - 6 <= t < et else 0.1))
            base.append((e, t, 0.5 if t % 3 == 0 else 0.1))
    bars = {"target_recall": 0.6, "precision": 0.2, "recall": 0.6, "median_lead_days": 7,
            "auc_margin": 0.01}
    a = harness.evaluate(signal_obs=obs, baseline_obs=base, labels=labels, horizon=26,
                         train_end=50, bars=bars)
    b = harness.evaluate(signal_obs=obs, baseline_obs=base, labels=labels, horizon=26,
                         train_end=50, bars=bars, test_start=51,
                         train_label_window=(-math.inf, 50), test_label_window=(51, math.inf))
    assert a["metrics"] == b["metrics"] and a["pass"] == b["pass"]


def test_a_deliberately_leaked_signal_is_caught(capsys=None):
    """SPEC-08 §7: plant a feature that reads the future and confirm the checklist machinery
    catches it. The leak here is the NHTSA-shaped one — a 'signal' that only lights up once the
    recall has already been filed — and it must surface as a nonpositive-lead flag."""
    labels = [(e, 20 + 3 * e) for e in range(25)]     # events straddle the split, so TRAIN has
    honest, leaked, base = [], [], []                 # labels to choose the operating point from
    for e in range(25):
        et = 20 + 3 * e
        for t in range(120):
            # `honest` fires before the event and also spuriously in a late window that no event
            # falls in, so it is a realistic imperfect signal rather than a perfect oracle. A
            # precision of exactly 1.0 is itself a leak tell (leakage_scan, 2026-07-30) and would
            # make this fixture assert the opposite of what it is testing.
            honest.append((e, t, 0.9 if (et - 10 <= t < et or 110 <= t < 118) else 0.1))
            leaked.append((e, t, 0.9 if t >= et else 0.1))      # fires only at/after the event
            base.append((e, t, 0.3))
    bars = {"target_recall": 0.5, "precision": 0.1, "recall": 0.5, "median_lead_days": 14,
            "auc_margin": 0.01}
    kw = dict(baseline_obs=base, labels=labels, horizon=26, train_end=59, bars=bars)
    clean = harness.evaluate(signal_obs=honest, **kw)
    dirty = harness.evaluate(signal_obs=leaked, **kw)
    assert not clean["leakage_flags"], clean["leakage_flags"]
    assert dirty["leakage_flags"], "a signal that only fires at the event must be flagged"
    assert not dirty["pass"], "a leaked signal must not pass the bars"


def _fit_reference(X, y, epochs, lr):
    """Pure-Python mirror of run_v1.fit_logreg — same algorithm, no library."""
    n, k = len(X), len(X[0])
    w = [0.0] * k
    base = sum(y) / n
    b = math.log(base / (1 - base)) if 0 < base < 1 else 0.0
    for _ in range(epochs):
        gw, gb = [0.0] * k, 0.0
        for i in range(n):
            z = b + sum(w[j] * X[i][j] for j in range(k))
            g = 1.0 / (1.0 + math.exp(-z)) - y[i]
            for j in range(k):
                gw[j] += g * X[i][j]
            gb += g
        for j in range(k):
            w[j] -= lr * gw[j] / n
        b -= lr * gb / n
    return w, b


def test_numpy_fit_equals_the_pure_python_reference():
    try:
        import numpy as np
    except ImportError:                                    # pragma: no cover - see requirements
        print("  (numpy absent — reference-only run; the published fit requires numpy)")
        return
    rng = random.Random(5)
    X = [[rng.gauss(0, 1) for _ in range(5)] for _ in range(400)]
    y = [1.0 if (x[0] + x[3] > 1.2) else 0.0 for x in X]
    w_ref, b_ref = _fit_reference(X, y, 60, 0.5)
    w, b = run_v1.fit_logreg(np.array(X), np.array(y), epochs=60, lr=0.5)
    assert abs(b - b_ref) < 1e-9, (b, b_ref)
    for a, c in zip(w.tolist(), w_ref):
        assert abs(a - c) < 1e-9, (a, c)


def test_fit_recovers_the_sign_of_a_known_effect():
    try:
        import numpy as np
    except ImportError:                                    # pragma: no cover
        return
    rng = random.Random(9)
    X = np.array([[rng.gauss(0, 1), rng.gauss(0, 1)] for _ in range(2000)])
    y = (X[:, 0] > 0.8).astype(float)
    w, b = run_v1.fit_logreg(X, y, epochs=400, lr=0.5)
    assert w[0] > 0 and abs(w[1]) < abs(w[0]) / 3, (w, b)


def test_event_recall_is_not_weighted_by_duplicate_recall_rows():
    """One campaign files a row per make/model/year and repeats across component
    sub-descriptions, so the raw flat file carries the same (cell, week) event many times over.
    Left as rows, every event-level metric silently weights the most-repeated cells. The labels a
    run hands the harness must therefore be DISTINCT (cell, week) events."""
    obs = [(0, t, 0.9 if t == 5 else 0.1) for t in range(12)] + \
          [(1, t, 0.1) for t in range(12)]
    dup = [(0, 8)] * 9 + [(1, 8)]          # cell 0 flagged, cell 1 not, 9:1 row duplication
    uniq = sorted(set(dup))
    assert harness.event_recall_at(obs, dup, 0.5, 6) == 0.9      # rows: 90% "recall"
    assert harness.event_recall_at(obs, uniq, 0.5, 6) == 0.5     # events: the honest 1 of 2


def test_vintage_pins_are_the_workbook_vintages():
    """Threshold-archaeology's cousin: the run must be pinned to the vintages the workbook
    names, and both must come from the same collection cycle."""
    assert run_v1.VINTAGES["complaints"]["sha256"].startswith("73acbdca6b6f")
    assert run_v1.VINTAGES["recalls"]["sha256"].startswith("efab48ed2da2")
    assert all(v["collected_at"].startswith("2026-07-28T12:2") for v in run_v1.VINTAGES.values())
    assert all("static.nhtsa.gov" in v["source_url"] for v in run_v1.VINTAGES.values())


def _run_plain():
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok:", name)
            passed += 1
    print(f"ALL {passed} NHTSA V1 TESTS PASS "
          f"(rule {L.INTERPRETABLE_RULE}, horizon {L.HORIZON_WEEKS}w)")


if __name__ == "__main__":
    _run_plain()
