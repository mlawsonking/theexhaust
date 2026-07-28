"""Framework unit tests (offline, deterministic). Runnable two ways:
    python -m pytest collectors/tests/test_framework.py
    python -m collectors.tests.test_framework      # plain asserts, no pytest needed
"""
from __future__ import annotations

import io
import json
import zstandard as zstd

from collectors.framework import Collector, CsvSchema, StorageBackend, sha256_hex

GOOD = (b"CMS Certification Number (CCN),Provider Name,State,Survey Date,Survey Type,"
        b"Deficiency Tag Number,Deficiency Category,Scope Severity Code\n"
        b"015009,ACME NURSING,TX,2026-01-15,Health,F0684,Quality of Care,G\n"
        b"015010,BETA CARE,TX,2026-02-01,Health,F0689,Quality of Care,J\n")

DRIFTED = b"CCN,Provider,State\n015009,ACME,TX\n"  # renamed/missing required columns
ROW_EXTRA = b"015011,GAMMA CARE,TX,2026-03-01,Health,F0690,Quality of Care,D\n"


class MemBackend(StorageBackend):
    def __init__(self):
        self.d = {}
    def put(self, key, data): self.d[key] = data
    def get(self, key): return self.d.get(key)
    def exists(self, key): return key in self.d


def _schema():
    return CsvSchema([
        "CMS Certification Number (CCN)", "Provider Name", "State", "Survey Date",
        "Survey Type", "Deficiency Tag Number", "Deficiency Category", "Scope Severity Code",
    ], row_floor=1)


def _fetch(raw):
    def f(max_bytes=None):
        return 200, {}, raw, "https://example.test/fixture.csv"
    return f


def _collector(be, tmp_health):
    return Collector("cms-deficiencies", be, _schema(), ext="csv",
                     health_path=str(tmp_health), heartbeat_url=None, repo_root=".")


def test_store_then_dedupe(tmp_path):
    be = MemBackend()
    hp = tmp_path / "HEALTH.json"
    c = _collector(be, hp)

    r1 = c.run(_fetch(GOOD))
    assert r1["action"] == "stored", r1
    assert r1["rows"] == 2, r1
    # raw stored, compressed, decompresses back to the original bytes
    rawkeys = [k for k in be.d if k.startswith("raw/") and k.endswith(".csv.zst")]
    assert len(rawkeys) == 1
    assert zstd.ZstdDecompressor().decompress(be.d[rawkeys[0]]) == GOOD
    # per-day manifest written with the full sha256
    mkey = [k for k in be.d if k.endswith("manifest.json")][0]
    man = json.loads(be.d[mkey])
    assert man["files"][0]["sha256"] == sha256_hex(GOOD)
    assert man["collector"] == "cms-deficiencies"

    # second run, identical bytes -> dedupe skip (no new raw object)
    r2 = c.run(_fetch(GOOD))
    assert r2["action"] == "unchanged", r2
    assert len([k for k in be.d if k.startswith("raw/") and k.endswith(".csv.zst")]) == 1


def test_schema_drift_quarantines(tmp_path):
    be = MemBackend()
    c = _collector(be, tmp_path / "HEALTH.json")
    r = c.run(_fetch(DRIFTED))
    assert r["action"] == "quarantined", r
    assert r["alarm"] is True
    assert "CMS Certification Number (CCN)" in r["missing"]
    # nothing polluted raw/
    assert not any(k.startswith("raw/") for k in be.d)
    assert any(k.startswith("quarantine/") for k in be.d)


_HEAD = (b"CMS Certification Number (CCN),Provider Name,State,Survey Date,Survey Type,"
         b"Deficiency Tag Number,Deficiency Category,Scope Severity Code\n")


def _csv(n):
    return _HEAD + b"".join(b"015%03d,X,TX,2026-01-01,Health,F0684,QoC,G\n" % i for i in range(n))


def test_extreme_volume_alarms(tmp_path):
    be = MemBackend()
    c = _collector(be, tmp_path / "HEALTH.json")
    assert c.run(_fetch(_csv(10)))["action"] == "stored"      # seeds rows_median = 10
    r = c.run(_fetch(_csv(200)))                               # 200 > 5x median -> extreme
    assert r["action"] == "stored" and r["alarm"] is True and r["volume_band"] == "extreme"
    man = json.loads([be.d[k] for k in be.d if k.endswith("manifest.json")][-1].decode())
    assert any(f.get("volume_band") == "extreme" for f in man["files"])


