"""C5 — CPSC recall listing (consumer-product recall ground truth).

The full CPSC recall listing CSV (22 cols incl. Importers / Manufacturers / Distributors /
"Manufactured In" provenance). Feeds the consumer-product leg of the recalls retrocast and
the factory-provenance enrichment. CPSC edits recalls post-hoc, so snapshot every vintage.

Source: official CPSC bulk CSV, public, no auth, fixed URL. verified 2026-07-13
(HTTP 200; 18 MB; text/csv; 22 cols). Covenant: official bulk download, honest UA,
no scraping gray zone, no circumvention.
"""
from __future__ import annotations

from .framework import Collector, CsvSchema, LocalFSBackend, http_get

NAME = "cpsc-recalls"
CSV_URL = "https://www.cpsc.gov/s3fs-public/recall-data/recalls_recall_listing.csv"

REQUIRED = [
    "Recall Number",
    "Date",
    "Name of product",
    "Hazard Description",
    "Units",
    "Incidents",
    "Importers",
    "Manufacturers",
    "Distributors",
    "Manufactured In",
]

SCHEMA = CsvSchema(REQUIRED, row_floor=1000, band=(0.5, 3.0))


def make_fetch():
    def fetch(max_bytes=None):
        status, headers, body = http_get(CSV_URL, max_bytes=max_bytes, timeout=300)
        return status, headers, body, CSV_URL
    return fetch


def build(storage=None, health_path=None, heartbeat_url=None, repo_root=".", local_root=None):
    if storage is None:
        storage = LocalFSBackend(local_root or "local-archive")
    return Collector(NAME, storage, SCHEMA, ext="csv",
                     health_path=health_path, heartbeat_url=heartbeat_url, repo_root=repo_root)
