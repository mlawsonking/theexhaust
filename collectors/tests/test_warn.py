"""WARN fleet tests (offline, deterministic). Run:
    python -m collectors.tests.test_warn
    python -m pytest collectors/tests/test_warn.py
"""
from __future__ import annotations

import io
import json
import os
import zipfile
from datetime import datetime, timezone

from collectors import warn
from collectors.framework import StorageBackend, sha256_hex

DT = datetime(2026, 7, 28, 12, 20, tzinfo=timezone.utc)

CSV = b"Company,Notice Date,Effective Date,Employees,County\nACME Corp,2026-07-01,2026-09-01,120,Cook\nBeta LLC,2026-07-03,2026-09-15,45,DuPage\n"


class MemBackend(StorageBackend):
    def __init__(self):
        self.d = {}
    def put(self, key, data): self.d[key] = data
    def get(self, key): return self.d.get(key)
    def exists(self, key): return key in self.d


def make_fetch(mapping, calls=None):
    """Fake http_get: url -> (status, raw). Unknown url raises (transport failure)."""
    def f(url, max_bytes=None, headers=None, timeout=300):
        if calls is not None:
            calls.append(url)
        if url not in mapping:
            raise OSError(f"no route to {url}")
        status, raw = mapping[url]
        return status, {}, (raw[:max_bytes] if max_bytes else raw)
    return f


def _make_xlsx(nrows):
    buf = io.BytesIO()
    body = "".join(f'<row r="{i}"><c><v>{i}</v></c></row>' for i in range(1, nrows + 1))
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", f"<worksheet><sheetData>{body}</sheetData></worksheet>")
    return buf.getvalue()


# ------------------------------------------------------------------ parsing
def test_parse_count_formats():
    assert warn.parse_count("csv", CSV) == (2, True)               # 2 data rows
    assert warn.parse_count("socrata-csv", CSV) == (2, True)
    assert warn.parse_count("json", json.dumps([{"a": 1}, {"a": 2}, {"a": 3}]).encode()) == (3, True)
    assert warn.parse_count("socrata-json", json.dumps({"data": [{"x": 1}]}).encode()) == (1, True)
    assert warn.parse_count("xlsx", _make_xlsx(4)) == (3, True)     # 4 rows minus header
    html = b"<table><thead><tr><th>Co</th></tr></thead><tbody><tr><td>ACME</td></tr><tr><td>BETA</td></tr></tbody></table>"
    assert warn.parse_count("html-table", html) == (2, True)
    # unparseable / unsupported → metadata, never raises
    assert warn.parse_count("pdf", b"%PDF-1.7 ...") == (None, False)
    assert warn.parse_count("json", b"{not json") == (None, False)
    assert warn.parse_count("xlsx", b"not a zip") == (None, False)


# ------------------------------------------------------------------ resolver
def test_resolve_direct_and_landing():
    assert warn.resolve_data_url({"state": "X", "data_url": "https://e.gov/warn.csv"}) == "https://e.gov/warn.csv"
    landing = "https://dol.state.gov/warn"
    html = b'<a href="/files/WARN_FY2026.xlsx">current</a>'
    fetch = make_fetch({landing: (200, html)})
    got = warn.resolve_data_url(
        {"state": "X", "landing_url": landing, "link_regex": r'href="([^"]+WARN_FY\d+\.xlsx)"'}, fetch=fetch)
    assert got == "https://dol.state.gov/files/WARN_FY2026.xlsx"


# ------------------------------------------------------------------ archive one state
def test_archive_stores_raw_parses_and_dedupes():
    st = MemBackend()
    node = {"states": {}}
    entry = {"state": "IL", "agency": "IDES", "format": "csv", "data_url": "https://il.gov/warn.csv"}
    fetch = make_fetch({"https://il.gov/warn.csv": (200, CSV)})
    r1 = warn.archive_state(st, entry, DT, node, fetch=fetch)
    assert r1["action"] == "stored" and r1["parsed_rows"] == 2 and r1["parse_ok"] is True
    # raw stored compressed (.csv.zst) + a manifest written with the parse metadata
    rawkeys = [k for k in st.d if k.startswith("raw/warn/IL/") and k.endswith(".csv.zst")]
    assert len(rawkeys) == 1
    man = json.loads(st.d["raw/warn/IL/2026/07/28/manifest.json"])
    assert man["files"][0]["parsed_rows"] == 2 and man["files"][0]["parse_ok"] is True
    assert man["files"][0]["sha256"] == sha256_hex(CSV)
    # second identical fetch → dedupe unchanged, no new object
    r2 = warn.archive_state(st, entry, DT, node, fetch=fetch)
    assert r2["action"] == "unchanged"
    assert len([k for k in st.d if k.startswith("raw/warn/IL/") and k.endswith(".csv.zst")]) == 1


def test_archive_year_template_substituted():
    st = MemBackend()
    node = {"states": {}}
    calls = []
    entry = {"state": "FL", "format": "html", "data_url": "https://fl.gov/WarnList?year={year}"}
    fetch = make_fetch({f"https://fl.gov/WarnList?year={DT.year}": (200, b"<table><tr><td>x</td></tr></table>")}, calls)
    r = warn.archive_state(st, entry, DT, node, fetch=fetch)
    assert r["action"] == "stored"                       # {year} was substituted to the real year
    assert calls[-1] == f"https://fl.gov/WarnList?year={DT.year}"


