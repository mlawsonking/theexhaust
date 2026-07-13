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
    c = _collector(be, tmp_path / "HEALTH.json")
    r = None
    for i in range(1, 4):                                      # 3 distinct drifted payloads
        r = c.run(_fetch(DRIFTED + b"row%d\n" % i))
        assert r["action"] == "quarantined" and r["alarm"] is True
    assert r["drift_streak"] == 3 and r["paused"] is True      # auto-pause on 3rd (SPEC-03 §2)
    dup = c.run(_fetch(DRIFTED + b"row3\n"))                   # identical drifted payload recurs
    assert dup["action"] == "quarantined-dup" and dup["alarm"] is False  # no alarm storm


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


# -- plain-asserts fallback (no pytest) --------------------------------------
def _run_plain():
    import tempfile, pathlib
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            with tempfile.TemporaryDirectory() as d:
                fn(pathlib.Path(d))
            print("ok:", name)
            passed += 1
    print(f"ALL {passed} FRAMEWORK TESTS PASS")


if __name__ == "__main__":
    _run_plain()
