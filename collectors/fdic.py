"""C9 — FDIC BankFind failed-bank list (Bank Stress ground truth).

The failed-bank list (resolution date, cost, city/state, closing code) — the named ground truth
for the (permanently aggregate-only) Bank Stress index's retrocast against prior call-report
drift. Call-report *quarterlies* (the drift signal) are a later expansion; this is the clean,
bounded, fully-public ground-truth leg.

Source: official FDIC BankFind Suite API, public, no auth, JSON. verified 2026-07-13
(HTTP 200; 4,115 failures; RESDATE/COST/PSTALP/CLOSCD present).
"""
from __future__ import annotations

from .framework import Collector, JsonSchema, LocalFSBackend, http_get

NAME = "fdic-failures"
URL = "https://api.fdic.gov/banks/failures?limit=10000&format=json"  # limit > total (4,115) -> all
SCHEMA = JsonSchema("data", ["RESDATE", "COST", "PSTALP", "CLOSCD"], row_floor=3000)


def make_fetch():
    def fetch(max_bytes=None):
        status, headers, body = http_get(URL, max_bytes=max_bytes, timeout=120)
        return status, headers, body, URL
    return fetch


def build(storage=None, health_path=None, heartbeat_url=None, repo_root=".", local_root=None):
    return Collector(NAME, storage or LocalFSBackend(local_root or "local-archive"), SCHEMA,
                     ext="json", health_path=health_path, heartbeat_url=heartbeat_url, repo_root=repo_root)
