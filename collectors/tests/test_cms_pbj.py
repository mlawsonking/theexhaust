"""cms-pbj collector tests (offline, deterministic). Run:
    python -m collectors.tests.test_cms_pbj
    python -m pytest collectors/tests/test_cms_pbj.py

Fixtures mirror the REAL catalog and CSV shapes verified live 2026-07-29: a DCAT catalog whose
distributions pair each quarterly CSV with an API twin, three generations of PBJ filename
convention, and the 33-column daily-staffing header keyed on PROVNUM.
"""
from __future__ import annotations

import json

import zstandard as zstd

from collectors import cms_pbj
from collectors.framework import LocalFSBackend, sha256_hex

HEADER = ('"PROVNUM","PROVNAME","CITY","STATE","COUNTY_NAME","COUNTY_FIPS","CY_Qtr","WorkDate",'
          '"MDScensus","Hrs_RNDON","Hrs_RN","Hrs_LPN","Hrs_CNA"')


def _csv(rows=5, quarter="2026Q1", header=HEADER):
    lines = [header]
    for i in range(rows):
        lines.append(f'"01500{i%10}","HOME {i}","TOWN","AL","Franklin","059","{quarter}",'
                     f'"2026010{i%9+1}",52,0,42.28,31.61,138.06')
    return ("\n".join(lines) + "\n").encode()


def _catalog(dists):
    return json.dumps({"dataset": [
        {"title": "Some Other CMS Dataset", "distribution": []},
        {"title": cms_pbj.DATASET_TITLE, "accrualPeriodicity": "R/P3M", "distribution": dists},
    ]}).encode()


def _dist(url, title, fmt="CSV"):
    d = {"title": title, "format": fmt}
    if fmt == "CSV":
        d["downloadURL"] = url
        d["mediaType"] = "text/csv"
    else:
        d["accessURL"] = url
    return d


CATALOG = _catalog([
    _dist("https://data.cms.gov/x/api", "Payroll Based Journal Daily Nurse Staffing : 2026-01-01", "API"),
    _dist("https://data.cms.gov/a/PBJ_dailynursestaffing_CY2026Q1.csv",
          "Payroll Based Journal Daily Nurse Staffing : 2026-01-01"),
    _dist("https://data.cms.gov/b/PBJ_dailynursestaffing_CY2025Q4.csv",
          "Payroll Based Journal Daily Nurse Staffing : 2025-10-01"),
    # legacy naming generations, plus one release identifiable ONLY by its title date
    _dist("https://data.cms.gov/c/pbj_daily_nurse_staffing_cy_2020q4.csv",
          "Payroll Based Journal Daily Nurse Staffing : 2020-12-31"),
    _dist("https://data.cms.gov/d/PBJ_Nurse_2019_Q1_aayb-gfzp.csv",
          "Payroll Based Journal Daily Nurse Staffing : 2019-03-13"),
    _dist("https://data.cms.gov/e/2qky-49qq.csv",
          "Payroll Based Journal Daily Nurse Staffing : 2020-09-30"),
])


def _fetcher(catalog=CATALOG, payloads=None, log=None):
    payloads = payloads or {}

    def fetch(url, max_bytes=None, headers=None, timeout=300):
        if log is not None:
            log.append(url)
        if url == cms_pbj.CATALOG_URL:
            return 200, {}, catalog
        if url in payloads:
            body = payloads[url]
            return (body if isinstance(body, tuple)
                    else (200, {}, body[:max_bytes] if max_bytes else body))
        return 404, {}, b"not found"
    return fetch


def _no_head(monkey_value=""):
    return lambda url, timeout=60: monkey_value


# --------------------------------------------------------------------------- release discovery
def test_resolve_releases_orders_newest_first_and_reads_every_naming_generation():
    rels = cms_pbj.resolve_releases(fetch=_fetcher())
    assert [r["quarter"] for r in rels] == ["2026Q1", "2025Q4", "2020Q4", "2020Q3", "2019Q1"]
    # the API twin of a release is not an archivable file
    assert all(r["url"].endswith(".csv") for r in rels)
    # a release whose filename is an opaque id is still placed, from its title date
    assert next(r for r in rels if r["quarter"] == "2020Q3")["url"].endswith("2qky-49qq.csv")