def test_drift_streak_pauses_then_dedupes(tmp_path):
    be = MemBackend()
    hp = tmp_path / "HEALTH.json"
    c = _collector(be, hp)

    r1 = c.run(_fetch(DRIFTED + b"row1\n"))                    # drift #1
    assert r1["action"] == "quarantined" and r1["alarm"] is True and r1["drift_streak"] == 1
    dup = c.run(_fetch(DRIFTED + b"row1\n"))                   # identical drifted payload recurs
    assert dup["action"] == "quarantined-dup" and dup["alarm"] is False   # no alarm storm
    assert len([k for k in be.d if k.startswith("quarantine/")]) == 1     # and no new object

    r = None
    for i in (2, 3):                                           # two more DISTINCT drifted payloads
        r = c.run(_fetch(DRIFTED + b"row%d\n" % i))
        assert r["action"] == "quarantined" and r["alarm"] is True
    assert r["drift_streak"] == 3 and r["paused"] is True      # auto-pause on 3rd (SPEC-03 §2)


def test_pause_is_enforced_and_only_an_operator_clears_it(tmp_path):
    """W-005c/F07: SPEC-03 §2's auto-pause was recorded but never enforced — a 'paused' collector
    kept fetching, so a varying drifted payload defeated the anti-storm dedupe and re-alarmed every
    firing, and any clean payload silently self-un-paused with no operator decision."""
    be = MemBackend()
    hp = tmp_path / "HEALTH.json"
    c = _collector(be, hp)
    for i in (1, 2, 3):
        c.run(_fetch(DRIFTED + b"row%d\n" % i))                # -> paused after the 3rd

    calls = []

    def counting_fetch(max_bytes=None):
        calls.append(1)
        return 200, {}, GOOD, "https://example.test/fixture.csv"

    # a paused collector does not fetch AT ALL — no request, no quarantine object, no alarm
    before = len(be.d)
    r = c.run(counting_fetch)
    assert r["action"] == "paused" and r["heartbeat"] == "withheld(paused)"
    assert calls == [] and len(be.d) == before
    assert r["needs_gate"] == "schema-drift-3x"

    # ...and a clean payload does NOT silently un-pause it (that is the operator's decision)
    assert c.run(counting_fetch)["action"] == "paused" and calls == []

    # operator re-enables via the gate -> collection resumes normally
    h = json.loads(hp.read_text())
    h["collectors"]["cms-deficiencies"].update(paused=False, needs_gate=None)
    hp.write_text(json.dumps(h))
    assert c.run(counting_fetch)["action"] == "stored" and calls == [1]


def test_corrupt_state_file_never_stops_collection(tmp_path):
    """W-005c/F14: the per-collector state file is a recoverable dedupe cache. A truncated write
    (committed by the workflow's always() persist step) must not crash every later firing."""
    be = MemBackend()
    hp = tmp_path / "HEALTH.json"
    hp.write_text('{"collectors": {"cms-def')                  # truncated mid-write
    c = _collector(be, hp)
    assert c.run(_fetch(GOOD))["action"] == "stored"           # collects anyway, state rebuilt
    assert json.loads(hp.read_text())["collectors"]["cms-deficiencies"]["last_hash"] == sha256_hex(GOOD)


def test_corrupt_manifest_is_replaced_not_fatal(tmp_path):
    """W-005c/F06: an unparseable existing day-manifest must not abort the run (it would cost the
    perishable corpus a full day, re-crashing every firing). Start fresh; raw objects are immutable."""
    be = MemBackend()
    c = _collector(be, tmp_path / "HEALTH.json")
    assert c.run(_fetch(GOOD))["action"] == "stored"
    mkey = [k for k in be.d if k.endswith("manifest.json")][0]
    be.d[mkey] = b"{truncated"
    assert c.run(_fetch(GOOD + ROW_EXTRA))["action"] == "stored"
    man = json.loads(be.d[mkey])
    assert len(man["files"]) == 1 and man["collector"] == "cms-deficiencies"


def test_http_get_returns_non_2xx_body_for_forensics():
    """W-005c/F13: urlopen raises HTTPError on 4xx/5xx and the body was discarded — but that body
    IS the block/notice page the SPEC-01 §4.5 403-ladder needs. http_get must return it."""
    import urllib.error
    import urllib.request
    from collectors import framework
    body = b"<html>Access denied: automated traffic</html>"
    orig = urllib.request.urlopen

    def raising(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {"X-Block": "1"}, io.BytesIO(body))

    urllib.request.urlopen = raising
    try:
        status, headers, got = framework.http_get("https://blocked.test/warn")
    finally:
        urllib.request.urlopen = orig
    assert status == 403 and got == body and headers.get("X-Block") == "1"


def test_polite_pause_is_injectable_and_bounded():
    """W-005c/F17: SPEC-01 §4.1 rate-limit/jitter is a MUST. Injectable so tests stay instant."""
    from collectors.framework import POLITE_PAUSE_S, polite_pause
    slept = []
    d = polite_pause(sleeper=slept.append)
    assert slept and d >= POLITE_PAUSE_S and d == slept[0]
    assert polite_pause(base=0, sleeper=slept.append) == 0.0 and len(slept) == 1   # disabled = no-op


