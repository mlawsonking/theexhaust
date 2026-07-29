"""C1 (signal side) — CMS Payroll-Based Journal Daily Nurse Staffing.

The staffing half of SPEC-01 §2 C1. `cms_deficiencies.py` archives the harm-deficiency ground
truth; this archives the daily nurse-staffing hours that the Hospital/Care Distress retrocast
(BUILD-05) reads *before* those deficiencies. Both are keyed on the CCN — `PROVNUM` here,
"CMS Certification Number (CCN)" there — so the join needs no semantic matching.

Source, re-verified live 2026-07-29 (standing order — research §5 last checked it 2026-07-11):
  catalog   https://data.cms.gov/data.json  (DCAT; the MAIN CMS catalog, *not* /provider-data/,
            which carries only staffing ratings — the raw PBJ files are not published there)
  dataset   "Payroll Based Journal Daily Nurse Staffing", id 7e0d53ba-8f02-4c66-98a5-14a1c997c50d
  cadence   accrualPeriodicity R/P3M (quarterly); temporal 2017-01-01/2026-03-31
  inventory 37 CSV releases, 2017Q1 .. 2026Q1, one file per quarter, all still downloadable
  latest    PBJ_dailynursestaffing_CY2026Q1.csv, 234,273,667 bytes, 33 columns, daily rows per CCN
  licence   https://www.usa.gov/government-works (public domain), no auth, no ToS gate

**Why this is a fleet, not a single-file Collector.** Unlike the deficiencies CSV — one file that
CMS overwrites in place — PBJ publishes a *separate file per quarter* and retains every one. The
SPEC-01 §3 obligation is that each release keeps its own manifest entry, so quarters are archived
as distinct units under `raw/cms-pbj/<QUARTER>/...` and are never concatenated: the retrocast needs
the release boundary intact, and a revision to one quarter must not disturb another.

**Politeness (SPEC-01 §4).** A quarterly 234 MB file must not be re-downloaded on every weekly
probe. Change is detected first from the catalog's own release URL — CMS embeds a per-release UUID
in the path, so a republish yields a new URL — cross-checked with a HEAD `Last-Modified`. Only a
release that looks genuinely new is fetched; the content hash is then the second line of defence.

    python -m collectors.cms_pbj --verify [--quarters N | --all] [--max-bytes N]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

import zstandard as zstd

from .framework import (DEFAULT_UA, POLITE_PAUSE_S, Collector, CsvSchema, LocalFSBackend, git_ref,
                        http_get, load_state, polite_pause, read_manifest, select_storage,
                        sha256_hex, utcnow_iso)

NAME = "cms-pbj"
CATALOG_URL = "https://data.cms.gov/data.json"
DATASET_TITLE = "Payroll Based Journal Daily Nurse Staffing"
DATASET_ID = "7e0d53ba-8f02-4c66-98a5-14a1c997c50d"   # cross-check only; the title is the selector

# Required columns keyed on the real CSV header (verified 2026-07-29). PROVNUM is the CCN the
# retrocast joins on; the Hrs_* triplets split each role into total/employee/contractor.
# Missing or renamed any of these -> schema drift -> quarantine + alarm, never a silent store.
REQUIRED = [
    "PROVNUM",        # CMS Certification Number (the hard join key to cms-deficiencies)
    "PROVNAME",
    "STATE",
    "CY_Qtr",         # e.g. "2026Q1" — the release the row belongs to
    "WorkDate",       # e.g. "20260101" — daily granularity
    "MDScensus",      # residents, the denominator for hours-per-resident-day
    "Hrs_RN",
    "Hrs_LPN",
    "Hrs_CNA",
]

# A quarter is ~1.28M daily rows across ~15k facilities. The floor catches a truncated or
# error-page payload; the band (vs this quarter's own prior row count, when a release is revised)
# catches a revision that loses a large share of its rows.
SCHEMA = CsvSchema(REQUIRED, row_floor=200_000, band=(0.5, 3.0))

DEFAULT_QUARTERS = 1          # the current release only; a backfill is a deliberate, separate act


# --------------------------------------------------------------------------- release discovery
def _quarter_from_url(url: str) -> str | None:
    """PBJ filenames changed convention twice (CY2026Q1 · cy_2020q4 · PBJ_Nurse_2019_Q1_xxxx ·
    PBJ_Nurse_Q2_2020_xxxx), and some legacy releases are named only by an opaque id."""
    for rx in (r"CY(\d{4})Q(\d)", r"cy_(\d{4})q(\d)", r"(\d{4})_Q(\d)", r"_Q(\d)_(\d{4})"):
        m = re.search(rx, url, re.I)
        if m:
            a, b = m.group(1), m.group(2)
            return f"{a}Q{b}" if len(a) == 4 else f"{b}Q{a}"
    return None


def _quarter_from_title(title: str) -> str | None:
    """Distribution titles end in a date inside the quarter — sometimes its first day
    ("... : 2026-01-01"), sometimes its last ("... : 2020-12-31"). The calendar quarter of that
    date is correct either way, and was verified to agree with every parseable filename."""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})\s*$", (title or "").strip())
    if not m:
        return None
    year, month = int(m.group(1)), int(m.group(2))
    return f"{year}Q{(month - 1) // 3 + 1}"


def _quarter_sort_key(q: str):
    y, _, n = q.partition("Q")
    return (int(y), int(n))


def resolve_releases(fetch=http_get) -> list:
    """-> [{quarter, url, title}], NEWEST FIRST, from the CMS DCAT catalog.

    Raises if the dataset is absent or yields no CSV release: a vanished source is a STOP-and-gate
    condition (SPEC-01 §4.5 / BUILD-PROTOCOL §3), never something to paper over with a substitute.
    """
    _s, _h, body = fetch(CATALOG_URL, timeout=240)
    catalog = json.loads(body)
    datasets = catalog.get("dataset", catalog) if isinstance(catalog, dict) else catalog
    ds = next((d for d in datasets if isinstance(d, dict) and d.get("title") == DATASET_TITLE), None)
    if ds is None:
        raise RuntimeError(f"dataset {DATASET_TITLE!r} not found in {CATALOG_URL} "
                           f"(source moved or retired — STOP and file a gate, do not substitute)")
    out, seen = [], {}
    for dist in ds.get("distribution") or []:
        url = dist.get("downloadURL")
        if not url or (dist.get("format") or "").upper() != "CSV":
            continue                        # the API twin of each release is not an archivable file
        title = dist.get("title") or ""
        quarter = _quarter_from_url(url) or _quarter_from_title(title)
        if not quarter:
            continue                        # unidentifiable release: skip rather than mis-file it
        if quarter in seen:                 # two files claiming one quarter is ambiguity, not data
            seen[quarter].setdefault("duplicates", []).append(url)
            continue
        rec = {"quarter": quarter, "url": url, "title": title}
        seen[quarter] = rec
        out.append(rec)
    if not out:
        raise RuntimeError(f"{DATASET_TITLE!r} exposes no CSV release (shape drifted — STOP + gate)")
    out.sort(key=lambda r: _quarter_sort_key(r["quarter"]), reverse=True)
    return out


def head_last_modified(url: str, timeout: int = 60) -> str:
    """Cheap change signal. Returns "" on any failure — this is an optimisation, never a gate:
    a missing Last-Modified must fall through to a real fetch, not skip a release."""
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": DEFAULT_UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.headers.get("Last-Modified") or ""
    except Exception:
        return ""


# --------------------------------------------------------------------------- archive one release
def _update_manifest(storage, datepath, rel, fname, full_hash, rows, ref="", band="ok"):
    mkey = f"raw/{datepath}/manifest.json"
    man = read_manifest(storage, mkey) or {
        "collector": NAME, "quarter": rel["quarter"], "dataset_id": DATASET_ID,
        "date": datepath.split("/", 2)[-1], "git_ref": ref,
        "schema_required": SCHEMA.required_columns, "files": [],
    }
    man["files"].append({
        "file": fname, "sha256": full_hash, "rows": rows, "volume_band": band,
        "source_url": rel["url"], "release_title": rel.get("title", ""),
        "stored_at": utcnow_iso(),
    })
    storage.put(mkey, json.dumps(man, indent=2).encode())


def _quarantine(rec, kind, extra=None):
    """Per-quarter quarantine + fail streak; 3 consecutive failures pause that quarter and ask for
    one gate (SPEC-03 §2) rather than alarming on every probe forever."""
    streak = rec.get("fail_streak", 0) + 1
    rec.update(last_run=utcnow_iso(), last_action=kind, fail_streak=streak, **(extra or {}))
    if streak >= 3:
        rec.update(paused=True)
    return streak


def archive_release(storage, rel, dt, node, *, fetch=http_get, max_bytes=None, ref="",
                    check_head=True, head_fn=None):
    """One quarterly release -> immutable snapshot. Returns a per-quarter result dict."""
    q = rel["quarter"]
    rec = node["quarters"].setdefault(q, {})
    if rec.get("paused"):                    # cleared only by an operator decision on the gate
        return {"quarter": q, "action": "paused"}

    # 1) Cheap change detection BEFORE moving 234 MB (SPEC-01 §4: cache, don't impair).
    #    The skip requires POSITIVE evidence of sameness: the same release URL *and* a matching
    #    non-empty Last-Modified. Absence of a signal is not evidence — SPEC-01 §2 C1 says CMS
    #    OVERWRITES revisions, so treating "no Last-Modified" as unchanged would silently lose the
    #    exact event this collector exists to catch. No signal => fetch and let the hash decide.
    last_mod = (head_fn or head_last_modified)(rel["url"]) if check_head else ""
    if (rec.get("source_url") == rel["url"] and rec.get("last_hash")
            and last_mod and last_mod == rec.get("last_modified")):
        rec.update(last_success=utcnow_iso(), last_action="unchanged", fail_streak=0)
        return {"quarter": q, "action": "unchanged", "reason": "same url and last-modified"}

    # 2) Fetch. Any transport error / non-200 -> quarantine + alarm, never a silent skip.
    try:
        status, _headers, raw = fetch(rel["url"], max_bytes=max_bytes, timeout=900)
    except Exception as e:
        _quarantine(rec, "quarantined-fetch", {"last_error": f"{type(e).__name__}: {e}"})
        return {"quarter": q, "action": "quarantined", "alarm": True, "error": str(e)}
    if status != 200 or not raw:
        if raw:                              # keep the block/notice body — 403-ladder forensics
            storage.put(f"quarantine/{NAME}/{q}/{dt:%Y%m%d}-{sha256_hex(raw)[:12]}.csv", raw)
        _quarantine(rec, "quarantined-fetch", {"last_status": status})
        return {"quarter": q, "action": "quarantined", "alarm": True, "status": status}

    full_hash = sha256_hex(raw)
    h12 = full_hash[:12]
    if rec.get("last_hash") == full_hash:    # republished at a new URL but byte-identical
        rec.update(last_success=utcnow_iso(), last_action="unchanged", source_url=rel["url"],
                   last_modified=last_mod, fail_streak=0)
        return {"quarter": q, "action": "unchanged", "hash": h12, "reason": "identical bytes"}

    # 3) Validate before storing. A drifted release is quarantined, and `raw/` stays clean.
    v = SCHEMA.validate(raw, rec.get("rows"))
    datepath = f"{NAME}/{q}/{dt:%Y}/{dt:%m}/{dt:%d}"
    fname = f"{dt:%H%M}-{h12}.csv.zst"
    if not v["ok"]:
        if rec.get("last_quarantine_hash") == full_hash:      # anti-storm (SPEC-03 §4)
            rec.update(last_run=utcnow_iso(), last_action="quarantined-dup")
            return {"quarter": q, "action": "quarantined-dup", "missing": v["missing"], "alarm": False}
        storage.put(f"quarantine/{datepath}/{fname}",
                    zstd.ZstdCompressor(level=10).compress(raw))
        _quarantine(rec, "quarantined-drift", {"drift_missing": v["missing"],
                                               "last_quarantine_hash": full_hash})
        return {"quarter": q, "action": "quarantined", "missing": v["missing"], "rows": v["rows"],
                "alarm": True}

    blob = zstd.ZstdCompressor(level=10).compress(raw)
    storage.put(f"raw/{datepath}/{fname}", blob)
    band = "extreme" if v["extreme"] else ("anomaly" if v["anomaly"] else "ok")
    _update_manifest(storage, datepath, rel, fname, full_hash, v["rows"], ref=ref, band=band)
    rec.update(last_success=utcnow_iso(), last_action="stored", last_hash=full_hash,
               source_url=rel["url"], last_modified=last_mod, rows=v["rows"],
               raw_bytes=len(raw), stored_bytes=len(blob), volume_band=band,
               key=f"raw/{datepath}/{fname}", release_title=rel.get("title", ""), fail_streak=0)
    return {"quarter": q, "action": "stored", "hash": h12, "rows": v["rows"], "bytes": len(raw),
            "stored": len(blob), "volume_band": band, "alarm": v["extreme"]}


# --------------------------------------------------------------------------- fleet
def run_fleet(storage, health_path=None, heartbeat_url=None, repo_root=".", fetch=http_get,
              quarters=DEFAULT_QUARTERS, only=None, max_bytes=None, pause_s=None, sleeper=None,
              check_head=True, head_fn=None):
    """Archive the newest `quarters` releases (default 1 = the current one).

    `quarters=None` means EVERY published release — the full-history backfill BUILD-05 needs
    (37 releases ~ 8.7 GB raw, ~1.1 GB stored as measured 2026-07-29). It is off by default because
    the floor doctrine bans ambient backfills: history is stable and re-fetchable, whereas the
    current release is the perishable thing this collector exists to never miss.
    """
    published = resolve_releases(fetch=fetch)      # resolved ONCE: the catalog is 3 MB
    releases = published
    if only:
        want = {q.strip().upper() for q in (only if isinstance(only, (list, set)) else [only])}
        releases = [r for r in published if r["quarter"].upper() in want]
    elif quarters is not None:
        releases = published[:max(int(quarters), 0)]

    health = load_state(health_path)
    node = health.setdefault("collectors", {}).setdefault(NAME, {})
    node.setdefault("quarters", {})
    dt = datetime.now(timezone.utc)
    ref = git_ref(repo_root)
    results = []
    for i, rel in enumerate(releases):
        if i:                                # SPEC-01 §4.1 rate-limit + jitter between requests
            polite_pause(POLITE_PAUSE_S if pause_s is None else pause_s, sleeper=sleeper)
        try:
            results.append(archive_release(storage, rel, dt, node, fetch=fetch, max_bytes=max_bytes,
                                           ref=ref, check_head=check_head, head_fn=head_fn))
        except Exception as e:               # one bad release must not end the run
            node["quarters"].setdefault(rel["quarter"], {}).update(
                last_run=utcnow_iso(), last_action="error", last_error=f"{type(e).__name__}: {e}")
            results.append({"quarter": rel["quarter"], "action": "error", "alarm": True,
                            "error": str(e)})

    stored = sum(1 for r in results if r["action"] == "stored")
    quarantined = sum(1 for r in results if r["action"] in ("quarantined", "error"))
    paused = [r["quarter"] for r in results if r["action"] == "paused"]
    extreme = [r["quarter"] for r in results if r.get("volume_band") == "extreme"]
    # `published_releases` is the whole inventory CMS currently exposes; `release_count` is what
    # this run looked at. The gap between them is the un-backfilled history, visible in state
    # rather than discovered later by a retrocast that expected it to be there.
    node.update(last_action=("quarantined" if quarantined else ("stored" if stored else "unchanged")),
                git_ref=ref, dataset_id=DATASET_ID, published_releases=len(published),
                release_count=len(releases), quarantined=quarantined,
                paused_quarters=paused, volume_extreme=extreme,
                latest_published_quarter=(published[0]["quarter"] if published else None))
    node.update(**({"last_success": utcnow_iso()} if not quarantined else {"last_run": utcnow_iso()}))
    gate = _fleet_gate(node)
    if health_path:
        health["generated"] = utcnow_iso()
        os.makedirs(os.path.dirname(health_path) or ".", exist_ok=True)
        json.dump(health, open(health_path, "w", encoding="utf-8"), indent=2)
    empty = not releases
    hb = _heartbeat(heartbeat_url, ok=(quarantined == 0 and not empty))
    return {"releases": len(releases), "stored": stored,
            "unchanged": sum(1 for r in results if r["action"] == "unchanged"),
            "quarantined": quarantined, "paused": paused, "empty": empty,
            "volume_extreme": extreme, "needs_gate": gate, "heartbeat": hb, "results": results}


def _fleet_gate(node):
    """Surface a paused quarter as a node-level `needs_gate` so weekly.file_collector_gates files
    exactly one source gate (W-005c/F05). The value lands in a FILENAME, so keep it slug-safe."""
    paused = sorted(k for k, v in (node.get("quarters") or {}).items() if v.get("paused"))
    if paused:
        units = "-".join(re.sub(r"[^A-Za-z0-9._-]+", "-", p) for p in paused)
        node["needs_gate"] = f"{NAME}-fetch-3x-{units}"
    else:
        node.pop("needs_gate", None)
    return node.get("needs_gate")


def _heartbeat(url, ok=True):
    """Ping the logical `cms-pbj` healthcheck (SPEC-02 §1). Inert if unset; any quarantine -> /fail.
    Never raises into the caller."""
    if not url:
        return "unset"
    target = url if ok else url.rstrip("/") + "/fail"
    try:
        http_get(target, timeout=15)
        return "pinged"
    except Exception as e:
        return f"err:{type(e).__name__}"


# Kept so the module still satisfies the single-collector build contract other tooling may expect
# (report/fleetgreen read the health record, not this, but the symmetry is cheap).
def build(storage=None, health_path=None, heartbeat_url=None, repo_root=".", local_root=None):
    if storage is None:
        storage = LocalFSBackend(local_root or "local-archive")
    return Collector(NAME, storage, SCHEMA, ext="csv", health_path=health_path,
                     heartbeat_url=heartbeat_url, repo_root=repo_root)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="dev run against a local backend")
    ap.add_argument("--local-root", default="local-archive")
    ap.add_argument("--quarters", type=int, default=DEFAULT_QUARTERS,
                    help="how many newest releases to archive (default 1)")
    ap.add_argument("--all", action="store_true",
                    help="EVERY published release — the BUILD-05 backfill (~8.7 GB raw); deliberate only")
    ap.add_argument("--only", default=None, help="comma-separated quarters, e.g. 2026Q1,2025Q4")
    ap.add_argument("--max-bytes", type=int, default=None, help="cap the stream read (verification)")
    ap.add_argument("--no-head", action="store_true", help="skip the HEAD change probe")
    args = ap.parse_args()

    hp = (os.path.join(args.local_root, "HEALTH.json") if args.verify
          else os.path.join("ops", "state", "health", f"{NAME}.json"))
    storage = LocalFSBackend(args.local_root) if args.verify else select_storage(args.local_root)
    heartbeat = None if args.verify else os.environ.get("HC_CMS_PBJ")
    res = run_fleet(storage, health_path=hp, heartbeat_url=heartbeat,
                    quarters=(None if args.all else args.quarters),
                    only=(args.only.split(",") if args.only else None),
                    max_bytes=args.max_bytes, check_head=not args.no_head)
    print(json.dumps({k: v for k, v in res.items() if k != "results"}, indent=2))
    for r in res["results"]:
        print("  ", r)
    # SPEC-02 §1 job contract: quarantine / empty fleet / extreme volume -> exit nonzero, loudly.
    raise SystemExit(2 if (res["quarantined"] or res["empty"] or res["volume_extreme"]) else 0)