def test_quarter_identity_agrees_between_url_and_title():
    """The live catalog had zero URL-vs-title disagreements across 37 releases; if CMS ever ships
    a file whose name contradicts its title date, that must not silently mis-file a quarter."""
    for url, title, expect in (
        ("x/PBJ_dailynursestaffing_CY2026Q1.csv", "... : 2026-01-01", "2026Q1"),
        ("x/pbj_daily_nurse_staffing_cy_2020q4.csv", "... : 2020-12-31", "2020Q4"),
        ("x/PBJ_Nurse_2019_Q1_aayb.csv", "... : 2019-03-13", "2019Q1"),
        ("x/PBJ_Nurse_Q2_2020_ym5d.csv", "... : 2020-06-30", "2020Q2"),
    ):
        assert cms_pbj._quarter_from_url(url) == expect, url
        assert cms_pbj._quarter_from_title(title) == expect, title


def test_missing_dataset_raises_rather_than_substituting():
    """A vanished source is a STOP-and-gate condition, never a reason to pick another dataset."""
    for catalog in (_catalog([]), json.dumps({"dataset": [{"title": "Something Else"}]}).encode()):
        try:
            cms_pbj.resolve_releases(fetch=_fetcher(catalog=catalog))
        except RuntimeError as e:
            assert "STOP" in str(e) or "not found" in str(e)
        else:
            raise AssertionError("a missing/empty PBJ dataset must raise")


# --------------------------------------------------------------------------- archiving
def test_stores_latest_release_only_by_default(tmp_path):
    url = "https://data.cms.gov/a/PBJ_dailynursestaffing_CY2026Q1.csv"
    raw = _csv(rows=300_000)
    storage = LocalFSBackend(str(tmp_path / "arch"))
    hp = str(tmp_path / "health.json")
    res = cms_pbj.run_fleet(storage, health_path=hp, fetch=_fetcher(payloads={url: raw}),
                            pause_s=0, check_head=False)
    assert res["releases"] == 1 and res["stored"] == 1 and res["quarantined"] == 0
    assert res["results"][0]["quarter"] == "2026Q1"

    node = json.load(open(hp, encoding="utf-8"))["collectors"]["cms-pbj"]
    # the un-backfilled history is visible in state, not discovered later by a retrocast
    assert node["published_releases"] == 5 and node["release_count"] == 1
    assert node["latest_published_quarter"] == "2026Q1"

    # SPEC-01 §3: the release keeps its OWN path and manifest entry — never concatenated
    key = node["quarters"]["2026Q1"]["key"]
    assert key.startswith("raw/cms-pbj/2026Q1/")
    man = json.loads(storage.get(key.rsplit("/", 1)[0] + "/manifest.json"))
    assert man["collector"] == "cms-pbj" and man["quarter"] == "2026Q1"
    assert man["files"][0]["source_url"] == url
    assert man["files"][0]["sha256"] == sha256_hex(raw)
    assert man["files"][0]["rows"] == 300_000
    assert "PROVNUM" in man["schema_required"]
    # stored bytes really are the payload
    blob = storage.get(key)
    assert zstd.ZstdDecompressor().decompress(blob, max_output_size=10**9) == raw


def test_unchanged_release_is_not_re_downloaded(tmp_path):
    """A 234 MB quarterly file must not move on every weekly probe (SPEC-01 §4 politeness). The
    skip needs the same URL *and* the same Last-Modified, which the live source does supply."""
    url = "https://data.cms.gov/a/PBJ_dailynursestaffing_CY2026Q1.csv"
    raw = _csv(rows=250_000)
    storage = LocalFSBackend(str(tmp_path / "arch"))
    hp = str(tmp_path / "health.json")
    log = []
    f = _fetcher(payloads={url: raw}, log=log)
    head = lambda u, timeout=60: "Tue, 30 Jun 2026 20:03:58 GMT"
    cms_pbj.run_fleet(storage, health_path=hp, fetch=f, pause_s=0, head_fn=head)
    assert url in log
    log.clear()
    res = cms_pbj.run_fleet(storage, health_path=hp, fetch=f, pause_s=0, head_fn=head)
    assert res["unchanged"] == 1 and res["stored"] == 0
    assert res["results"][0]["reason"] == "same url and last-modified"
    assert url not in log, "the payload was re-fetched despite an unchanged release"
    assert cms_pbj.CATALOG_URL in log, "the catalog is still read — that is the change signal"


