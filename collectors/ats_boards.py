"""C3 — ats-boards fleet archiver (E1 Posting-Diff corpus).

Snapshots every board in the seed universe (collectors/seed_boards.json) to immutable storage,
per-board content-hash dedupe, one shared 'ats-boards' logical heartbeat with per-board detail in
HEALTH (SPEC-03 §1). Postings vanish silently, so this is the most perishable corpus — every
uncollected day loses the diff. Universe expansion is a gate item (SPEC-01 C3 / SPEC-04).

    python -m collectors.ats_boards --verify [--local-root DIR] [--max-bytes N]
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

import zstandard as zstd

from engines import ats
from .framework import (POLITE_PAUSE_S, LocalFSBackend, git_ref, http_get, load_state, polite_pause,
                        read_manifest, sha256_hex, select_storage, utcnow_iso)


def load_seed(path):
    return json.load(open(path, encoding="utf-8")).get("boards", [])


def _heartbeat(url, ok=True):
    """Ping the logical 'ats-boards' healthcheck (SPEC-02 §1 job contract). Inert if unset;
    a fleet run with any quarantine pings the /fail endpoint. Never raises into the caller."""
    if not url:
        return "unset"
    target = url if ok else url.rstrip("/") + "/fail"
    try:
        http_get(target, timeout=15)
        return "pinged"
    except Exception as e:  # a heartbeat failure must never crash the run
        return f"err:{type(e).__name__}"


def _update_manifest(storage, datepath, board, fname, full_hash, postings, source_url, ref=""):
    """Per-day manifest for this board (SPEC-01 §3: files, hashes, row counts, schema version,
    collector git ref). Mirrors framework.Collector._update_manifest / warn._update_manifest —
    without it a day's snapshots carry no independently checkable index."""
    mkey = f"raw/{datepath}/manifest.json"
    man = read_manifest(storage, mkey) or {
        "collector": "ats-boards", "ats": board["ats"], "token": board["token"],
        "date": datepath.split("/", 3)[-1], "schema_version": ats.SCHEMA_VERSION,
        "git_ref": ref, "files": [],
    }
    man["files"].append({
        "file": fname, "sha256": full_hash, "postings": postings,
        "source_url": source_url, "stored_at": utcnow_iso(),
    })
    storage.put(mkey, json.dumps(man, indent=2).encode())


def _quarantine(rec, kind, extra=None):
    """Record a per-unit quarantine + advance its fail streak. At 3 consecutive failures the unit
    PAUSES itself and asks for one gate (SPEC-03 §2) — otherwise a permanently broken board alarms
    3x/day forever and never surfaces as a decision (W-005c/F05)."""
    streak = rec.get("fail_streak", 0) + 1
    rec.update(last_run=utcnow_iso(), last_action=kind, fail_streak=streak, **(extra or {}))
    if streak >= 3:
        rec.update(paused=True)
    return streak


def archive_board(storage, board, dt, node, fetch_fn=None, max_bytes=None, repo_root=".", ref=None):
    fetch_fn = fetch_fn or ats.fetch_board
    a, token = board["ats"], board["token"]
    bkey = f"{a}/{token}"
    rec = node["boards"].setdefault(bkey, {})
    if rec.get("paused"):                       # cleared only by an operator decision on the gate
        return {"board": bkey, "action": "paused"}
    # One dead board must never kill the fleet (W-005c/F02): a seed company dropping its ATS is a
    # routine 404, and every board sorted after it would otherwise lose the day's diff forever.
    try:
        status, headers, raw, url = fetch_fn(a, token, max_bytes=max_bytes)
    except Exception as e:
        _quarantine(rec, "quarantined-fetch", {"last_error": f"{type(e).__name__}: {e}"})
        return {"board": bkey, "action": "quarantined", "alarm": True, "error": str(e)}
    if status != 200 or not raw:
        if raw:                                 # keep the block/notice page — 403-ladder forensics
            storage.put(f"quarantine/ats-boards/{a}/{token}/{dt:%Y%m%d}-{sha256_hex(raw)[:12]}.json", raw)
        _quarantine(rec, "quarantined-fetch", {"last_status": status})
        return {"board": bkey, "action": "quarantined", "alarm": True, "status": status}
    h = sha256_hex(raw)
    h12 = h[:12]
    if rec.get("last_hash") == h:
        rec.update(last_success=utcnow_iso(), last_action="unchanged", fail_streak=0)
        return {"board": bkey, "action": "unchanged"}
    # Validation is PARSEABILITY only. An empty board is not a defect — it is the single most
    # valuable event this corpus exists to catch (W-005c/F03): a company whose last opening just
    # closed. Quarantining it would alarm 3x/day forever AND drop the vanished-postings snapshot.
    try:
        n = len(ats.normalize(a, raw))
    except Exception as e:
        if rec.get("last_quarantine_hash") != h:        # anti-storm: alarm once per bad payload
            storage.put(f"quarantine/ats-boards/{a}/{token}/{dt:%Y%m%d}-{h12}.json", raw)
            _quarantine(rec, "quarantined-parse", {"last_quarantine_hash": h,
                                                   "last_error": f"{type(e).__name__}: {e}"})
            return {"board": bkey, "action": "quarantined", "alarm": True}
        rec.update(last_run=utcnow_iso(), last_action="quarantined-dup")
        return {"board": bkey, "action": "quarantined-dup", "alarm": False}
    # Never archive a payload that admits it is incomplete (W-005c/F16): an immutable truncated
    # "full board" vintage can never be re-fetched, and posting_diff would read phantom churn off it.
    truncated, detail = ats.truncation(a, raw)
    if truncated:
        if rec.get("last_quarantine_hash") != h:
            storage.put(f"quarantine/ats-boards/{a}/{token}/{dt:%Y%m%d}-{h12}.json", raw)
            _quarantine(rec, "quarantined-truncated", {"last_quarantine_hash": h, "last_error": detail})
            return {"board": bkey, "action": "quarantined", "alarm": True, "detail": detail}
        rec.update(last_run=utcnow_iso(), last_action="quarantined-dup")
        return {"board": bkey, "action": "quarantined-dup", "alarm": False}
    datepath = f"ats-boards/{a}/{token}/{dt:%Y}/{dt:%m}/{dt:%d}"
    fname = f"{dt:%H%M}-{h12}.json.zst"
    storage.put(f"raw/{datepath}/{fname}", zstd.ZstdCompressor(level=10).compress(raw))
    _update_manifest(storage, datepath, board, fname, h, n, url,
                     ref=git_ref(repo_root) if ref is None else ref)
    rec.update(last_success=utcnow_iso(), last_action="stored", last_hash=h, postings=n,
               source_url=url, fail_streak=0)
    return {"board": bkey, "action": "stored", "postings": n, "hash": h12}


