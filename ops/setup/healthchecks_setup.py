#!/usr/bin/env python
"""Provision the healthchecks.io dead-man checks for the collector fleet (SPEC-03 §1).

OPERATOR ERRAND (W-003 item 1) — needs a healthchecks.io project API key, which only the operator
can mint. Once you have it, this replaces the whole manual dashboard dance:

  1. healthchecks.io -> your project -> Settings -> API Access -> create a key with
     "read/write" scope. Copy it.
  2. In the HC dashboard -> Integrations, add an **ntfy** integration once, pointed at topic
     `theexhaust-75Z` (the phone-confirmed topic). Every check below is created with channels="*",
     so it inherits this (and any other) integration automatically — no per-check wiring.
  3. From the repo root:
         # dry run (no network, no secrets) — prints the plan:
         set HEALTHCHECKS_API_KEY=...   (PowerShell: $env:HEALTHCHECKS_API_KEY='...')
         C:\\ProgramData\\miniconda3\\python.exe ops/setup/healthchecks_setup.py
         # do it for real (creates/updates checks + sets HC_<COLLECTOR> Actions secrets via gh):
         C:\\ProgramData\\miniconda3\\python.exe ops/setup/healthchecks_setup.py --apply

Idempotent: checks are keyed unique on name, so re-running updates rather than duplicates. This also
re-homes the ad-hoc `nhtsa-recalls` check created during BUILD-00 onto a properly-scheduled check
(you can delete the old ad-hoc one afterward). The weekly-session + site-publish checks in the
SPEC-03 §1 budget are intentionally NOT created here: their runners don't exist yet, and a check for a
not-yet-running job just false-alarms. Add them when the weekly Task Scheduler job / the publisher land.
"""
from __future__ import annotations

import argparse
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from opscore import healthchecks as hc  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Provision healthchecks.io collector checks (SPEC-03 §1).")
    ap.add_argument("--apply", action="store_true",
                    help="actually create/update checks and set Actions secrets (default: dry run)")
    ap.add_argument("--no-secrets", action="store_true",
                    help="with --apply, create checks but do NOT set HC_<COLLECTOR> Actions secrets")
    ap.add_argument("--repo", default=None, help="gh --repo target (default: current dir's remote)")
    ap.add_argument("--repo-root", default=_REPO_ROOT)
    args = ap.parse_args(argv)

    wf_dir = os.path.join(args.repo_root, ".github", "workflows")
    specs = hc.collector_specs(wf_dir)

    print(f"Planned checks ({len(specs)}) from {wf_dir}:")
    print(f"  {'collector':<20} {'secret':<24} {'cron':<16} {'max-gap':>8} {'grace':>10}")
    for s in specs:
        print(f"  {s['collector']:<20} {s['secret']:<24} {s['cron']:<16} "
              f"{s['max_gap_hours']:>6}h  {s['grace'] // 3600:>7}h")

    if not args.apply:
        print("\n(dry run) re-run with --apply and HEALTHCHECKS_API_KEY set to create these.")
        return 0

    key = os.environ.get("HEALTHCHECKS_API_KEY", "").strip()
    if not key:
        print("\nERROR: HEALTHCHECKS_API_KEY is not set — cannot create checks.", file=sys.stderr)
        return 2

    print("\nApplying...")
    results = hc.apply(wf_dir, key, set_secrets=not args.no_secrets, repo=args.repo)
    for r in results:
        flag = "secret set" if r["secret_set"] else "secret NOT set"
        print(f"  {r['collector']:<20} grace={r['grace'] // 3600}h  {flag}  ping_url={r['ping_url']}")
    print("\nDone. Confirm the checks show 'new'/'up' in the HC dashboard and that the ntfy "
          "integration is attached, then run the kill-one-collector drill (ops/playbooks/kill-drill.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
