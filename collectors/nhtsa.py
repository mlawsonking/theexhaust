"""C4 — NHTSA ODI flat files (the first-retrocast corpus).

Two collectors from one source ecosystem:
- nhtsa-recalls  : FLAT_RCL_POST_2010.zip (29 tab-delimited fields; CAMPNO/MAKETXT/MODELTXT/
                   YEARTXT/COMPNAME/RCLDATE...) — the recall-campaign GROUND TRUTH.
- nhtsa-complaints: FLAT_CMPL.zip (~367 MB; 51 tab-delimited fields; CMPLID/ODINO/MAKETXT/
                   MODELTXT/YEARTXT/CRASH/FIRE/COMPDESC/DATEA/CDESCR...) — the SIGNAL.

Both are the retrocast-of-record (archived flat-file vintages, never live endpoints). Official
NHTSA bulk downloads, public, no auth, TAB-delimited. verified 2026-07-13. Snapshot the raw ZIP
immutably (already compressed -> recompress=False).
"""
from __future__ import annotations

from .framework import Collector, LocalFSBackend, ZipTabSchema, http_get

NAME_RCL = "nhtsa-recalls"
URL_RCL = "https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip"
SCHEMA_RCL = ZipTabSchema(expected_fields=29, member_suffix=".txt", row_floor=10_000)

NAME_CMPL = "nhtsa-complaints"
URL_CMPL = "https://static.nhtsa.gov/odi/ffdd/cmpl/FLAT_CMPL.zip"
SCHEMA_CMPL = ZipTabSchema(expected_fields=51, member_suffix=".txt", row_floor=500_000)


def _fetch(url):
    def fetch(max_bytes=None):
        status, headers, body = http_get(url, max_bytes=max_bytes, timeout=1200)
        return status, headers, body, url
    return fetch


def _build(name, schema):
    def build(storage=None, health_path=None, heartbeat_url=None, repo_root=".", local_root=None):
        return Collector(name, storage or LocalFSBackend(local_root or "local-archive"), schema,
                         ext="zip", recompress=False, health_path=health_path,
                         heartbeat_url=heartbeat_url, repo_root=repo_root)
    return build


build_recalls, make_fetch_recalls = _build(NAME_RCL, SCHEMA_RCL), lambda: _fetch(URL_RCL)
build_complaints, make_fetch_complaints = _build(NAME_CMPL, SCHEMA_CMPL), lambda: _fetch(URL_CMPL)