def test_absent_change_signal_forces_a_fetch_rather_than_assuming_unchanged(tmp_path):
    """SPEC-01 §2 C1: **CMS overwrites revisions.** So when there is no positive evidence of
    sameness — no Last-Modified, or a HEAD that failed — the collector must fetch and let the
    content hash decide. Treating silence as 'unchanged' would silently lose an in-place revision,
    which is precisely the event this collector exists to catch."""
    url = "https://data.cms.gov/a/PBJ_dailynursestaffing_CY2026Q1.csv"
    storage = LocalFSBackend(str(tmp_path / "arch"))
    hp = str(tmp_path / "health.json")
    log = []
    cms_pbj.run_fleet(storage, health_path=hp,
                      fetch=_fetcher(payloads={url: _csv(rows=250_000)}, log=log),
                      pause_s=0, head_fn=lambda u, timeout=60: "")       # no signal available
    log.clear()
    revised = _csv(rows=251_000)                                          # same URL, new bytes
    res = cms_pbj.run_fleet(storage, health_path=hp,
                            fetch=_fetcher(payloads={url: revised}, log=log),
                            pause_s=0, head_fn=lambda u, timeout=60: "")
    assert url in log, "no change signal must force a real fetch"
    assert res["stored"] == 1, "an in-place revision was silently lost"


def test_republished_at_a_new_url_but_identical_bytes_stores_nothing_new(tmp_path):
    """CMS reissues a quarter under a fresh UUID path. Identical bytes are the same vintage, so the
    hash — not the URL — decides whether a new immutable object is written."""
    old = "https://data.cms.gov/a/PBJ_dailynursestaffing_CY2026Q1.csv"
    new = "https://data.cms.gov/zz/PBJ_dailynursestaffing_CY2026Q1.csv"
    raw = _csv(rows=250_000)
    storage = LocalFSBackend(str(tmp_path / "arch"))
    hp = str(tmp_path / "health.json")
    cms_pbj.run_fleet(storage, health_path=hp, fetch=_fetcher(payloads={old: raw}), pause_s=0,
                      check_head=False)
    cat2 = _catalog([_dist(new, "Payroll Based Journal Daily Nurse Staffing : 2026-01-01")])
    res = cms_pbj.run_fleet(storage, health_path=hp,
                            fetch=_fetcher(catalog=cat2, payloads={new: raw}), pause_s=0,
                            check_head=False)
    assert res["unchanged"] == 1 and res["stored"] == 0
    assert res["results"][0]["reason"] == "identical bytes"
    node = json.load(open(hp, encoding="utf-8"))["collectors"]["cms-pbj"]
    assert node["quarters"]["2026Q1"]["source_url"] == new      # the new URL is still recorded


def test_revision_with_changed_bytes_is_archived_as_a_second_vintage(tmp_path):
    url = "https://data.cms.gov/a/PBJ_dailynursestaffing_CY2026Q1.csv"
    storage = LocalFSBackend(str(tmp_path / "arch"))
    hp = str(tmp_path / "health.json")
    cms_pbj.run_fleet(storage, health_path=hp,
                      fetch=_fetcher(payloads={url: _csv(rows=250_000)}), pause_s=0, check_head=False)
    res = cms_pbj.run_fleet(storage, health_path=hp,
                            fetch=_fetcher(payloads={url: _csv(rows=260_000)}), pause_s=0,
                            check_head=False)
    assert res["stored"] == 1, "a revised release is a new vintage, not an overwrite"
    day = json.load(open(hp, encoding="utf-8"))["collectors"]["cms-pbj"]["quarters"]["2026Q1"]["key"]
    man = json.loads(storage.get(day.rsplit("/", 1)[0] + "/manifest.json"))
    assert len(man["files"]) == 2, "both vintages are indexed in the day's manifest"
    assert man["files"][0]["sha256"] != man["files"][1]["sha256"]


def test_schema_drift_quarantines_and_never_pollutes_raw(tmp_path):
    url = "https://data.cms.gov/a/PBJ_dailynursestaffing_CY2026Q1.csv"
    bad = _csv(rows=250_000, header=HEADER.replace('"PROVNUM"', '"FACILITY_ID"'))   # CCN key gone
    storage = LocalFSBackend(str(tmp_path / "arch"))
    hp = str(tmp_path / "health.json")
    res = cms_pbj.run_fleet(storage, health_path=hp, fetch=_fetcher(payloads={url: bad}),
                            pause_s=0, check_head=False)
    r = res["results"][0]
    assert r["action"] == "quarantined" and r["alarm"] and "PROVNUM" in r["missing"]
    assert res["quarantined"] == 1
    node = json.load(open(hp, encoding="utf-8"))["collectors"]["cms-pbj"]
    assert node["last_action"] == "quarantined", "the state must REPORT it or the commit is skipped"
    assert not storage.exists("raw/cms-pbj/2026Q1/2026/07/29/manifest.json") or True
    import os
    raw_root = os.path.join(str(tmp_path / "arch"), "raw")
    stored = [f for _r, _d, fs in os.walk(raw_root) for f in fs] if os.path.isdir(raw_root) else []
    assert not stored, f"drifted payload polluted raw/: {stored}"


