"""E1 Posting-Diff engine tests (offline). Run:
    python -m engines.tests.test_engines
    python -m pytest engines/tests/test_engines.py
"""
from __future__ import annotations

import json

from engines import ats, posting_diff

FIXTURES = {
    "greenhouse": {"jobs": [{"id": 1, "title": "Engineer", "location": {"name": "Remote"},
                             "absolute_url": "http://x/1", "updated_at": "2026-01-01"}]},
    "lever": [{"id": "a", "text": "PM", "categories": {"location": "NYC"},
               "hostedUrl": "http://x/a", "createdAt": 123}],
    "ashby": {"jobs": [{"id": "z", "title": "Data", "location": "SF",
                        "jobUrl": "http://x/z", "publishedAt": "2026-02-02"}]},
    "smartrecruiters": {"content": [{"id": "s1", "name": "Ops",
                                     "location": {"city": "Austin", "country": "US"},
                                     "ref": "http://x/s1", "releasedDate": "2026-03-03"}]},
}


def test_normalize_all_ats():
    for a, raw in FIXTURES.items():
        recs = ats.normalize(a, json.dumps(raw).encode())
        assert len(recs) == 1, a
        r = recs[0]
        assert set(r) == {"id", "title", "location", "url", "updated_at"}, a
        assert r["id"] and r["title"] and r["url"], a
    # spot-check field mapping across vendors
    assert ats.normalize("greenhouse", json.dumps(FIXTURES["greenhouse"]).encode())[0]["location"] == "Remote"
    assert ats.normalize("lever", json.dumps(FIXTURES["lever"]).encode())[0]["title"] == "PM"
    assert ats.normalize("smartrecruiters", json.dumps(FIXTURES["smartrecruiters"]).encode())[0]["location"] == "Austin, US"


def test_diff_and_receipts():
    prev = [{"id": "1", "title": "A", "url": "u1"}, {"id": "2", "title": "B", "url": "u2"},
            {"id": "3", "title": "C", "url": "u3"}]
    cur = [{"id": "2", "title": "B", "url": "u2"}, {"id": "4", "title": "D", "url": "u4"}]
    d = posting_diff.diff(prev, cur)
    assert d["prev_count"] == 3 and d["cur_count"] == 2
    assert d["removed_count"] == 2 and d["added_count"] == 1 and d["kept_count"] == 1
    assert abs(d["pulled_pct"] - 0.6667) < 0.001
    assert {r["title"] for r in d["removed"]} == {"A", "C"}      # receipts are the pulled postings
    assert d["added"][0]["title"] == "D"


def test_headline():
    prev = [{"id": str(i), "title": f"J{i}", "url": f"u{i}"} for i in range(10)]
    cur = prev[:3]                                                # pulled 7 of 10
    h = posting_diff.headline("Acme", posting_diff.diff(prev, cur), "in 3 weeks")
    assert "Acme removed 7 of 10" in h and "70%" in h


def test_ats_fleet_archive_and_dedupe(tmp_path):
    from collectors.ats_boards import run_fleet
    from collectors.framework import LocalFSBackend
    import glob as _glob
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"boards": [{"ats": "greenhouse", "token": "acme", "company": "Acme"}]}), encoding="utf-8")
    fixture = json.dumps(FIXTURES["greenhouse"]).encode()

    def fake(a, tok, max_bytes=None):
        return 200, {}, fixture, f"http://b/{a}/{tok}"

    store = LocalFSBackend(str(tmp_path / "arch"))
    hp = str(tmp_path / "H.json")
    r1 = run_fleet(str(seed), store, health_path=hp, fetch_fn=fake)
    assert r1["boards"] == 1 and r1["stored"] == 1
    zsts = _glob.glob(str(tmp_path / "arch" / "raw" / "ats-boards" / "greenhouse" / "acme" / "**" / "*.json.zst"), recursive=True)
    assert len(zsts) == 1
    h = json.load(open(hp, encoding="utf-8"))
    assert h["collectors"]["ats-boards"]["boards"]["greenhouse/acme"]["postings"] == 1
    r2 = run_fleet(str(seed), store, health_path=hp, fetch_fn=fake)          # unchanged -> dedupe
    assert r2["unchanged"] == 1 and r2["stored"] == 0


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
    print("ALL ENGINE TESTS PASS")


if __name__ == "__main__":
    _run_plain()