def run_fleet(seed_path, storage, health_path=None, heartbeat_url=None, repo_root=".",
              fetch_fn=None, max_bytes=None, pause_s=None, sleeper=None):
    boards = load_seed(seed_path)
    health = load_state(health_path)
    node = health.setdefault("collectors", {}).setdefault("ats-boards", {})
    node.setdefault("boards", {})
    dt = datetime.now(timezone.utc)
    ref = git_ref(repo_root)          # resolved once per fleet run (one subprocess, not one per board)
    results = []
    for i, b in enumerate(boards):
        if i:                          # SPEC-01 §4.1: rate-limit + jitter between same-fleet requests
            polite_pause(POLITE_PAUSE_S if pause_s is None else pause_s, sleeper=sleeper)
        try:
            results.append(archive_board(storage, b, dt, node, fetch_fn=fetch_fn, max_bytes=max_bytes,
                                         repo_root=repo_root, ref=ref))
        except Exception as e:         # storage/manifest failure on ONE board must not end the run
            bkey = f"{b.get('ats')}/{b.get('token')}"
            node["boards"].setdefault(bkey, {}).update(
                last_run=utcnow_iso(), last_action="error", last_error=f"{type(e).__name__}: {e}")
            results.append({"board": bkey, "action": "error", "alarm": True, "error": str(e)})
    stored = sum(1 for r in results if r["action"] == "stored")
    quarantined = sum(1 for r in results if r["action"] in ("quarantined", "error"))
    paused = [r["board"] for r in results if r["action"] == "paused"]
    # last_action must REPORT the quarantine, or _collector.yml skips the state commit and the
    # quarantine/pause evidence never reaches main (W-005c/F01). last_success means what it says.
    node.update(last_action=("quarantined" if quarantined else ("stored" if stored else "unchanged")),
                git_ref=ref, board_count=len(boards), quarantined=quarantined, paused_boards=paused)
    node.update(**({"last_success": utcnow_iso()} if not quarantined else {"last_run": utcnow_iso()}))
    gate = _fleet_gate(node, "ats-boards", "boards")
    if health_path:
        health["generated"] = utcnow_iso()
        os.makedirs(os.path.dirname(health_path) or ".", exist_ok=True)
        json.dump(health, open(health_path, "w", encoding="utf-8"), indent=2)
    # An empty fleet is a silent stop, not a success — never ping the dead-man green (F15).
    empty = not boards
    hb = _heartbeat(heartbeat_url, ok=(quarantined == 0 and not empty))
    return {"boards": len(boards), "stored": stored,
            "unchanged": sum(1 for r in results if r["action"] == "unchanged"),
            "quarantined": quarantined, "paused": paused, "empty": empty,
            "needs_gate": gate, "heartbeat": hb, "results": results}


def _fleet_gate(node, collector, unit_key):
    """Surface a paused unit as a node-level `needs_gate` so weekly.file_collector_gates — which
    only reads top-level collector records — can file exactly one source gate (W-005c/F05).
    The value ends up inside a gate FILENAME, and board keys contain '/', so it must be sanitized."""
    paused = sorted(k for k, v in (node.get(unit_key) or {}).items() if v.get("paused"))
    if paused:
        units = "-".join(re.sub(r"[^A-Za-z0-9._-]+", "-", p) for p in paused)
        node["needs_gate"] = f"{collector}-fetch-3x-{units}"
    else:
        node.pop("needs_gate", None)
    return node.get("needs_gate")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--local-root", default="local-archive")
    ap.add_argument("--seed", default=os.path.join(os.path.dirname(__file__), "seed_boards.json"))
    ap.add_argument("--max-bytes", type=int, default=None)
    args = ap.parse_args()
    hp = os.path.join(args.local_root, "HEALTH.json") if args.verify else os.path.join("ops", "state", "health", "ats-boards.json")
    storage = LocalFSBackend(args.local_root) if args.verify else select_storage(args.local_root)
    heartbeat = None if args.verify else os.environ.get("HC_ATS_BOARDS")
    res = run_fleet(args.seed, storage, health_path=hp, heartbeat_url=heartbeat, max_bytes=args.max_bytes)
    print(json.dumps({k: v for k, v in res.items() if k != "results"}, indent=2))
    for r in res["results"]:
        print("  ", r)
    # SPEC-02 §1 job contract: any quarantine -> exit nonzero loudly (alarms via SPEC-03).
    # An empty fleet exits nonzero too: collecting nothing is the silent stop, not a clean run.
    raise SystemExit(2 if (res["quarantined"] or res["empty"]) else 0)
