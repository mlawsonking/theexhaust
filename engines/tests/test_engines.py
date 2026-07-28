"""E1 Posting-Diff engine tests (offline). Run:
    python -m engines.tests.test_engines
    python -m pytest engines/tests/test_engines.py
"""
from __future__ import annotations

import hashlib
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


def test_ats_fleet_writes_per_day_manifest(tmp_path):
    """W-005 regression: SPEC-01 §3 requires a per-day manifest.json (files, hashes, row counts,
    schema version, collector git ref) beside every day's snapshots. ats-boards shipped without
    one (found in R2 at BUILD-01 fleet-green), so a day's objects had no checkable index."""
    from collectors.ats_boards import run_fleet
    from collectors.framework import LocalFSBackend
    import glob as _glob
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"boards": [{"ats": "greenhouse", "token": "acme"}]}), encoding="utf-8")
    fixture = json.dumps(FIXTURES["greenhouse"]).encode()
    store = LocalFSBackend(str(tmp_path / "arch"))
    run_fleet(str(seed), store, health_path=str(tmp_path / "H.json"),
              fetch_fn=lambda a, t, max_bytes=None: (200, {}, fixture, f"http://b/{a}/{t}"))

    mans = _glob.glob(str(tmp_path / "arch" / "raw" / "ats-boards" / "greenhouse" / "acme" / "**" / "manifest.json"),
                      recursive=True)
    assert len(mans) == 1, mans                       # exactly one per board per day
    man = json.load(open(mans[0], encoding="utf-8"))
    assert man["collector"] == "ats-boards" and man["ats"] == "greenhouse" and man["token"] == "acme"
    assert man["schema_version"] == ats.SCHEMA_VERSION and man["git_ref"]
    f0 = man["files"][0]
    assert f0["sha256"] == hashlib.sha256(fixture).hexdigest()      # hash matches the archived bytes
    assert f0["postings"] == 1 and f0["file"].endswith(".json.zst") and f0["source_url"]

    # a second, CHANGED snapshot the same day appends to the same manifest (never overwrites)
    fixture2 = json.dumps({"jobs": FIXTURES["greenhouse"]["jobs"] * 2}).encode()
    run_fleet(str(seed), store, health_path=str(tmp_path / "H.json"),
              fetch_fn=lambda a, t, max_bytes=None: (200, {}, fixture2, "u"))
    man2 = json.load(open(mans[0], encoding="utf-8"))
    assert len(man2["files"]) == 2 and man2["files"][0] == f0


def test_one_dead_board_does_not_kill_the_fleet(tmp_path):
    """W-005c/F02: archive_board called fetch with no try/except, and http_get raises on non-2xx —
    so ONE dead token (routine when a seed company drops its ATS) killed the whole run: every board
    after it lost the day's diff, the health file was never written, and no heartbeat fired at all."""
    from collectors.ats_boards import run_fleet
    from collectors.framework import LocalFSBackend
    import glob as _glob
    import urllib.error
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"boards": [{"ats": "greenhouse", "token": "a"},
                                           {"ats": "greenhouse", "token": "dead"},
                                           {"ats": "greenhouse", "token": "c"}]}), encoding="utf-8")
    good = json.dumps(FIXTURES["greenhouse"]).encode()

    def fetch(a, tok, max_bytes=None):
        if tok == "dead":
            raise urllib.error.URLError("nodename nor servname provided")
        return 200, {}, good, f"http://b/{a}/{tok}"

    store = LocalFSBackend(str(tmp_path / "arch"))
    hp = str(tmp_path / "H.json")
    res = run_fleet(str(seed), store, health_path=hp, fetch_fn=fetch, pause_s=0)
    assert res["stored"] == 2 and res["quarantined"] == 1          # the fleet CONTINUED
    for tok in ("a", "c"):
        assert _glob.glob(str(tmp_path / "arch" / "raw" / "ats-boards" / "greenhouse" / tok / "**" / "*.json.zst"),
                          recursive=True)
    h = json.load(open(hp, encoding="utf-8"))                       # health really was written
    boards = h["collectors"]["ats-boards"]["boards"]
    assert boards["greenhouse/dead"]["last_action"] == "quarantined-fetch"
    assert "URLError" in boards["greenhouse/dead"]["last_error"]
    assert h["collectors"]["ats-boards"]["last_action"] == "quarantined"   # persists to main (F01)


