"""Orphan clock (SPEC-06 §1). Activity = an operator-authored commit, any gate DECISION, or a
touch of ops/state/ACK. Week 3 -> warning + one nudge; week 4 -> orphan mode engages
automatically (entering is safe; exiting is instant on any activity).

Operator vs agent commits can't be told apart by git author on this repo (the human is the git
author, Claude the co-author), so the reliable liveness signals are the ACK 'last-active' date
and the newest gate DECISION date. A future refinement can add an explicit operator-commit marker.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

WARN_WEEKS = 3
ORPHAN_WEEKS = 4


def parse_ack_date(ack_text: str) -> date | None:
    m = re.search(r"last-active:\s*(\d{4})-(\d{2})-(\d{2})", ack_text or "")
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


@dataclass
class OrphanStatus:
    last_active: date | None
    weeks_since: int
    state: str          # active | warn | orphan
    weeks_to_freeze: int

    @property
    def is_orphaned(self) -> bool:
        return self.state == "orphan"


def status(today: date, ack_date: date | None, decision_dates: list[date] | None = None) -> OrphanStatus:
    # Only past/present signals count — a future-dated ACK or decision (clock skew, or a
    # 'defer 2026-09-01' date) must NOT reset a stale clock and defeat the fail-safe (SPEC-06).
    candidates = [d for d in ([ack_date] + list(decision_dates or [])) if d and d <= today]
    last = max(candidates) if candidates else None
    if last is None:
        # No liveness signal at all -> treat as maximally stale (safe: freezes gated surfaces).
        return OrphanStatus(None, ORPHAN_WEEKS, "orphan", 0)
    days = (today - last).days
    weeks = max(0, days // 7)
    if weeks >= ORPHAN_WEEKS:
        state = "orphan"
    elif weeks >= WARN_WEEKS:
        state = "warn"
    else:
        state = "active"
    return OrphanStatus(last, weeks, state, max(0, ORPHAN_WEEKS - weeks))


def report_line(st: OrphanStatus) -> str | None:
    """SPEC-05 §2 orphan-clock line; omitted when fully active (weeks_since == 0)."""
    if st.last_active is None:
        return "Operator liveness unknown — system treating as orphaned (gated surfaces frozen)."
    if st.weeks_since == 0:
        return None
    if st.state == "orphan":
        return f"Operator last active {st.last_active.isoformat()} ({st.weeks_since} weeks). Orphan mode ENGAGED — gated surfaces frozen, collectors running."
    return f"Operator last active {st.last_active.isoformat()} ({st.weeks_since} weeks). {st.weeks_to_freeze} weeks to autonomous freeze."
