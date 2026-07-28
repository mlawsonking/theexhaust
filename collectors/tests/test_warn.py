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


def _seed(tmp_path, states):
    p = tmp_path / "seed.json"
    p.write_text(json.dumps({"states": states}), encoding="utf-8")
    return str(p)


def test_fleet_mixed_outcome_persists_the_quarantine(tmp_path):
    """W-005c/F01: a run where one state fails and the rest are fine used to record
    last_action='unchanged'/'stored', so _collector.yml skipped the state commit and the quarantine
    evidence never reached main — weekly, report and fleet_green all saw a healthy fleet."""
    seed = _seed(tmp_path, [{"state": "CA", "format": "csv", "data_url": "https://ca.gov/warn.csv"},
                            {"state": "IL", "format": "csv", "data_url": "https://il.gov/warn.csv"}])
    hp = str(tmp_path / "warn.json")
    pings = []
    orig = warn.http_get
    warn.http_get = lambda url, **kw: pings.append(url) or (200, {}, b"")
    try:
        fetch = make_fetch({"https://il.gov/warn.csv": (200, CSV)})   # CA raises -> quarantine
        res = warn.run_fleet(seed, MemBackend(), health_path=hp, heartbeat_url="http://hb/warn",
                             fetch=fetch, pause_s=0)
    finally:
        warn.http_get = orig
    assert res["stored"] == 1 and res["quarantined"] == 1
    assert pings[-1] == "http://hb/warn/fail"                  # the /fail leg, previously untested
    node = json.load(open(hp, encoding="utf-8"))["collectors"]["warn"]
    assert node["last_action"] == "quarantined"                # -> the workflow WILL commit this
    assert "last_success" not in node                          # not a success; last_run instead
    assert node["last_run"] and node["quarantined"] == 1
    assert node["states"]["CA"]["last_action"] == "quarantined-fetch"


def test_state_pauses_after_three_failures_and_asks_for_one_gate(tmp_path):
    """W-005c/F05: a state that rotates its yearly filename 404s forever — 14 alarms/week, no gate.
    Three consecutive failures now pause the state and surface ONE node-level needs_gate."""
    seed = _seed(tmp_path, [{"state": "CA", "format": "csv", "data_url": "https://ca.gov/warn.csv"},
                            {"state": "IL", "format": "csv", "data_url": "https://il.gov/warn.csv"}])
    hp = str(tmp_path / "warn.json")
    fetch = make_fetch({"https://il.gov/warn.csv": (200, CSV)})       # CA always fails
    calls = []
    for _ in range(3):
        res = warn.run_fleet(seed, MemBackend(), health_path=hp, fetch=fetch, pause_s=0)
    node = json.load(open(hp, encoding="utf-8"))["collectors"]["warn"]
    assert node["states"]["CA"]["fail_streak"] == 3 and node["states"]["CA"]["paused"] is True
    assert node["needs_gate"] == "warn-fetch-3x-CA"            # weekly reads needs_gate here
    assert ":" not in node["needs_gate"]                       # it becomes a gate FILENAME
    # the 4th firing skips the paused state entirely — no fetch, no alarm from it
    res = warn.run_fleet(seed, MemBackend(), health_path=hp,
                         fetch=make_fetch({"https://il.gov/warn.csv": (200, CSV)}, calls), pause_s=0)
    assert res["paused"] == ["CA"] and res["quarantined"] == 0
    assert not any("ca.gov" in u for u in calls)

    # ...and weekly files exactly one source gate off that record
    from opscore import gates, weekly
    from datetime import date
    pend = os.path.join(str(tmp_path), "ops", "state", "QUEUE", "pending")
    os.makedirs(pend, exist_ok=True)
    filed = weekly.file_collector_gates(str(tmp_path), {"collectors": {"warn": node}}, date(2026, 7, 28))
    assert filed == ["collector-warn-warn-fetch-3x-CA"]
    assert len(gates.load_pending(pend)) == 1                  # the gate really is on disk


