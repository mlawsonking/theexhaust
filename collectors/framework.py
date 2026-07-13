"""Collector framework — SPEC-01 contract, runtime-agnostic.

Storage is pluggable: LocalFSBackend (dev + the operator-box 403-ladder path) now;
R2Backend (production) once the BUILD-00 R2 credentials exist. Nothing here makes a
metered LLM call, ever. Every collector: fetch -> hash -> dedupe -> schema-validate ->
compress(.zst) -> store immutable raw + per-day manifest -> update HEALTH -> heartbeat
on validated store; quarantine + alarm on schema drift.
"""
from __future__ import annotations

import abc
import csv
import hashlib
import io
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone

import zstandard as zstd

DEFAULT_UA = (
    "TheExhaust/0.1 (+https://theexhaust.org; archival public-interest collector; "
    "contact: ops@theexhaust.org)"
)


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    return utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def git_ref(repo_root: str) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", repo_root, "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL,
        )
        return out.strip()[:12]
    except Exception:
        return "unknown"


def http_get(url: str, max_bytes: int | None = None, headers: dict | None = None, timeout: int = 300):
    """GET url. max_bytes caps the STREAM READ (not an HTTP Range — some sources ignore Range).
    Returns (status, headers_dict, body_bytes)."""
    h = {"User-Agent": DEFAULT_UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read(max_bytes) if max_bytes else r.read()
        return r.status, dict(r.headers), body


# --------------------------------------------------------------------------- storage
class StorageBackend(abc.ABC):
    @abc.abstractmethod
    def put(self, key: str, data: bytes) -> None: ...
    @abc.abstractmethod
    def get(self, key: str) -> bytes | None: ...
    @abc.abstractmethod
    def exists(self, key: str) -> bool: ...


class LocalFSBackend(StorageBackend):
    """Filesystem backend. Used for dev/verification and the operator-box fallback
    (SPEC-01 §4.5). Also the local half of a future R2+local mirror."""

    def __init__(self, root: str):
        self.root = root

    def _p(self, key: str) -> str:
        return os.path.join(self.root, key.replace("/", os.sep))

    def put(self, key, data):
        p = self._p(key)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)

    def get(self, key):
        p = self._p(key)
        if not os.path.exists(p):
            return None
        with open(p, "rb") as f:
            return f.read()

    def exists(self, key):
        return os.path.exists(self._p(key))


class R2Backend(StorageBackend):
    """Cloudflare R2 (S3-compatible). boto3 is imported lazily so this module loads on a
    box without boto3 (pre-BUILD-01-deploy). Verified end-to-end once the operator's R2
    credentials exist (BUILD-00 errand); never serve from raw r2.dev (egress covenant)."""

    def __init__(self, bucket: str, endpoint_url: str, access_key: str, secret_key: str):
        import boto3  # lazy
        self.bucket = bucket
        self.s3 = boto3.client(
            "s3", endpoint_url=endpoint_url,
            aws_access_key_id=access_key, aws_secret_access_key=secret_key,
            region_name="auto",
        )

    def put(self, key, data):
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data)

    def get(self, key):
        try:
            return self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        except Exception:
            return None

    def exists(self, key):
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False


# --------------------------------------------------------------------------- schema
class CsvSchema:
    """Schema contract for a CSV corpus (SPEC-01 §5). Missing/renamed required column ->
    drift (quarantine). Row count out of band vs trailing median -> anomaly (store + flag)."""

    def __init__(self, required_columns, row_floor: int = 1, band=(0.5, 3.0)):
        self.required_columns = list(required_columns)
        self.row_floor = row_floor
        self.band = band

    def validate(self, raw: bytes, trailing_median: int | None = None):
        text = raw.decode("utf-8-sig", errors="replace")
        reader = csv.reader(io.StringIO(text))
        try:
            header = next(reader)
        except StopIteration:
            return {"ok": False, "rows": 0, "missing": ["<no header>"], "anomaly": False}
        cols = {c.strip().strip('"') for c in header}
        missing = [c for c in self.required_columns if c not in cols]
        rows = sum(1 for _ in reader)  # last row may be partial under a read-cap (tolerated)
        drift = len(missing) > 0
        anomaly = extreme = False
        if not drift:
            if rows < self.row_floor:
                anomaly = True
            if trailing_median:
                lo, hi = self.band
                if rows < lo * trailing_median or rows > hi * trailing_median:
                    anomaly = True
                if rows < 0.25 * trailing_median or rows > 5 * trailing_median:  # SPEC-03 §2 alarm tier
                    anomaly = extreme = True
        return {"ok": not drift, "rows": rows, "missing": missing, "anomaly": anomaly, "extreme": extreme}