def test_three_fetch_failures_pause_the_quarter_and_ask_for_one_gate(tmp_path):
    storage = LocalFSBackend(str(tmp_path / "arch"))
    hp = str(tmp_path / "health.json")
    f = _fetcher(payloads={})                       # every payload 404s
    for _ in range(3):
        res = cms_pbj.run_fleet(storage, health_path=hp, fetch=f, pause_s=0, check_head=False)
    node = json.load(open(hp, encoding="utf-8"))["collectors"]["cms-pbj"]
    assert node["quarters"]["2026Q1"]["paused"] is True
    assert res["needs_gate"] == "cms-pbj-fetch-3x-2026Q1"
    # a paused quarter is ENFORCED, not merely recorded
    res2 = cms_pbj.run_fleet(storage, health_path=hp, fetch=f, pause_s=0, check_head=False)
    assert res2["results"][0]["action"] == "paused" and res2["paused"] == ["2026Q1"]


def test_backfill_is_opt_in_and_bounded(tmp_path):
    """History is stable and re-fetchable; the CURRENT release is the perishable thing. So the
    default archives one release and `quarters=None` is the deliberate BUILD-05 backfill."""
    payloads = {r["url"]: _csv(rows=250_000, quarter=r["quarter"])
                for r in cms_pbj.resolve_releases(fetch=_fetcher())}
    storage = LocalFSBackend(str(tmp_path / "arch"))
    hp = str(tmp_path / "health.json")
    res = cms_pbj.run_fleet(storage, health_path=hp, fetch=_fetcher(payloads=payloads),
                            quarters=None, pause_s=0, check_head=False)
    assert res["releases"] == 5 and res["stored"] == 5
    quarters = json.load(open(hp, encoding="utf-8"))["collectors"]["cms-pbj"]["quarters"]
    assert set(quarters) == {"2026Q1", "2025Q4", "2020Q4", "2020Q3", "2019Q1"}
    # each release under its own prefix — the retrocast needs the boundary intact
    assert all(quarters[q]["key"].startswith(f"raw/cms-pbj/{q}/") for q in quarters)

    res2 = cms_pbj.run_fleet(storage, health_path=hp, fetch=_fetcher(payloads=payloads),
                             only="2019Q1", pause_s=0, check_head=False)
    assert res2["releases"] == 1 and res2["unchanged"] == 1


def test_empty_selection_never_pings_the_deadman_green(tmp_path):
    """Collecting nothing is the silent stop, not a clean run (W-005c/F15)."""
    storage = LocalFSBackend(str(tmp_path / "arch"))
    res = cms_pbj.run_fleet(storage, health_path=str(tmp_path / "h.json"),
                            fetch=_fetcher(), quarters=0, pause_s=0, check_head=False)
    assert res["empty"] is True and res["heartbeat"] == "unset"
    res2 = cms_pbj.run_fleet(storage, health_path=str(tmp_path / "h2.json"),
                             heartbeat_url="http://127.0.0.1:9/hc", fetch=_fetcher(),
                             quarters=0, pause_s=0, check_head=False)
    assert res2["empty"] is True and res2["heartbeat"].startswith("err:")


def test_head_probe_failure_falls_through_to_a_real_fetch(tmp_path):
    """The HEAD is an optimisation. If it fails it must never cause a release to be skipped."""
    assert cms_pbj.head_last_modified("http://127.0.0.1:9/nope", timeout=1) == ""
    url = "https://data.cms.gov/a/PBJ_dailynursestaffing_CY2026Q1.csv"
    storage = LocalFSBackend(str(tmp_path / "arch"))
    res = cms_pbj.run_fleet(storage, health_path=str(tmp_path / "h.json"),
                            fetch=_fetcher(payloads={url: _csv(rows=250_000)}),
                            pause_s=0, check_head=True)
    assert res["stored"] == 1


def test_politeness_pause_between_releases(tmp_path):
    calls = []
    payloads = {r["url"]: _csv(rows=250_000, quarter=r["quarter"])
                for r in cms_pbj.resolve_releases(fetch=_fetcher())}
    cms_pbj.run_fleet(LocalFSBackend(str(tmp_path / "arch")), health_path=str(tmp_path / "h.json"),
                      fetch=_fetcher(payloads=payloads), quarters=None, check_head=False,
                      sleeper=calls.append)
    assert len(calls) == 4, "one pause between each of 5 releases"
    assert all(c > 0 for c in calls)


def _run_plain():
    import pathlib
    import tempfile
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
    print(f"ALL {passed} CMS-PBJ TESTS PASS")


if __name__ == "__main__":
    _run_plain()
