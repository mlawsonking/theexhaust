#!/usr/bin/env python3
"""Covenant guard — foundations guardrail (SPEC-04 §5 seed).

Fails (exit 1) if either constitutional invariant is violated:
  (1) any collector references a do-not-collect source (ci/do_not_collect.txt), or
  (2) any R1 GitHub Actions workflow references an Anthropic API key
      (R1 holds no metered LLM key — SPEC-02 §1, SPEC-04 §4).

Scans only collector code and workflow files, never docs/ops specs
(which legitimately name the banned sources in the register itself).

Run locally:  python ci/covenant_guard.py
"""
from __future__ import annotations
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_banned() -> list[str]:
    f = ROOT / "ci" / "do_not_collect.txt"
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line.lower())
    return out


def check_collectors(banned: list[str]) -> list[str]:
    viol = []
    cdir = ROOT / "collectors"
    if not cdir.exists():
        return viol
    for p in cdir.rglob("*.py"):
        text = p.read_text(encoding="utf-8", errors="ignore").lower()
        for d in banned:
            if d in text:
                viol.append(f"do-not-collect source '{d}' referenced in {p.relative_to(ROOT)}")
    return viol


def check_r1_no_llm_key() -> list[str]:
    viol = []
    wf = ROOT / ".github" / "workflows"
    if not wf.exists():
        return viol
    for p in list(wf.rglob("*.yml")) + list(wf.rglob("*.yaml")):
        if re.search(r"ANTHROPIC_API_KEY", p.read_text(encoding="utf-8", errors="ignore")):
            viol.append(f"Anthropic key reference in R1 workflow {p.relative_to(ROOT)} (R1 must hold no metered LLM key)")
    return viol


def main() -> int:
    banned = load_banned()
    viol = check_collectors(banned) + check_r1_no_llm_key()
    if viol:
        print("COVENANT GUARD: FAIL")
        for v in viol:
            print("  -", v)
        return 1
    print(f"COVENANT GUARD: OK ({len(banned)} do-not-collect sources enforced; no R1 LLM key; collectors clean)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