def test_one_state_storage_failure_does_not_end_the_run(tmp_path):
    """W-005c/F06: a transient R2 500 on the FIRST state used to abort the whole comprehension —
    the other states lost the day entirely (perishable corpus) and their dedupe updates were lost."""
    class FlakyBackend(MemBackend):
        def put(self, key, data):
            if "/CA/" in key:
                raise OSError("R2 500")
            super().put(key, data)

    seed = _seed(tmp_path, [{"state": "CA", "format": "csv", "data_url": "https://ca.gov/warn.csv"},
                            {"state": "IL", "format": "csv", "data_url": "https://il.gov/warn.csv"}])
    hp = str(tmp_path / "warn.json")
    st = FlakyBackend()
    res = warn.run_fleet(seed, st, health_path=hp, pause_s=0,
                         fetch=make_fetch({"https://ca.gov/warn.csv": (200, CSV),
                                           "https://il.gov/warn.csv": (200, CSV)}))
    assert res["stored"] == 1 and res["quarantined"] == 1      # IL still collected
    assert any(k.startswith("raw/warn/IL/") for k in st.d)
    node = json.load(open(hp, encoding="utf-8"))["collectors"]["warn"]
    assert node["states"]["CA"]["last_action"] == "error" and node["last_action"] == "quarantined"


def test_empty_fleet_never_pings_success(tmp_path):
    """W-005c/F15: `--only CAX` (typo) collected nothing, pinged the dead-man GREEN and exited 0 —
    the exact silent stop SPEC-03 §1 exists to alarm on."""
    seed = _seed(tmp_path, [{"state": "CA", "format": "csv", "data_url": "https://ca.gov/warn.csv"}])
    pings = []
    orig = warn.http_get
    warn.http_get = lambda url, **kw: pings.append(url) or (200, {}, b"")
    try:
        res = warn.run_fleet(seed, MemBackend(), heartbeat_url="http://hb/warn",
                             fetch=make_fetch({}), only=["CAX"], pause_s=0)
    finally:
        warn.http_get = orig
    assert res["states"] == 0 and res["empty"] is True
    assert pings == ["http://hb/warn/fail"]                    # never the success URL


def test_unparseable_payload_still_stores_raw(tmp_path):
    """W-005c/F19a: the constitutional store-raw-always steer (W-004). A refactor that re-promoted
    a parse miss to a quarantine — the exact pre-W-004 behavior this design reversed — would
    otherwise pass the whole suite.

    Note vs the review's suggested fixture: a garbage body declared `csv` does NOT fail to parse
    (csv.reader tolerates any bytes -> (0, True)), so that case is asserted separately below; the
    genuine parse-miss path is exercised with a format whose parser really can fail."""
    st = MemBackend()
    node = {"states": {}}
    entry = {"state": "PA", "format": "xlsx", "data_url": "https://pa.gov/warn.xlsx"}
    r = warn.archive_state(st, entry, DT, node,                 # not a zip -> genuine parse miss
                           fetch=make_fetch({"https://pa.gov/warn.xlsx": (200, b"%PDF-1.4 \x00garbage")}))
    assert r["action"] == "stored" and r["parse_ok"] is False and r["parsed_rows"] is None
    assert any(k.startswith("raw/warn/PA/") for k in st.d)     # the raw payload IS the deliverable
    assert not any(k.startswith("quarantine/") for k in st.d)  # a parse miss is METADATA, not a quarantine
    man = json.loads(st.d["raw/warn/PA/2026/07/28/manifest.json"])
    assert man["files"][0]["parse_ok"] is False and man["files"][0]["parsed_rows"] is None
    assert man["files"][0]["volume_band"] == "unparsed"
    assert man["schema_version"] == warn.PARSER_VERSION        # F18: which parser produced the count

    # and the csv-garbage case still STORES (parse_ok True, 0 rows) — a collapse to 0 against a real
    # baseline is caught by the volume detector (F12), not by refusing to archive
    st2, node2 = MemBackend(), {"states": {}}
    e2 = {"state": "WA", "format": "csv", "data_url": "https://wa.gov/warn.csv"}
    r2 = warn.archive_state(st2, e2, DT, node2,
                            fetch=make_fetch({"https://wa.gov/warn.csv": (200, b"%PDF-1.4 \x00garbage")}))
    assert r2["action"] == "stored" and any(k.startswith("raw/warn/WA/") for k in st2.d)


