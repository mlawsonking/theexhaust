"""Retrocast harness tests on synthetic data (offline, deterministic). Exercises the SPEC-08 §7
acceptance items: a dumb-baseline comparison is present; a deliberately-leaked feature is caught;
the scorecard validates. Run:
    python -m retrocast.tests.test_harness
    python -m pytest retrocast/tests/test_harness.py
"""
from __future__ import annotations

import json

from retrocast import harness

N_ENT, WEEKS, H, TRAIN_END = 50, 105, 26, 52
EVENTS = {i: 30 + 3 * i for i in range(20)}          # entity -> event week (30..87); test events et>52
BARS = {"target_recall": 0.8, "precision": 0.5, "recall": 0.8, "median_lead_days": 14, "auc_margin": 0.05}


def _gen():
    """A genuine leading SIGNATURE (a clean step high for the 8 weeks BEFORE the event), a dumb
    BASELINE (every 4th week 'suspicious', ignoring the real signal), and a LEAKED signal (fires
    only at the event week itself — uses the announcement, so it never truly leads)."""
    labels = [(e, et) for e, et in EVENTS.items()]
    sig, base, leak = [], [], []
    for e in range(N_ENT):
        et = EVENTS.get(e)
        for t in range(WEEKS):
            # The signature fires for the 8 weeks before an event AND, on a handful of event-free
            # entities, spuriously. Without those false positives the fixture would be a perfect
            # oracle (precision 1.0), which is not what an honest signal looks like and — since
            # 2026-07-30 — correctly trips the leakage scan's implausible-precision rule.
            true_hit = et is not None and et - 8 <= t < et
            false_hit = et is None and e % 7 == 0 and 60 <= t < 68     # inside the TEST split
            sig.append((e, t, 1.0 if (true_hit or false_hit) else 0.05))
            base.append((e, t, 0.5 if t % 4 == 0 else 0.05))
            leak.append((e, t, 1.0 if (et is not None and t == et) else 0.05))
    return sig, base, leak, labels


def test_signature_passes_and_beats_baseline():
    sig, base, _leak, labels = _gen()
    res = harness.evaluate(signal_obs=sig, baseline_obs=base, labels=labels,
                           horizon=H, train_end=TRAIN_END, bars=BARS)
    m = res["metrics"]
    assert m["event_recall"] >= BARS["recall"], m
    assert m["median_lead_days"] is not None and m["median_lead_days"] >= BARS["median_lead_days"], m
    assert m["pr_auc"] >= m["baseline_pr_auc"] + BARS["auc_margin"], m   # beats the dumb baseline
    assert res["pass"] is True, res["pass_detail"]
    assert res["leakage_flags"] == [], res["leakage_flags"]              # a clean signal trips no leak flag


def test_planted_leak_is_caught():
    _sig, base, leak, labels = _gen()
    res = harness.evaluate(signal_obs=leak, baseline_obs=base, labels=labels,
                           horizon=H, train_end=TRAIN_END, bars=BARS)
    assert res["leakage_flags"], "planted leak (detects at the event, lead<=0) must be flagged"
    assert res["pass"] is False                                         # and it must NOT publish


def test_impossible_bars_fail():
    sig, base, _leak, labels = _gen()
    res = harness.evaluate(signal_obs=sig, baseline_obs=base, labels=labels, horizon=H,
                           train_end=TRAIN_END, bars=dict(BARS, median_lead_days=9999))
    assert res["pass"] is False and res["pass_detail"]["lead_ok"] is False


def test_scorecard_roundtrip(tmp_path):
    sig, base, _leak, labels = _gen()
    res = harness.evaluate(signal_obs=sig, baseline_obs=base, labels=labels,
                           horizon=H, train_end=TRAIN_END, bars=BARS)
    card = harness.scorecard(index="synthetic", version="v1", registration_commit="abc123",
                             generated="2026-07-13",
                             data_vintages=[{"name": "labels", "vintage": "2026-06", "sha256": "deadbeef"}],
                             horizon=H, result=res)
    p = tmp_path / "scorecard.json"
    harness.write_scorecard(str(p), card)
    loaded = json.load(open(p, encoding="utf-8"))
    assert loaded["pass"] is True and loaded["index"] == "synthetic"
    assert loaded["registration_commit"] == "abc123"
    assert "lead_times_days" not in loaded["metrics"]                   # heavy field excluded from the card


def _run_plain():
    import tempfile, pathlib
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            if "tmp_path" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
                with tempfile.TemporaryDirectory() as d:
                    fn(pathlib.Path(d))
            else:
                fn()
            print("ok:", name)
            passed += 1
    # surface the headline metrics for the record
    sig, base, _l, labels = _gen()
    r = harness.evaluate(signal_obs=sig, baseline_obs=base, labels=labels, horizon=H, train_end=TRAIN_END, bars=BARS)
    m = r["metrics"]
    print(f"[metrics] op_thr={r['operating_threshold']} event_recall={m['event_recall']:.2f} "
          f"precision={m['precision']:.2f} median_lead={m['median_lead_days']}d "
          f"pr_auc={m['pr_auc']:.3f} baseline_auc={m['baseline_pr_auc']:.3f} pass={r['pass']}")
    print(f"ALL {passed} HARNESS TESTS PASS")


if __name__ == "__main__":
    _run_plain()
