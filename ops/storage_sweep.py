#!/usr/bin/env python
"""Measured R2 storage sweep -> the SPEC-04 §4 budget ledger.

`ops/state/BUDGET.json` carries its own `re_project_triggers` ("any collector added to the
roster", a seed expansion, a WARN tranche). W-007c/G11: the cms-pbj trigger FIRED at W-007b and
was not executed, so the ledger's spend-visibility guarantee — and the free-tier-exhausted date
the covenant's $5/mo bar is read off — were computed on inputs missing the newest and
second-largest storage line. A trigger nobody can execute in one command is a trigger that gets
skipped, so the ad-hoc W-005 sweep is now this file.

    python ops/storage_sweep.py              # measure and print, change nothing
    python ops/storage_sweep.py --write      # measure and update ops/state/BUDGET.json

Read-only against R2 (a single list_objects_v2 paginate; no gets, no writes, no egress cost).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from opscore.budget import Budget  # noqa: E402

BUDGET_PATH = os.path.join(ROOT, "ops", "state", "BUDGET.json")


def sweep():
    """-> (by_prefix_bytes, total_bytes, objects). Prefix = the first two key segments, so each
    collector's `raw/<name>` line is separately visible rather than hidden in one total."""
    import boto3
    s3 = boto3.client("s3", endpoint_url=os.environ["R2_ENDPOINT"],
                      aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                      aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"], region_name="auto")
    by, total, objects = {}, 0, 0
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=os.environ["R2_BUCKET"]):
        for o in page.get("Contents", []):
            parts = o["Key"].split("/")
            prefix = "/".join(parts[:2]) if len(parts) > 1 else o["Key"]
            by[prefix] = by.get(prefix, 0) + o["Size"]
            total += o["Size"]
            objects += 1
    return dict(sorted(by.items())), total, objects


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="update ops/state/BUDGET.json in place")
    ap.add_argument("--note", default=None, help="replace storage.note")
    args = ap.parse_args()

    for k in ("R2_BUCKET", "R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"):
        if not os.environ.get(k):
            print(f"missing {k} — this sweep needs read access to the archive", file=sys.stderr)
            return 2

    by, total, objects = sweep()
    gb = total / (1024 ** 3)
    print(f"MEASURED SWEEP — {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} · "
          f"bucket {os.environ['R2_BUCKET']}")
    w = max(len(k) for k in by)
    for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
        print(f"  {k:{w}}  {v:>15,} B  {v / total:6.1%}")
    print(f"  {'TOTAL':{w}}  {total:>15,} B  = {gb:.4f} GB in {objects:,} objects")
    print(f"  projection: ${Budget.storage_cost(gb):.4f}/mo "
          f"(10 GB free tier, $0.015/GB-month beyond it)")

    if not args.write:
        print("\n(dry run — pass --write to update ops/state/BUDGET.json)")
        return 0

    b = Budget.load(BUDGET_PATH)
    b.set_storage(gb)
    st = b.data["storage"]
    st["raw_bytes"] = total
    st["objects"] = objects
    st["by_collector_bytes"] = by
    st["measured"] = f"{date.today().isoformat()} (ops/storage_sweep.py; full list_objects_v2 sweep)"
    if args.note:
        st["note"] = args.note
    b.save(BUDGET_PATH, today=date.today())
    print(f"\nwrote {BUDGET_PATH}")
    if b.storage_alarm():
        print("::warning:: storage projection is over the $5/mo covenant bar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
