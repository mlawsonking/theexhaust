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


# Any first-class Anthropic/Claude metered credential — not just the literal ANTHROPIC_API_KEY
# (also ANTHROPIC_AUTH_TOKEN, CLAUDE_*_KEY/TOKEN, etc.). R1 must hold none.
LLM_KEY_RE = re.compile(r"ANTHROPIC_[A-Z0-9_]*|CLAUDE[A-Z0-9_]*(?:KEY|TOKEN)", re.I)


def check_collectors(banned, root=ROOT) -> list[str]:
    viol = []
    for sub in ("collectors", "engines", "resolver"):  # any code that fetches sources
        cdir = root / sub
        if not cdir.exists():
            continue
        for p in cdir.rglob("*.py"):
            for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                low = line.lower()
                for d in banned:
                    if d in low:
                        # SPEC-01 sanctions ALEC-Exposed via Wayback ONLY; allow a web.archive.org-wrapped ref.
                        if d == "alecexposed.org" and "web.archive.org" in low:
                            continue
                        viol.append(f"do-not-collect source '{d}' referenced in {p.relative_to(root)}:{i}")
    return viol


def check_r1_no_llm_key(root=ROOT) -> list[str]:
    viol = []
    wf = root / ".github" / "workflows"
    if not wf.exists():
        return viol
    for p in list(wf.rglob("*.yml")) + list(wf.rglob("*.yaml")):
        m = LLM_KEY_RE.search(p.read_text(encoding="utf-8", errors="ignore"))
        if m:
            viol.append(f"metered-LLM credential '{m.group(0)}' in R1 workflow {p.relative_to(root)} (R1 holds no LLM key)")
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