def test_empty_board_is_a_valid_store_not_a_quarantine(tmp_path):
    """W-005c/F03: `assert n >= 1` treated a legitimately empty board as a parse failure — so a
    company closing its last opening alarmed 3x/day forever AND the all-postings-vanished snapshot,
    the single most valuable event for Posting-Diff, never landed in raw/."""
    from collectors.ats_boards import run_fleet
    from collectors.framework import LocalFSBackend
    import glob as _glob
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"boards": [{"ats": "greenhouse", "token": "frozen"}]}), encoding="utf-8")
    store = LocalFSBackend(str(tmp_path / "arch"))
    hp = str(tmp_path / "H.json")
    res = run_fleet(str(seed), store, health_path=hp, pause_s=0,
                    fetch_fn=lambda a, t, max_bytes=None: (200, {}, b'{"jobs": []}', "u"))
    assert res["stored"] == 1 and res["quarantined"] == 0
    assert res["results"][0]["postings"] == 0
    zsts = _glob.glob(str(tmp_path / "arch" / "raw" / "ats-boards" / "**" / "*.json.zst"), recursive=True)
    assert len(zsts) == 1                                           # the vanished-postings vintage IS archived
    mans = _glob.glob(str(tmp_path / "arch" / "raw" / "ats-boards" / "**" / "manifest.json"), recursive=True)
    assert json.load(open(mans[0], encoding="utf-8"))["files"][0]["postings"] == 0
    assert not _glob.glob(str(tmp_path / "arch" / "quarantine" / "**"), recursive=True)
    # genuinely unparseable payloads DO still quarantine — once, then anti-storm (F03 second half)
    res2 = run_fleet(str(seed), store, health_path=hp, pause_s=0,
                     fetch_fn=lambda a, t, max_bytes=None: (200, {}, b"not json", "u"))
    assert res2["quarantined"] == 1 and res2["results"][0]["alarm"] is True
    res3 = run_fleet(str(seed), store, health_path=hp, pause_s=0,
                     fetch_fn=lambda a, t, max_bytes=None: (200, {}, b"not json", "u"))
    assert res3["results"][0]["action"] == "quarantined-dup" and res3["results"][0]["alarm"] is False


def test_board_pauses_after_three_failures_and_empty_fleet_never_pings_green(tmp_path):
    """W-005c/F05 + F15 for the board fleet: three consecutive failures pause the board and raise
    one node-level needs_gate; an empty seed must never ping the dead-man heartbeat green."""
    import collectors.ats_boards as ab
    from collectors.framework import LocalFSBackend
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"boards": [{"ats": "greenhouse", "token": "dead"}]}), encoding="utf-8")
    store = LocalFSBackend(str(tmp_path / "arch"))
    hp = str(tmp_path / "H.json")

    def boom(a, t, max_bytes=None):
        raise OSError("connection reset")

    for _ in range(3):
        ab.run_fleet(str(seed), store, health_path=hp, fetch_fn=boom, pause_s=0)
    node = json.load(open(hp, encoding="utf-8"))["collectors"]["ats-boards"]
    assert node["boards"]["greenhouse/dead"]["paused"] is True
    assert node["needs_gate"] == "ats-boards-fetch-3x-greenhouse-dead"   # slug-safe: no '/' left
    res = ab.run_fleet(str(seed), store, health_path=hp, fetch_fn=boom, pause_s=0)
    assert res["paused"] == ["greenhouse/dead"] and res["quarantined"] == 0

    pings = []
    orig = ab.http_get
    ab.http_get = lambda url, **kw: pings.append(url) or (200, {}, b"", url)
    try:
        empty = tmp_path / "empty.json"
        empty.write_text(json.dumps({"boards": []}), encoding="utf-8")
        r = ab.run_fleet(str(empty), store, health_path=str(tmp_path / "H2.json"),
                         heartbeat_url="http://hb/ats", pause_s=0)
    finally:
        ab.http_get = orig
    assert r["empty"] is True and pings == ["http://hb/ats/fail"]


