"""C2 — WARN Watch fleet archiver (state layoff-notice ground truth for Shadow Layoffs).

Snapshots each state's PRIMARY WARN (Worker Adjustment and Retraining Notification) source
(collectors/seed_warn.json) to immutable storage, per-state content-hash dedupe, one shared 'warn'
logical heartbeat with per-state detail in HEALTH (SPEC-03 §1, mirrors the ats-boards fleet). WARN
notices are amended/removed silently → perishable; every uncollected day loses the diff.

W-004 steer (WORKPLAN): **store the raw payload ALWAYS**; parse what's parseable (a best-effort
notice count) as manifest metadata — a parse miss is metadata (`parse_ok=false`), NOT a quarantine.
Quarantine is reserved for FETCH failures (transport error / non-200 / block page) — those alarm and
withhold the heartbeat. Parsing is stdlib-only (no new R1 deps): CSV/JSON exactly; XLSX/HTML via
lightweight row counters; PDF/unknown → store raw, count withheld.

Covenant (SPEC-01 §4): honest UA (framework `DEFAULT_UA`), one polite request per state per day,
primary state sources only (aggregators are cross-checks, never sources), no auth/ToS/CAPTCHA
surface (each seed entry is onboarding-verified). 403-ladder: a datacenter-IP 403 → run from the
operator box (step b); a collector-specific block/CAPTCHA → STOP + gate (never evade).

    python -m collectors.warn --verify [--local-root DIR] [--only CA] [--max-bytes N]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin

import zstandard as zstd

from .framework import (LocalFSBackend, git_ref, http_get, select_storage, sha256_hex, utcnow_iso)

# Formats stored as-is (already compressed); everything else is zstd-compressed before store.
_PRECOMPRESSED = {"xlsx", "xls", "pdf", "zip"}


def load_seed(path):
    return json.load(open(path, encoding="utf-8")).get("states", [])


# --------------------------------------------------------------------------- source resolution
def resolve_data_url(entry, *, fetch=http_get):
    """Return the concrete data URL to fetch. Direct `data_url` wins; otherwise a `landing_url` +
    `link_regex` resolves the current link off the landing page (states rotate yearly filenames —
    mirrors cms_deficiencies.resolve_csv_url). Raises if a landing resolve finds nothing."""
    if entry.get("data_url"):
        return entry["data_url"]
    landing, rx = entry.get("landing_url"), entry.get("link_regex")
    if not (landing and rx):
        raise ValueError(f"seed entry for {entry.get('state')} has neither data_url nor landing_url+link_regex")
    _s, _h, body = fetch(landing, timeout=120)
    m = re.search(rx, body.decode("utf-8", errors="replace"))
    if not m:
        raise RuntimeError(f"{entry.get('state')}: link_regex matched nothing on {landing}")
    return urljoin(landing, m.group(m.lastindex or 0))


# --------------------------------------------------------------------------- best-effort parsing
class _RowTdCounter(HTMLParser):
    """Counts HTML table rows that hold at least one <td> (i.e. data rows, not <th> header rows)."""
    def __init__(self):
        super().__init__()
        self.rows = 0
        self._in_tr = False
        self._td_in_tr = False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._in_tr, self._td_in_tr = True, False
        elif tag == "td" and self._in_tr:
            self._td_in_tr = True

    def handle_endtag(self, tag):
        if tag == "tr" and self._in_tr:
            if self._td_in_tr:
                self.rows += 1
            self._in_tr = False


def _count_xlsx_rows(raw: bytes):
    """Row count of the densest worksheet in an .xlsx (a zip of XML), stdlib-only. Best effort."""
    zf = zipfile.ZipFile(io.BytesIO(raw))
    sheets = [n for n in zf.namelist() if n.startswith("xl/worksheets/") and n.endswith(".xml")]
    if not sheets:
        raise ValueError("no worksheets")
    best = max(zf.read(n).count(b"<row ") for n in sheets)
    return max(best - 1, 0)  # minus header row


def parse_count(fmt: str, raw: bytes):
    """(parsed_rows, parse_ok). Never raises — a parse miss is metadata, not a failure."""
    fmt = (fmt or "").lower()
    try:
        if fmt in ("csv", "socrata-csv", "tsv"):
            import csv
            delim = "\t" if fmt == "tsv" else ","
            rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig", errors="replace")), delimiter=delim))
            return (max(len(rows) - 1, 0), True) if rows else (0, True)
        if fmt in ("json", "socrata-json"):
            j = json.loads(raw)
            if isinstance(j, list):
                return len(j), True
            for k in ("data", "results", "records", "value"):
                if isinstance(j.get(k), list):
                    return len(j[k]), True
            return None, False
        if fmt == "xlsx":
            return _count_xlsx_rows(raw), True
        if fmt in ("html", "html-table"):
            p = _RowTdCounter()
            p.feed(raw.decode("utf-8", errors="replace"))
            return p.rows, True
    except Exception:
        return None, False
    return None, False  # xls / pdf / unknown → store raw, no count


# --------------------------------------------------------------------------- archive one state
def _ext_for(fmt: str) -> str:
    fmt = (fmt or "").lower()
    return {"socrata-csv": "csv", "socrata-json": "json", "html-table": "html"}.get(fmt, fmt or "bin")


def _update_manifest(storage, datepath, entry, fname, full_hash, parsed_rows, parse_ok, source_url, ref=""):
    mkey = f"raw/{datepath}/manifest.json"
    cur = storage.get(mkey)
    man = json.loads(cur) if cur else {
        "collector": f"warn-{entry['state'].lower()}", "state": entry["state"],
        "agency": entry.get("agency", ""), "date": datepath.split("/", 2)[-1],
        "git_ref": ref,                      # SPEC-01 §3: manifests carry the collector git ref
        "files": [],
    }
    man["files"].append({
        "file": fname, "sha256": full_hash, "format": entry.get("format", ""),
        "parsed_rows": parsed_rows, "parse_ok": parse_ok, "source_url": source_url,
        "stored_at": utcnow_iso(),
    })
    storage.put(mkey, json.dumps(man, indent=2).encode())


def archive_state(storage, entry, dt, node, *, fetch=http_get, max_bytes=None, ref=""):
    state = entry["state"]
    rec = node["states"].setdefault(state, {})
    fmt = entry.get("format", "")
    # 1) resolve + fetch. Any transport error / non-200 → quarantine (alarm), never silent.
    try:
        url = resolve_data_url(entry, fetch=fetch)
        url = url.replace("{year}", f"{dt:%Y}")  # e.g. FL's ?year={year} → the current UTC year
        status, _headers, raw = fetch(url, max_bytes=max_bytes, timeout=300)
    except Exception as e:
        rec.update(last_run=utcnow_iso(), last_action="quarantined-fetch", last_error=f"{type(e).__name__}: {e}")
        return {"state": state, "action": "quarantined", "alarm": True, "error": str(e)}
    if status != 200 or not raw:
        # keep the non-200 body for forensics (it may be a block/notice page) — quarantine, don't pollute raw/
        if raw:
            storage.put(f"quarantine/warn/{state}/{dt:%Y%m%d}-{sha256_hex(raw)[:12]}.{_ext_for(fmt)}", raw)
        rec.update(last_run=utcnow_iso(), last_action="quarantined-fetch", last_status=status)
        return {"state": state, "action": "quarantined", "alarm": True, "status": status}

    full_hash = sha256_hex(raw)
    h12 = full_hash[:12]
    if rec.get("last_hash") == full_hash:  # per-state dedupe (also the cron-drift defense)
        rec.update(last_success=utcnow_iso(), last_action="unchanged", source_url=url)
        return {"state": state, "action": "unchanged", "hash": h12}

    # 2) STORE RAW ALWAYS (the archive is the deliverable). Compress unless already-compressed.
    ext = _ext_for(fmt)
    if fmt in _PRECOMPRESSED:
        blob, stored_ext = raw, ext
    else:
        blob, stored_ext = zstd.ZstdCompressor(level=10).compress(raw), f"{ext}.zst"
    datepath = f"warn/{state}/{dt:%Y}/{dt:%m}/{dt:%d}"
    fname = f"{dt:%H%M}-{h12}.{stored_ext}"
    storage.put(f"raw/{datepath}/{fname}", blob)

    # 3) parse what's parseable → manifest metadata (never gates)
    parsed_rows, parse_ok = parse_count(fmt, raw)
    _update_manifest(storage, datepath, entry, fname, full_hash, parsed_rows, parse_ok, url, ref=ref)
    rec.update(last_success=utcnow_iso(), last_action="stored", last_hash=full_hash, source_url=url,
               parsed_rows=parsed_rows, parse_ok=parse_ok, raw_bytes=len(raw), stored_bytes=len(blob),
               key=f"raw/{datepath}/{fname}")
    return {"state": state, "action": "stored", "hash": h12, "parsed_rows": parsed_rows,
            "parse_ok": parse_ok, "bytes": len(raw)}


# --------------------------------------------------------------------------- fleet
def run_fleet(seed_path, storage, health_path=None, heartbeat_url=None, repo_root=".",
              fetch=http_get, max_bytes=None, only=None):
    states = load_seed(seed_path)
    if only:
        want = {s.strip().upper() for s in (only if isinstance(only, (list, set)) else [only])}
        states = [e for e in states if e["state"].upper() in want]
    health = json.load(open(health_path, encoding="utf-8")) if (health_path and os.path.exists(health_path)) else {"collectors": {}}
    node = health.setdefault("collectors", {}).setdefault("warn", {})
    node.setdefault("states", {})
    dt = datetime.now(timezone.utc)
    ref = git_ref(repo_root)          # resolved once per fleet run (one subprocess, not one per state)
    results = [archive_state(storage, e, dt, node, fetch=fetch, max_bytes=max_bytes, ref=ref) for e in states]
    stored = sum(1 for r in results if r["action"] == "stored")
    quarantined = sum(1 for r in results if r["action"] == "quarantined")
    node.update(last_success=utcnow_iso(), last_action="stored" if stored else "unchanged",
                git_ref=ref, state_count=len(states),
                quarantined=quarantined)
    if health_path:
        health["generated"] = utcnow_iso()
        os.makedirs(os.path.dirname(health_path) or ".", exist_ok=True)
        json.dump(health, open(health_path, "w", encoding="utf-8"), indent=2)
    hb = _heartbeat(heartbeat_url, ok=(quarantined == 0))
    return {"states": len(states), "stored": stored,
            "unchanged": sum(1 for r in results if r["action"] == "unchanged"),
            "quarantined": quarantined, "heartbeat": hb, "results": results}


def _heartbeat(url, ok=True):
    """Ping the logical 'warn' healthcheck (SPEC-02 §1). Inert if unset; any quarantine → /fail.
    Never raises into the caller."""
    if not url:
        return "unset"
    target = url if ok else url.rstrip("/") + "/fail"
    try:
        http_get(target, timeout=15)
        return "pinged"
    except Exception as e:
        return f"err:{type(e).__name__}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--local-root", default="local-archive")
    ap.add_argument("--seed", default=os.path.join(os.path.dirname(__file__), "seed_warn.json"))
    ap.add_argument("--only", default=None, help="comma-separated state codes, e.g. CA,NY")
    ap.add_argument("--max-bytes", type=int, default=None)
    args = ap.parse_args()
    hp = os.path.join(args.local_root, "HEALTH.json") if args.verify else os.path.join("ops", "state", "health", "warn.json")
    storage = LocalFSBackend(args.local_root) if args.verify else select_storage(args.local_root)
    heartbeat = None if args.verify else os.environ.get("HC_WARN")
    only = args.only.split(",") if args.only else None
    res = run_fleet(args.seed, storage, health_path=hp, heartbeat_url=heartbeat, max_bytes=args.max_bytes, only=only)
    print(json.dumps({k: v for k, v in res.items() if k != "results"}, indent=2))
    for r in res["results"]:
        print("  ", r)
    # SPEC-02 §1 job contract: any quarantine → exit nonzero loudly (alarms via SPEC-03).
    raise SystemExit(2 if res["quarantined"] else 0)