def test_archive_xlsx_stored_uncompressed():
    st = MemBackend()
    node = {"states": {}}
    entry = {"state": "CA", "format": "xlsx", "data_url": "https://ca.gov/warn.xlsx"}
    fetch = make_fetch({"https://ca.gov/warn.xlsx": (200, _make_xlsx(6))})
    r = warn.archive_state(st, entry, DT, node, fetch=fetch)
    assert r["action"] == "stored" and r["parsed_rows"] == 5
    assert any(k.endswith(".xlsx") for k in st.d) and not any(k.endswith(".xlsx.zst") for k in st.d)


def test_archive_quarantines_on_fetch_failure_and_non200():
    st = MemBackend()
    node = {"states": {}}
    # transport error (unknown url raises)
    r = warn.archive_state(st, {"state": "NJ", "format": "html", "data_url": "https://nj.gov/x"},
                           DT, node, fetch=make_fetch({}))
    assert r["action"] == "quarantined" and r["alarm"] is True
    assert node["states"]["NJ"]["last_action"] == "quarantined-fetch"
    # non-200 with a body → quarantined, body kept for forensics, raw/ not polluted
    st2, node2 = MemBackend(), {"states": {}}
    fetch = make_fetch({"https://oh.gov/warn": (503, b"<html>maintenance</html>")})
    r2 = warn.archive_state(st2, {"state": "OH", "format": "html", "data_url": "https://oh.gov/warn"},
                            DT, node2, fetch=fetch)
    assert r2["action"] == "quarantined"
    assert any(k.startswith("quarantine/warn/OH/") for k in st2.d)
    assert not any(k.startswith("raw/warn/OH/") for k in st2.d)


# ------------------------------------------------------------------ fleet
def test_run_fleet_aggregates_and_heartbeat(tmp_path):
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"states": [
        {"state": "IL", "format": "csv", "data_url": "https://il.gov/warn.csv"},
        {"state": "NY", "format": "socrata-csv", "data_url": "https://ny.gov/warn.csv"},
    ]}), encoding="utf-8")
    st = MemBackend()
    hp = str(tmp_path / "warn.json")
    fetch = make_fetch({"https://il.gov/warn.csv": (200, CSV), "https://ny.gov/warn.csv": (200, CSV)})
    res = warn.run_fleet(str(seed), st, health_path=hp, heartbeat_url=None, fetch=fetch)
    assert res["states"] == 2 and res["stored"] == 2 and res["quarantined"] == 0
    assert res["heartbeat"] == "unset"
    health = json.load(open(hp, encoding="utf-8"))
    assert set(health["collectors"]["warn"]["states"]) == {"IL", "NY"}
    assert health["collectors"]["warn"]["last_action"] == "stored"
    # --only filter runs one state
    res2 = warn.run_fleet(str(seed), MemBackend(), health_path=str(tmp_path / "w2.json"),
                          fetch=fetch, only=["ny"])
    assert res2["states"] == 1 and res2["results"][0]["state"] == "NY"


def test_fleet_manifests_carry_git_ref(tmp_path):
    """W-005 regression (SPEC-01 §3): every per-day manifest carries the collector git ref, so a
    snapshot can be tied to the exact code that fetched it. Resolved ONCE per fleet run."""
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"states": [
        {"state": "IL", "format": "csv", "data_url": "https://il.gov/warn.csv"},
        {"state": "NY", "format": "csv", "data_url": "https://ny.gov/warn.csv"},
    ]}), encoding="utf-8")
    st = MemBackend()
    calls = []
    orig = warn.git_ref
    warn.git_ref = lambda root: calls.append(root) or "deadbeefcafe"
    try:
        warn.run_fleet(str(seed), st, health_path=str(tmp_path / "warn.json"),
                       fetch=make_fetch({"https://il.gov/warn.csv": (200, CSV),
                                         "https://ny.gov/warn.csv": (200, CSV)}))
    finally:
        warn.git_ref = orig
    assert len(calls) == 1, f"git_ref resolved {len(calls)}x — must be once per fleet run"
    mans = [json.loads(v) for k, v in st.d.items() if k.endswith("manifest.json")]
    assert len(mans) == 2 and all(m["git_ref"] == "deadbeefcafe" for m in mans)


# ------------------------------------------------------------------ seed integrity (the real seed)
def test_seed_warn_integrity():
    seed_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "seed_warn.json")
    states = warn.load_seed(seed_path)
    codes = [e["state"] for e in states]
    assert len(codes) == len(set(codes)) >= 10                       # ≥10 distinct states
    for want in ("CA", "NY", "TX", "WA", "IL"):
        assert want in codes, f"required state {want} missing from seed"
    banned = ("layoffs.fyi", "warntracker", "warn-tracker", "trackthelayoffs")   # aggregators (covenant)
    for e in states:
        assert e.get("format"), f"{e['state']} missing format"
        assert e.get("data_url") or (e.get("landing_url") and e.get("link_regex")), f"{e['state']} has no source"
        blob = json.dumps(e).lower()
        assert not any(b in blob for b in banned), f"{e['state']} references an aggregator"


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
    print(f"ALL {passed} WARN TESTS PASS")


if __name__ == "__main__":
    _run_plain()