def test_truncated_smartrecruiters_board_is_refused_not_archived(tmp_path):
    """W-005c/F16: ?limit=100 with no pagination would archive a silently truncated 'full board'
    snapshot — unfixable once immutable. Until pagination lands (C3 gate) we refuse the payload."""
    from collectors.ats_boards import run_fleet
    from collectors.framework import LocalFSBackend
    import glob as _glob
    complete = json.dumps({"totalFound": 1, "content": FIXTURES["smartrecruiters"]["content"]}).encode()
    truncated = json.dumps({"totalFound": 150, "content": FIXTURES["smartrecruiters"]["content"]}).encode()
    assert ats.truncation("smartrecruiters", complete)[0] is False
    assert ats.truncation("smartrecruiters", truncated)[0] is True
    assert ats.truncation("greenhouse", b'{"jobs": []}')[0] is False      # only SR is capped

    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"boards": [{"ats": "smartrecruiters", "token": "big"}]}), encoding="utf-8")
    store = LocalFSBackend(str(tmp_path / "arch"))
    res = run_fleet(str(seed), store, health_path=str(tmp_path / "H.json"), pause_s=0,
                    fetch_fn=lambda a, t, max_bytes=None: (200, {}, truncated, "u"))
    assert res["quarantined"] == 1 and res["results"][0]["alarm"] is True
    assert not _glob.glob(str(tmp_path / "arch" / "raw" / "**" / "*.json.zst"), recursive=True)
    assert _glob.glob(str(tmp_path / "arch" / "quarantine" / "**" / "*.json"), recursive=True)
    # a complete SR payload archives normally
    res2 = run_fleet(str(seed), store, health_path=str(tmp_path / "H2.json"), pause_s=0,
                     fetch_fn=lambda a, t, max_bytes=None: (200, {}, complete, "u"))
    assert res2["stored"] == 1


def test_no_smartrecruiters_in_the_seed_until_pagination_lands():
    """W-005c/F16 onboarding block: SR entries stay out of the seed universe until the endpoint
    pages. Delete this test in the same change that implements pagination — not before."""
    import os
    seed_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                             "collectors", "seed_boards.json")
    boards = json.load(open(seed_path, encoding="utf-8")).get("boards", [])
    assert boards, "seed_boards.json must not be empty"
    assert not [b for b in boards if b.get("ats") == "smartrecruiters"], \
        "smartrecruiters boards are blocked at onboarding until F16 pagination lands"


def test_ats_fleet_heartbeat_and_alarm(tmp_path):
    """SPEC-02 §1 job contract: healthy fleet run pings the heartbeat OK; a quarantine pings
    /fail and is counted (drives the nonzero exit in __main__)."""
    import collectors.ats_boards as ab
    from collectors.framework import LocalFSBackend
    pings = []
    orig = ab.http_get
    ab.http_get = lambda url, **kw: pings.append(url) or (200, {}, b"", url)
    try:
        seed = tmp_path / "seed.json"
        seed.write_text(json.dumps({"boards": [{"ats": "greenhouse", "token": "acme"}]}), encoding="utf-8")
        store = LocalFSBackend(str(tmp_path / "arch"))
        hp = str(tmp_path / "H.json")

        good = json.dumps(FIXTURES["greenhouse"]).encode()
        r_ok = ab.run_fleet(str(seed), store, health_path=hp, heartbeat_url="http://hb/ats",
                            fetch_fn=lambda a, t, max_bytes=None: (200, {}, good, "u"))
        assert r_ok["quarantined"] == 0 and r_ok["heartbeat"] == "pinged"
        assert pings and pings[-1] == "http://hb/ats"                        # OK ping, no /fail

        pings.clear()
        r_bad = ab.run_fleet(str(seed), store, health_path=hp, heartbeat_url="http://hb/ats",
                             fetch_fn=lambda a, t, max_bytes=None: (200, {}, b"not json", "u"))
        assert r_bad["quarantined"] == 1                                     # -> __main__ exits nonzero
        assert pings and pings[-1] == "http://hb/ats/fail"                   # failure ping
    finally:
        ab.http_get = orig


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
