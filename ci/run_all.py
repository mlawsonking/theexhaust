#!/usr/bin/env python
"""The full suite (BUILD-PROTOCOL §5), one command. Runs every guard + test module in order,
prints a compact per-step result, and exits nonzero if ANY step fails. This is the gate CI runs
on every push and the liturgy a worker runs before every commit.

    python ci/run_all.py

Offline + deterministic: no network, no metered LLM, no R2 creds needed (collectors are exercised
by their offline unit tests, not live here).
"""
from __future__ import annotations

import subprocess
import sys
import time

# (label, argv-after-interpreter) — exact BUILD-PROTOCOL §5 block, in order.
STEPS = [
    ("covenant guard",        ["ci/covenant_guard.py"]),
    ("covenant guard tests",  ["ci/test_covenant_guard.py"]),
    ("collectors framework",  ["-m", "collectors.tests.test_framework"]),
    ("collectors warn",       ["-m", "collectors.tests.test_warn"]),
    ("opscore",               ["-m", "opscore.tests.test_opscore"]),
    ("retrocast harness",     ["-m", "retrocast.tests.test_harness"]),
    ("retrocast nhtsa freeze", ["-m", "retrocast.tests.test_nhtsa_lexicon"]),
    ("sitegen",               ["-m", "sitegen.tests.test_site"]),
    ("engines",               ["-m", "engines.tests.test_engines"]),
    ("resolver",              ["-m", "resolver.tests.test_resolver"]),
]


def main() -> int:
    failures = []
    t0 = time.time()
    for label, args in STEPS:
        r = subprocess.run([sys.executable, *args], capture_output=True, text=True)
        ok = r.returncode == 0
        tail = (r.stdout.strip().splitlines() or [""])[-1]
        print(f"[{'PASS' if ok else 'FAIL'}] {label:22s} {tail}")
        if not ok:
            failures.append(label)
            # surface the failing step's output so CI logs are actionable
            print(r.stdout, file=sys.stderr)
            print(r.stderr, file=sys.stderr)
    dt = time.time() - t0
    if failures:
        print(f"\nSUITE FAILED ({len(failures)}/{len(STEPS)}): {', '.join(failures)} — {dt:.1f}s")
        return 1
    print(f"\nSUITE GREEN — {len(STEPS)}/{len(STEPS)} steps, {dt:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