def _make_zip(rows, fields):
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("FLAT_TEST.txt", "\n".join("\t".join(f"c{j}" for j in range(fields)) for _ in range(rows)))
    return buf.getvalue()


def test_ziptab_schema_and_zip_collector(tmp_path):
    from collectors.framework import ZipTabSchema, Collector
    sch = ZipTabSchema(expected_fields=29, member_suffix=".txt", row_floor=5)
    ok = sch.validate(_make_zip(10, 29))
    assert ok["ok"] is True and ok["rows"] == 10 and ok["extreme"] is False
    assert sch.validate(_make_zip(10, 28))["ok"] is False        # wrong field count -> drift
    assert sch.validate(b"not a zip")["ok"] is False             # not a zip -> drift
    # end-to-end: recompress=False stores the raw zip at .zip (no .zst), byte-identical
    be = MemBackend()
    c = Collector("nhtsa-recalls", be, sch, ext="zip", recompress=False, health_path=str(tmp_path / "H.json"))
    z = _make_zip(10, 29)
    r = c.run(lambda max_bytes=None: (200, {}, z, "http://x/FLAT.zip"))
    assert r["action"] == "stored"
    rawkeys = [k for k in be.d if k.startswith("raw/") and k.endswith(".zip")]
    assert len(rawkeys) == 1 and be.d[rawkeys[0]] == z


def test_jsonschema_and_json_collector(tmp_path):
    from collectors.framework import JsonSchema, Collector
    sch = JsonSchema("data", ["RESDATE", "COST"], row_floor=2)
    good = b'{"meta":{"total":3},"data":[{"RESDATE":"2020","COST":1},{"RESDATE":"2021","COST":2},{"RESDATE":"2022","COST":3}]}'
    assert sch.validate(good)["ok"] is True and sch.validate(good)["rows"] == 3
    assert sch.validate(b'{"data":[{"data":{"RESDATE":"x","COST":1}},{"data":{"RESDATE":"y","COST":2}}]}')["ok"] is True
    assert sch.validate(b'{"data":[{"RESDATE":"x"}]}')["ok"] is False   # missing COST -> drift
    assert sch.validate(b"nope")["ok"] is False                        # not json -> drift
    be = MemBackend()
    c = Collector("fdic-failures", be, sch, ext="json", health_path=str(tmp_path / "H.json"))
    assert c.run(lambda max_bytes=None: (200, {}, good, "http://x"))["action"] == "stored"
    assert any(k.endswith(".json.zst") for k in be.d if k.startswith("raw/"))


def test_health_path_creates_nested_dir(tmp_path):
    """W-002b: R1 collectors write per-collector state to ops/state/health/<c>.json — the health
    writer must create the (possibly missing) parent dir, and the file holds the one collector."""
    be = MemBackend()
    hp = tmp_path / "ops" / "state" / "health" / "cms-deficiencies.json"   # parent dirs don't exist
    c = Collector("cms-deficiencies", be, _schema(), ext="csv", health_path=str(hp))
    assert c.run(_fetch(GOOD))["action"] == "stored"
    assert hp.exists()
    saved = json.loads(hp.read_text())
    assert list(saved["collectors"].keys()) == ["cms-deficiencies"]        # single-collector shape
    assert saved["collectors"]["cms-deficiencies"]["last_hash"] == sha256_hex(GOOD)


def test_select_storage_switches_on_env(tmp_path):
    """R2 creds present -> R2Backend; absent -> LocalFSBackend (the W-001 fleet-to-R2 switch)."""
    import os
    from collectors.framework import select_storage, LocalFSBackend, R2Backend
    keys = ["R2_BUCKET", "R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"]
    saved = {k: os.environ.pop(k, None) for k in keys}
    try:
        # no creds -> local
        assert isinstance(select_storage(str(tmp_path)), LocalFSBackend)
        # creds present -> R2 (boto3 client construction is offline; no network until a call)
        os.environ.update({"R2_BUCKET": "b", "R2_ENDPOINT": "https://x.example",
                           "R2_ACCESS_KEY_ID": "k", "R2_SECRET_ACCESS_KEY": "s"})
        assert isinstance(select_storage(str(tmp_path)), R2Backend)
    finally:
        for k in keys:
            os.environ.pop(k, None)
            if saved[k] is not None:
                os.environ[k] = saved[k]


# -- plain-asserts fallback (no pytest) --------------------------------------
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
    print(f"ALL {passed} FRAMEWORK TESTS PASS")


if __name__ == "__main__":
    _run_plain()
