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
from datetime import datetime, timezone

import zstandard as zstd

from engines import ats
from .framework import LocalFSBackend, git_ref, http_get, sha256_hex, select_storage, utcnow_iso


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
    cur = storage.get(mkey)
    man = json.loads(cur) if cur else {
        "collector": "ats-boards", "ats": board["ats"], "token": board["token"],
        "date": datepath.split("/", 3)[-1], "schema_version": ats.SCHEMA_VERSION,
        "git_ref": ref, "files": [],
    }
    man["files"].append({
        "file": fname, "sha256": full_hash, "postings": postings,
        "source_url": source_url, "stored_at": utcnow_iso(),
    })
    storage.put(mkey, json.dumps(man, indent=2).encode())


def archive_board(storage, board, dt, node, fetch_fn=None, max_bytes=None, repo_root=".", ref=None):
    fetch_fn = fetch_fn or ats.fetch_board
    a, token = board["ats"], board["token"]
    bkey = f"{a}/{token}"
    rec = node["boards"].setdefault(bkey, {})
    status, headers, raw, url = fetch_fn(a, token, max_bytes=max_bytes)
    h = sha256_hex(raw)
    h12 = h[:12]
    if rec.get("last_hash") == h:
        rec.update(last_success=utcnow_iso(), last_action="unchanged")
        return {"board": bkey, "action": "unchanged"}
    # light validation: parseable + normalizes to >=1 posting
    try:
        n = len(ats.normalize(a, raw))
        assert n >= 1
    except Exception:
        storage.put(f"quarantine/ats-boards/{a}/{token}/{dt:%Y%m%d}-{h12}.json", raw)
        rec.update(last_run=utcnow_iso(), last_action="quarantined-parse")
        return {"board": bkey, "action": "quarantined", "alarm": True}
    datepath = f"ats-boards/{a}/{token}/{dt:%Y}/{dt:%m}/{dt:%d}"
    fname = f"{dt:%H%M}-{h12}.json.zst"
    storage.put(f"raw/{datepath}/{fname}", zstd.ZstdCompressor(level=10).compress(raw))
    _update_manifest(storage, datepath, board, fname, h, n, url,
                     ref=git_ref(repo_root) if ref is None else ref)
    rec.update(last_success=utcnow_iso(), last_action="stored", last_hash=h, postings=n, source_url=url)
    return {"board": bkey, "action": "stored", "postings": n, "hash": h12}


def run_fleet(seed_path, storage, health_path=None, heartbeat_url=None, repo_root=".",
              fetch_fn=None, max_bytes=None):
    boards = load_seed(seed_path)
    health = json.load(open(health_path, encoding="utf-8")) if (health_path and os.path.exists(health_path)) else {"collectors": {}}
    node = health.setdefault("collectors", {}).setdefault("ats-boards", {})
    node.setdefault("boards", {})
    dt = datetime.now(timezone.utc)
    ref = git_ref(repo_root)          # resolved once per fleet run (one subprocess, not one per board)
    results = [archive_board(storage, b, dt, node, fetch_fn=fetch_fn, max_bytes=max_bytes,
                             repo_root=repo_root, ref=ref) for b in boards]
    stored = sum(1 for r in results if r["action"] == "stored")
    node.update(last_success=utcnow_iso(), last_action="stored" if stored else "unchanged",
                git_ref=ref, board_count=len(boards))
    if health_path:
        health["generated"] = utcnow_iso()
        os.makedirs(os.path.dirname(health_path) or ".", exist_ok=True)
        json.dump(health, open(health_path, "w", encoding="utf-8"), indent=2)
    quarantined = sum(1 for r in results if r["action"] == "quarantined")
    hb = _heartbeat(heartbeat_url, ok=(quarantined == 0))
    return {"boards": len(boards), "stored": stored,
            "unchanged": sum(1 for r in results if r["action"] == "unchanged"),
            "quarantined": quarantined, "heartbeat": hb, "results": results}


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
    raise SystemExit(2 if res["quarantined"] else 0)
