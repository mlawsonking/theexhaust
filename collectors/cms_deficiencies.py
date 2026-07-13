"""C1 (ground-truth side) — CMS Nursing Home Health Deficiencies (dataset r5ix-sfxw).

The hard-CCN-keyed harm-deficiency ground truth for the Hospital/Care Distress retrocast
(BUILD-05). CMS OVERWRITES this file each release (the CSV URL embeds the vintage, e.g.
NH_HealthCitations_Jun2026.csv), so we snapshot every vintage immutably.

Source: official CMS Provider Data Catalog, public, no auth. verified 2026-07-13
(HTTP 200; 165 MB CSV; 23 cols incl. CCN / Survey Date / Deficiency Tag / Scope Severity).
Covenant: official bulk download, honest UA, no scraping gray zone, no circumvention.
"""
from __future__ import annotations

import json

from .framework import Collector, CsvSchema, LocalFSBackend, http_get

NAME = "cms-deficiencies"
DATASET_ID = "r5ix-sfxw"
ITEM_URL = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/{id}?show-reference-ids=false"
ITEMS_URL = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items?show-reference-ids=false"

# Required columns keyed on the BULK CSV's display-name header (NOT the datastore API's
# snake_case). Missing/renamed any of these -> schema drift -> quarantine + alarm.
REQUIRED = [
    "CMS Certification Number (CCN)",
    "Provider Name",
    "State",
    "Survey Date",
    "Survey Type",
    "Deficiency Tag Number",
    "Deficiency Category",
    "Scope Severity Code",
]

SCHEMA = CsvSchema(REQUIRED, row_floor=100_000, band=(0.5, 3.0))


def resolve_csv_url() -> str:
    """Resolve the current CSV downloadURL for r5ix-sfxw from the CMS metastore.
    Tries the single-item endpoint, falls back to scanning the items list."""
    try:
        _, _, body = http_get(ITEM_URL.format(id=DATASET_ID), timeout=60)
        item = json.loads(body)
        url = _csv_from_item(item)
        if url:
            return url
    except Exception:
        pass
    _, _, body = http_get(ITEMS_URL, timeout=120)
    for d in json.loads(body):
        if isinstance(d, dict) and d.get("identifier") == DATASET_ID:
            url = _csv_from_item(d)
            if url:
                return url
    raise RuntimeError(f"could not resolve CSV downloadURL for {DATASET_ID}")


def _csv_from_item(item: dict) -> str | None:
    for dist in (item.get("distribution") or []):
        data = dist if "downloadURL" in dist else dist.get("data", {})
        url = data.get("downloadURL")
        mt = (data.get("mediaType") or "").lower()
        if url and (url.lower().endswith(".csv") or "csv" in mt):
            return url
    return None


def make_fetch():
    def fetch(max_bytes=None):
        url = resolve_csv_url()
        status, headers, body = http_get(url, max_bytes=max_bytes, timeout=600)
        return status, headers, body, url
    return fetch


def build(storage=None, health_path=None, heartbeat_url=None, repo_root=".", local_root=None):
    if storage is None:
        storage = LocalFSBackend(local_root or "local-archive")
    return Collector(NAME, storage, SCHEMA, ext="csv",
                     health_path=health_path, heartbeat_url=heartbeat_url, repo_root=repo_root)