# --------------------------------------------------------------------------- collector
class ZipTabSchema:
    """Schema contract for a TAB-delimited, header-less flat file inside a ZIP (the NHTSA ODI
    format). Wrong field count in the primary member -> drift (quarantine). Row count out of band
    -> anomaly. Duck-typed like CsvSchema (validate + required_columns)."""

    def __init__(self, expected_fields, member_suffix=".txt", row_floor=1, band=(0.5, 3.0), delimiter="\t"):
        self.expected_fields = expected_fields
        self.member_suffix = member_suffix.lower()
        self.row_floor = row_floor
        self.band = band
        self.delimiter = delimiter.encode()
        self.required_columns = [f"<{expected_fields} tab-delimited fields in *{member_suffix}>"]

    def validate(self, raw: bytes, trailing_median: int | None = None):
        import io
        import zipfile
        try:
            zf = zipfile.ZipFile(io.BytesIO(raw))
        except Exception:
            return {"ok": False, "rows": 0, "missing": ["<not-a-valid-zip>"], "anomaly": False, "extreme": False}
        members = [n for n in zf.namelist() if n.lower().endswith(self.member_suffix)]
        if not members:
            return {"ok": False, "rows": 0, "missing": [f"<no {self.member_suffix} member>"],
                    "anomaly": False, "extreme": False}
        rows, fields = 0, None
        with zf.open(members[0]) as fh:
            for i, line in enumerate(fh):
                if i == 0:
                    fields = line.count(self.delimiter) + 1
                rows += 1
        drift = fields != self.expected_fields
        anomaly = extreme = False
        if not drift:
            if rows < self.row_floor:
                anomaly = True
            if trailing_median:
                lo, hi = self.band
                if rows < lo * trailing_median or rows > hi * trailing_median:
                    anomaly = True
                if rows < 0.25 * trailing_median or rows > 5 * trailing_median:
                    anomaly = extreme = True
        return {"ok": not drift, "rows": rows,
                "missing": ([f"field-count {fields}!={self.expected_fields}"] if drift else []),
                "anomaly": anomaly, "extreme": extreme}


