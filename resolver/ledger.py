"""The resolution ledger (SPEC-09 §1) — append-only. Every accepted pair is recorded once and
never re-adjudicated at cost (the cache is permanent). Published joins cite ledger entries."""
from __future__ import annotations

import json
import os
from datetime import date

METHOD_VERSION = "resolver-v1"


def record(ledger_path, a_ref, b_ref, tier, confidence, evidence, method_version=METHOD_VERSION, today=None):
    rec = {"a": a_ref, "b": b_ref, "tier": tier, "confidence": round(float(confidence), 4),
           "evidence": evidence, "method_version": method_version,
           "date": (today or date.today()).isoformat()}
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def load(ledger_path):
    if not os.path.exists(ledger_path):
        return []
    out = []
    for line in open(ledger_path, encoding="utf-8"):
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def cached_pair(ledger_path, a_ref, b_ref):
    """A pair is never re-adjudicated at cost — return the prior verdict if present (either order)."""
    for r in load(ledger_path):
        if (r["a"] == a_ref and r["b"] == b_ref) or (r["a"] == b_ref and r["b"] == a_ref):
            return r
    return None
