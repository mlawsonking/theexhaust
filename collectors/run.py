"""Collector runner. Used by R1 (Actions) and locally.

  python -m collectors.run cms-deficiencies --verify --max-bytes 3000000
  python -m collectors.run cms-deficiencies                      # full fetch -> local-archive/

Production (once R2 secrets exist) selects the R2 backend from env; absent that, it uses
the LocalFS backend (dev + operator-box fallback). No metered LLM, ever.
"""
from __future__ import annotations

import argparse
import json
import os

from . import cms_deficiencies, cpsc_recalls, nhtsa
from .framework import LocalFSBackend, R2Backend

# collector name -> (build_fn, make_fetch_fn)
REGISTRY = {
    cms_deficiencies.NAME: (cms_deficiencies.build, cms_deficiencies.make_fetch),
    cpsc_recalls.NAME: (cpsc_recalls.build, cpsc_recalls.make_fetch),
    nhtsa.NAME_RCL: (nhtsa.build_recalls, nhtsa.make_fetch_recalls),
    nhtsa.NAME_CMPL: (nhtsa.build_complaints, nhtsa.make_fetch_complaints),
}


def select_storage(local_root: str):
    """R2 if the BUILD-00 secrets are present in env, else LocalFS."""
    if os.environ.get("R2_BUCKET") and os.environ.get("R2_ENDPOINT"):
        return R2Backend(
            bucket=os.environ["R2_BUCKET"],
            endpoint_url=os.environ["R2_ENDPOINT"],
            access_key=os.environ["R2_ACCESS_KEY_ID"],
            secret_key=os.environ["R2_SECRET_ACCESS_KEY"],
        )
    return LocalFSBackend(local_root)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("collector", choices=sorted(REGISTRY))
    ap.add_argument("--verify", action="store_true", help="dev verification run (local backend)")
    ap.add_argument("--local-root", default="local-archive")
    ap.add_argument("--health-path", default=None, help="HEALTH.json to update (default: none in verify)")
    ap.add_argument("--max-bytes", type=int, default=None, help="cap stream read (verification only)")
    args = ap.parse_args()

    build_fn, make_fetch = REGISTRY[args.collector]
    storage = LocalFSBackend(args.local_root) if args.verify else select_storage(args.local_root)
    heartbeat = None if args.verify else os.environ.get(f"HC_{args.collector.upper().replace('-', '_')}")
    health_path = args.health_path or (os.path.join(args.local_root, "HEALTH.json") if args.verify else "ops/state/HEALTH.json")

    collector = build_fn(storage=storage, health_path=health_path, heartbeat_url=heartbeat, repo_root=".")
    result = collector.run(make_fetch(), max_bytes=args.max_bytes)
    print(json.dumps(result, indent=2))
    # Alarm surfaces as a nonzero exit (SPEC-02 job contract: exit loudly on trouble).
    return 2 if result.get("alarm") else 0


if __name__ == "__main__":
    raise SystemExit(main())
