"""Entity resolver + receipts tests (offline, deterministic; SPEC-09 §4 skeleton). Run:
    python -m resolver.tests.test_resolver
    python -m pytest resolver/tests/test_resolver.py
"""
from __future__ import annotations

from resolver import ledger, receipts
from resolver.crosswalks import Crosswalk
from resolver.resolve import jaccard, norm_key, resolve_company

ROWS = [
    {"cik": "320193", "ticker": "AAPL", "title": "Apple Inc.", "source": "sec"},
    {"cik": "1045810", "ticker": "NVDA", "title": "NVIDIA CORP", "source": "sec"},
    {"cik": "51143", "ticker": "IBM", "title": "International Business Machines Corp", "source": "sec"},
    {"cik": "1318605", "ticker": "TSLA", "title": "Tesla Motors Inc", "source": "sec"},
    {"cik": "111", "ticker": "ACM1", "title": "Acme Corp", "source": "sec"},
    {"cik": "222", "ticker": "ACM2", "title": "Acme Inc", "source": "sec"},
]
CX = Crosswalk(ROWS)


def test_normalize_and_jaccard():
    assert norm_key("Apple Inc.") == "apple"
    assert norm_key("International Business Machines Corp") == "international business machines"
    assert jaccard(["a", "b"], ["b", "c"]) == 1 / 3


def test_tiers():
    r = resolve_company(CX, "AAPL")
    assert r["tier"] == "T0" and r["match"]["cik"] == "320193"
    assert resolve_company(CX, "320193")["tier"] == "T0"
    r = resolve_company(CX, "Apple Inc.")
    assert r["tier"] == "T1" and r["match"]["ticker"] == "AAPL"
    # T2 accept: reordered tokens (T1 misses the order-sensitive key; set-based T2 catches it)
    r = resolve_company(CX, "Business Machines International")
    assert r["tier"] == "T2" and r["match"]["cik"] == "51143" and r["confidence"] >= 0.85
    # T1 ambiguous: two issuers share the normalized name 'acme' -> QUEUE, never guess
    r = resolve_company(CX, "Acme")
    assert "ambiguous" in r and r["tier"] == "T1" and len(r["ambiguous"]) == 2
    # T2 ambiguous band -> queue for T3
    r = resolve_company(CX, "Tesla Motors Cars")
    assert "ambiguous" in r and r["tier"] == "T2"
    # no match
    assert resolve_company(CX, "Nonexistent Widget Factory") is None


def test_ledger_append_and_cache(tmp_path):
    lp = str(tmp_path / "ledger" / "ledger.jsonl")
    a, b = {"cik": "51143"}, {"warn_company": "IBM Corp"}
    ledger.record(lp, a, b, "T2", 0.95, "token sim 1.0")
    assert ledger.cached_pair(lp, a, b)["confidence"] == 0.95
    assert ledger.cached_pair(lp, b, a) is not None                 # order-independent
    assert ledger.cached_pair(lp, {"cik": "999"}, {"x": "y"}) is None


def test_receipts_fail_closed(tmp_path):
    root = str(tmp_path / "receipts")
    good = receipts.build_bundle(
        number=42, unit="pct", as_of="2026-07-13", index_version="layoffs-v0",
        methodology_ref="docs/03-GAMEPLAN.md",
        inputs=[{"r2_path": "raw/ats-boards/greenhouse/stripe/2026/07/13/x.json.zst",
                 "sha256": "abc", "manifest_ref": "m"}],
        code_ref="9b89d79", official_chain={"series": "JOLTS", "last_value": None, "divergence_state": "n/a"})
    assert receipts.valid_bundle(good)
    receipts.write_bundle(root, "layoffs", "n1", good)
    assert receipts.has_valid_bundle(root, "layoffs", "n1")
    assert "sha256=abc" in receipts.render_bundle(good)
    # fail-closed: a bundle with no raw inputs is invalid and cannot be written
    bad = dict(good, inputs=[])
    assert not receipts.valid_bundle(bad)
    try:
        receipts.write_bundle(root, "layoffs", "n2", bad)
        assert False, "should refuse to write an incomplete bundle"
    except ValueError:
        pass
    assert not receipts.has_valid_bundle(root, "layoffs", "missing")   # unreceipted number cannot render


def _run_plain():
    import tempfile
    import pathlib
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            if "tmp_path" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
                with tempfile.TemporaryDirectory() as d:
                    fn(pathlib.Path(d))
            else:
                fn()
            print("ok:", name)
    print("ALL RESOLVER TESTS PASS")


if __name__ == "__main__":
    _run_plain()
