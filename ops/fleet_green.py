#!/usr/bin/env python
"""Fleet-green evidence report (SPEC-01 §6 criterion 1: "all enabled collectors green 7
consecutive days (heartbeats + manifests)").

Built at W-005 because that criterion is a WINDOW, not a one-shot check: the archive clock started
2026-07-28, so the earliest it can be satisfied is 2026-08-04. Rather than make a future session
re-derive the evidence by hand, this gathers it mechanically from three independent sources:

  1. **Actions run history** (`gh run list` per collect-*.yml) — did every firing succeed?
  2. **R2 manifests** (`raw/**/manifest.json`) — did validated snapshots actually land? (corroborating,
     not primary: a dedupe firing is green and writes no manifest.)
  3. **Committed collector state** (`ops/state/health/<c>.json`) — quarantined / paused / drifting?

Heartbeats are the SPEC's first-choice evidence, but the healthchecks checks are inert until the
operator provisions them (Vikunja #212); until then 1-3 above are the evidence of record and this
report says so out loud rather than quietly claiming heartbeat coverage.

    python ops/fleet_green.py                 # 7-day window ending today
    python ops/fleet_green.py --days 7 --today 2026-08-04
    python ops/fleet_green.py --no-r2         # skip the R2 sweep (no creds / offline)

Read-only: no writes to R2, the repo, or GitHub.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from opscore.fleetgreen import (FLEET, committed_state, day_of_manifest_key,  # noqa: E402
                                run_rows, score)


# --------------------------------------------------------------------------- evidence gathering
def gh_runs(workflow: str, limit: int = 50):
    try:
        out = subprocess.check_output(
            ["gh", "run", "list", "--workflow", workflow, "--limit", str(limit),
             "--json", "conclusion,createdAt,databaseId,event"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL, shell=(os.name == "nt"))
    except Exception as e:
        print(f"  ! gh unavailable for {workflow} ({type(e).__name__}) — run evidence skipped", file=sys.stderr)
        return []
    return run_rows(json.loads(out))          # drops non-terminal runs (W-005c/F10)


def r2_manifest_days():
    """{collector_prefix: set(days)} from a single list sweep. Empty if creds/boto3 absent."""
    if not (os.environ.get("R2_BUCKET") and os.environ.get("R2_ENDPOINT")):
        return None
    try:
        import boto3
    except ImportError:
        return None
    s3 = boto3.client("s3", endpoint_url=os.environ["R2_ENDPOINT"],
                      aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                      aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"], region_name="auto")
    days = {name: set() for name in FLEET}
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=os.environ["R2_BUCKET"], Prefix="raw/"):
        for o in page.get("Contents", []):
            d = day_of_manifest_key(o["Key"])
            if not d:
                continue
            for name, (_wf, prefix) in FLEET.items():
                if o["Key"].startswith(prefix):
                    days[name].add(d)
    return days


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--today", default=None, help="YYYY-MM-DD (default: today, UTC)")
    ap.add_argument("--no-r2", action="store_true")
    args = ap.parse_args()

    today = date.fromisoformat(args.today) if args.today else datetime.now(timezone.utc).date()
    window = [today - timedelta(days=i) for i in range(args.days - 1, -1, -1)]
    print(f"FLEET-GREEN — {args.days}-day window {window[0]} .. {window[-1]} (UTC)")
    hb = "healthchecks heartbeats INERT (operator #212 unprovisioned)" if not os.environ.get("HC_WARN") \
        else "heartbeats configured"
    print(f"evidence: Actions runs + R2 manifests + committed state · {hb}\n")

    mdays = None if args.no_r2 else r2_manifest_days()
    if mdays is None:
        print("(R2 sweep skipped — no creds/boto3; manifest column empty)\n")

    rows, green = [], 0
    for name, (wf, _prefix) in FLEET.items():
        s = score(gh_runs(wf), (mdays or {}).get(name, set()), committed_state(ROOT, name), window)
        rows.append((name, s))
        green += s["green"]
    w = max(len(n) for n in FLEET)
    print(f"{'collector':{w}}  {'verdict':14} runs  ok-days                    manifest-days")
    for name, s in rows:
        print(f"{name:{w}}  {s['verdict']:14} {s['runs_in_window']:4}  "
              f"{','.join(d[5:] for d in s['ok_days']) or '-':25}  "
              f"{','.join(d[5:] for d in s['manifest_days']) or '-'}")
        if s["failed_days"]:
            print(f"{'':{w}}  ^ FAILED RUNS on {', '.join(s['failed_days'])}")
        if s["state_unreadable"]:
            print(f"{'':{w}}  ^ COMMITTED STATE UNREADABLE — {s['state_unreadable']}")
    print(f"\n{green}/{len(FLEET)} collectors green across the window.")
    if green < len(FLEET):
        print("SPEC-01 §6 criterion 1 NOT yet satisfied for the collectors above.")
        return 1
    print("SPEC-01 §6 criterion 1 SATISFIED for every enabled collector.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