class Collector:
    """One perishable corpus -> immutable snapshots. See module docstring for the flow."""

    def __init__(self, name, storage: StorageBackend, schema, ext="csv", recompress=True,
                 health_path: str | None = None, heartbeat_url: str | None = None, repo_root="."):
        self.name = name
        self.storage = storage
        self.schema = schema
        self.ext = ext
        self.recompress = recompress  # False for already-compressed sources (zip): store as-is
        self.health_path = health_path
        self.heartbeat_url = heartbeat_url
        self.repo_root = repo_root

    # -- state ------------------------------------------------------------
    def _load_health(self) -> dict:
        if self.health_path and os.path.exists(self.health_path):
            with open(self.health_path) as f:
                return json.load(f)
        return {"_doc": "collector heartbeat/health state (SPEC-03 §1)", "collectors": {}}

    def _save_health(self, h: dict):
        if not self.health_path:
            return
        h["generated"] = utcnow_iso()
        with open(self.health_path, "w") as f:
            json.dump(h, f, indent=2)

    def _heartbeat(self, ok=True) -> str:
        if not self.heartbeat_url:
            return "unset(pre-BUILD-00)"
        url = self.heartbeat_url if ok else self.heartbeat_url.rstrip("/") + "/fail"
        try:
            http_get(url, timeout=15)
            return "pinged"
        except Exception as e:
            return f"err:{type(e).__name__}"

    def _update_manifest(self, datepath: str, fname: str, full_hash: str, rows: int, source_url: str, band: str = "ok"):
        mkey = f"raw/{datepath}/manifest.json"
        cur = self.storage.get(mkey)
        man = json.loads(cur) if cur else {
            "collector": self.name,
            "date": datepath.split("/", 1)[1],
            "git_ref": git_ref(self.repo_root),
            "schema_required": self.schema.required_columns,
            "files": [],
        }
        man["files"].append({
            "file": fname, "sha256": full_hash, "rows": rows, "volume_band": band,
            "source_url": source_url, "stored_at": utcnow_iso(),
        })
        self.storage.put(mkey, json.dumps(man, indent=2).encode())

    # -- run --------------------------------------------------------------
    def run(self, fetch, dt: datetime | None = None, max_bytes: int | None = None) -> dict:
        """fetch(max_bytes) -> (status, headers_dict, raw_bytes, source_url)."""
        dt = dt or utcnow()
        status, headers, raw, source_url = fetch(max_bytes=max_bytes)
        full_hash = sha256_hex(raw)
        h12 = full_hash[:12]
        health = self._load_health()
        rec = health["collectors"].get(self.name, {})

        # dedupe (also the cron-drift defense): unchanged source is a healthy run -> reset drift/pause
        if rec.get("last_hash") == full_hash:
            rec.update(last_success=utcnow_iso(), last_action="unchanged", source_url=source_url,
                       drift_streak=0, paused=False)
            health["collectors"][self.name] = rec
            self._save_health(health)
            return {"action": "unchanged", "hash": h12, "heartbeat": self._heartbeat(True)}

        median = rec.get("rows_median")
        v = self.schema.validate(raw, median)
        datepath = f"{self.name}/{dt:%Y}/{dt:%m}/{dt:%d}"
        if self.recompress:
            blob = zstd.ZstdCompressor(level=10).compress(raw)
            stored_ext = f"{self.ext}.zst"
        else:
            blob = raw  # already-compressed (e.g. zip): store immutable, don't re-compress
            stored_ext = self.ext
        fname = f"{dt:%H%M}-{h12}.{stored_ext}"

        if not v["ok"]:  # schema drift -> quarantine + alarm, never pollute raw/
            # Same drifted payload recurring -> don't re-store, don't re-alarm (anti-storm, SPEC-03 §4).
            if rec.get("last_quarantine_hash") == full_hash:
                rec.update(last_run=utcnow_iso(), last_action="quarantined-dup")
                health["collectors"][self.name] = rec
                self._save_health(health)
                return {"action": "quarantined-dup", "missing": v["missing"], "rows": v["rows"],
                        "alarm": False, "heartbeat": "withheld(drift)"}
            streak = rec.get("drift_streak", 0) + 1
            qkey = f"quarantine/{datepath}/{fname}"
            self.storage.put(qkey, blob)
            rec.update(last_run=utcnow_iso(), last_action="quarantined-drift", drift_missing=v["missing"],
                       drift_streak=streak, last_quarantine_hash=full_hash)
            if streak >= 3:  # SPEC-03 §2: auto-pause + gate item after 3 consecutive drifts
                rec.update(paused=True, needs_gate="schema-drift-3x")
            health["collectors"][self.name] = rec
            self._save_health(health)
            return {"action": "quarantined", "missing": v["missing"], "rows": v["rows"], "key": qkey,
                    "alarm": True, "drift_streak": streak, "paused": rec.get("paused", False),
                    "heartbeat": "withheld(drift)"}

        rawkey = f"raw/{datepath}/{fname}"
        self.storage.put(rawkey, blob)
        band = "extreme" if v["extreme"] else ("anomaly" if v["anomaly"] else "ok")
        self._update_manifest(datepath, fname, full_hash, v["rows"], source_url, band)
        hist = (rec.get("rows_history", []) + [v["rows"]])[-8:]
        rec.update(
            last_success=utcnow_iso(), last_action="stored", last_hash=full_hash,
            rows=v["rows"], rows_history=hist, rows_median=sorted(hist)[len(hist) // 2],
            anomaly=v["anomaly"], volume_band=band, raw_bytes=len(raw), stored_bytes=len(blob),
            key=rawkey, source_url=source_url, drift_streak=0, paused=False,
        )
        health["collectors"][self.name] = rec
        self._save_health(health)
        # Extreme volume (<0.25x / >5x median) still stores (data is data) but ALARMS (SPEC-03 §2).
        return {"action": "stored", "rows": v["rows"], "hash": h12, "key": rawkey,
                "compressed": len(blob), "raw": len(raw), "anomaly": v["anomaly"], "volume_band": band,
                "alarm": v["extreme"], "heartbeat": self._heartbeat(True)}