def test_same_day_manifest_appends_both_entries():
    """W-005c/F19b: mirrors the ats-boards regression — a second CHANGED store the same day must
    append, never overwrite, or stored objects go missing from the SPEC-01 §3 audit index."""
    st = MemBackend()
    node = {"states": {}}
    entry = {"state": "IL", "format": "csv", "data_url": "https://il.gov/warn.csv"}
    warn.archive_state(st, entry, DT, node, fetch=make_fetch({"https://il.gov/warn.csv": (200, CSV)}))
    warn.archive_state(st, entry, DT, node,
                       fetch=make_fetch({"https://il.gov/warn.csv": (200, CSV + b"Gamma,2026-07-05,2026-09-20,7,Lake\n")}))
    man = json.loads(st.d["raw/warn/IL/2026/07/28/manifest.json"])
    assert len(man["files"]) == 2 and man["files"][0]["sha256"] != man["files"][1]["sha256"]


def test_volume_anomaly_flags_a_collapse():
    """W-005c/F12: W-004 relaxed schema-drift quarantining to parse-as-metadata; it did NOT waive
    the volume detector. A flagship state collapsing 800 -> 3 parsed rows must flag, not store green."""
    st = MemBackend()
    node = {"states": {}}
    entry = {"state": "CA", "format": "csv", "data_url": "https://ca.gov/warn.csv"}
    head = b"Company,Notice Date\n"
    for n in (800, 790, 810):                                   # build a baseline median
        body = head + b"".join(b"C%d,2026-07-01\n" % i for i in range(n))
        r = warn.archive_state(st, entry, DT, node, fetch=make_fetch({"https://ca.gov/warn.csv": (200, body)}))
        assert r["volume_band"] == "ok" and r["alarm"] is False
    collapsed = head + b"".join(b"C%d,2026-07-01\n" % i for i in range(3))
    r = warn.archive_state(st, entry, DT, node, fetch=make_fetch({"https://ca.gov/warn.csv": (200, collapsed)}))
    assert r["action"] == "stored"                              # data is data — still archived
    assert r["volume_band"] == "extreme" and r["alarm"] is True  # ...but it ALARMS
    man = json.loads(st.d["raw/warn/CA/2026/07/28/manifest.json"])
    assert man["files"][-1]["volume_band"] == "extreme"
    # a state that legitimately always parses to 0 (PA/WI link lists) is exempt, not permanently red
    node2 = {"states": {}}
    e2 = {"state": "WI", "format": "html", "data_url": "https://wi.gov/warn"}
    for body in (b"<html>a</html>", b"<html>b</html>"):
        r2 = warn.archive_state(MemBackend(), e2, DT, node2, fetch=make_fetch({"https://wi.gov/warn": (200, body)}))
        assert r2["volume_band"] == "ok" and r2["parsed_rows"] == 0


def test_http_error_body_is_quarantined_for_forensics():
    """W-005c/F13: with http_get returning non-2xx, the block-page forensics branch is now REAL —
    a 403 datacenter block stores the block page instead of discarding it."""
    st = MemBackend()
    node = {"states": {}}
    entry = {"state": "TX", "format": "html", "data_url": "https://tx.gov/warn"}
    block = b"<html>Access denied: automated traffic detected</html>"
    r = warn.archive_state(st, entry, DT, node, fetch=make_fetch({"https://tx.gov/warn": (403, block)}))
    assert r["action"] == "quarantined" and r["status"] == 403
    qkeys = [k for k in st.d if k.startswith("quarantine/warn/TX/")]
    assert qkeys and st.d[qkeys[0]] == block                    # the body was KEPT
    assert not any(k.startswith("raw/warn/TX/") for k in st.d)  # and raw/ stayed clean


def test_fleet_pauses_politely_between_states(tmp_path):
    """W-005c/F17: SPEC-01 §4.1 rate-limit + jitter is a MUST and was entirely unimplemented."""
    seed = _seed(tmp_path, [{"state": "CA", "format": "csv", "data_url": "https://ca.gov/warn.csv"},
                            {"state": "IL", "format": "csv", "data_url": "https://il.gov/warn.csv"},
                            {"state": "TX", "format": "csv", "data_url": "https://tx.gov/warn.csv"}])
    slept = []
    warn.run_fleet(seed, MemBackend(), sleeper=slept.append,
                   fetch=make_fetch({"https://ca.gov/warn.csv": (200, CSV),
                                     "https://il.gov/warn.csv": (200, CSV),
                                     "https://tx.gov/warn.csv": (200, CSV)}))
    assert len(slept) == 2 and all(s > 0 for s in slept)        # N-1 pauses, none before the first


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
