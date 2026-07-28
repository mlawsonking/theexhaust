"""Gate mechanics (SPEC-04 §3). A gate is one operator decision as a file. The safe default
everywhere is: do nothing, keep collecting, ask. Nothing here ever *executes* an approval —
it only parses, validates, and moves files; execution is the weekly session's job on decided files.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

GATE_TYPES = ["new-index", "methodology", "named-entity", "source", "spend", "legal", "comms", "other"]
# Report ordering (SPEC-05 §1): legal > spend > named-entity > methodology > new-index > source > comms
PRIORITY = ["legal", "spend", "named-entity", "methodology", "new-index", "source", "comms", "other"]
# default_on_expiry MUST be a safe (non-executing) option — nothing ever executes by expiry.
SAFE_ON_EXPIRY = {"no-action", "reject"}
DEFAULT_EXPIRY_DAYS = 28


def _parse_date(s: str) -> date | None:
    s = (s or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


@dataclass
class Gate:
    slug: str = ""
    title: str = ""
    type: str = "other"
    created: str = ""
    by: str = ""
    expires: str = ""
    default_on_expiry: str = "no-action"
    estimate_usd: float | None = None
    hard_cap_usd: float | None = None
    what: str = ""
    evidence: str = ""
    options: str = ""
    decision: str = ""
    notes: str = ""
    path: str | None = None

    # -- status --------------------------------------------------------------
    TERMINAL_VERBS = ("reject", "no-action")

    @property
    def decision_verb(self) -> str:
        d = self.decision.strip()
        return d.split()[0].lower() if d else ""

    @property
    def is_decided(self) -> bool:
        """Terminal decisions ONLY (approve-* / reject / no-action). 'defer …' is not terminal,
        and free-text notes ('pending — need legal') leave the gate pending (SPEC-04 §3)."""
        v = self.decision_verb
        return v.startswith("approve") or v in self.TERMINAL_VERBS

    @property
    def defer_until(self) -> date | None:
        if self.decision_verb == "defer":
            return _parse_date(self.decision.strip()[len("defer"):].strip())
        return None

    def is_deferred(self, today: date) -> bool:
        du = self.defer_until
        return du is not None and today < du

    def is_expired(self, today: date) -> bool:
        exp = _parse_date(self.expires)
        return bool(exp and today > exp and not self.is_decided and not self.is_deferred(today))

    def priority_rank(self) -> int:
        return PRIORITY.index(self.type) if self.type in PRIORITY else len(PRIORITY)

    def resolve(self, today: date) -> str:
        """What this gate currently means. Never returns an executing action by expiry."""
        if self.is_decided:
            return self.decision.strip()
        if self.is_deferred(today):
            return f"deferred until {self.defer_until.isoformat()}"
        if self.is_expired(today):
            return "expired-no-action"
        return "pending"

    # -- validation ----------------------------------------------------------
    def validate(self) -> list[str]:
        errs = []
        if not self.title:
            errs.append("missing title")
        if self.type not in GATE_TYPES:
            errs.append(f"bad type '{self.type}'")
        if self.default_on_expiry not in SAFE_ON_EXPIRY:
            errs.append(f"default_on_expiry '{self.default_on_expiry}' is not a safe option {sorted(SAFE_ON_EXPIRY)}")
        if not _parse_date(self.created):
            errs.append("missing/invalid created date")
        if not _parse_date(self.expires):
            errs.append("missing/invalid expires date")
        if self.type == "spend" and (self.estimate_usd is None or self.hard_cap_usd is None):
            errs.append("spend gate requires estimate_usd and hard_cap_usd")
        return errs


HEADER_KEYS = ["type", "created", "by", "expires", "default_on_expiry", "estimate_usd", "hard_cap_usd"]


def parse(text: str, path: str | None = None) -> Gate:
    g = Gate(path=path)
    section = None
    buf: dict[str, list[str]] = {"what": [], "evidence": [], "options": []}
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line.startswith("# GATE:"):
            g.title = line[len("# GATE:"):].strip()
            continue
        if line.startswith("## "):
            h = line[3:].strip().lower()
            section = "what" if h.startswith("what") else "evidence" if h.startswith("evidence") else "options" if h.startswith("options") else None
            continue
        if line.startswith("DECISION:"):
            g.decision = line[len("DECISION:"):].strip()
            section = None
            continue
        if line.startswith("notes:"):
            g.notes = line[len("notes:"):].strip()
            section = None
            continue
        if section:
            buf[section].append(line)
            continue
        m = re.match(r"([a-z_]+)\s*:\s*(.*)$", line)
        if m and m.group(1) in HEADER_KEYS:
            k, v = m.group(1), m.group(2).strip()
            if k in ("estimate_usd", "hard_cap_usd"):
                try:
                    setattr(g, k, float(v))
                except ValueError:
                    pass
            elif k == "by":
                # 'created: YYYY-MM-DD  by: <x>' may fold by onto the created line
                setattr(g, "by", v)
            else:
                setattr(g, k, v)
            # handle 'created: D  by: X' on one line
            if k == "created" and "by:" in v:
                cv, _, bv = v.partition("by:")
                g.created = cv.strip()
                g.by = bv.strip()
    g.what = "\n".join(buf["what"]).strip()
    g.evidence = "\n".join(buf["evidence"]).strip()
    g.options = "\n".join(buf["options"]).strip()
    if path:
        base = os.path.splitext(os.path.basename(path))[0]
        m2 = re.match(r"GATE-\d{8}-(.+)$", base)  # logical slug, not the GATE-<date>- filename prefix
        g.slug = m2.group(1) if m2 else base
    return g


def to_text(g: Gate) -> str:
    lines = [f"# GATE: {g.title}", f"type: {g.type}", f"created: {g.created}  by: {g.by}",
             f"expires: {g.expires}", f"default_on_expiry: {g.default_on_expiry}"]
    if g.type == "spend":
        lines.append(f"estimate_usd: {g.estimate_usd}")
        lines.append(f"hard_cap_usd: {g.hard_cap_usd}")
    lines += ["## What & why now", g.what or "", "## Evidence", g.evidence or "",
              "## Options", g.options or "", f"DECISION: {g.decision}", f"notes: {g.notes}"]
    return "\n".join(lines) + "\n"


def new_gate(queue_pending_dir, slug, title, gtype, by, what, evidence="", options="",
             created: date | None = None, expiry_days=DEFAULT_EXPIRY_DAYS,
             estimate_usd=None, hard_cap_usd=None, default_on_expiry="no-action") -> Gate:
    created = created or date.today()
    g = Gate(slug=slug, title=title, type=gtype, created=created.isoformat(), by=by,
             expires=(created + timedelta(days=expiry_days)).isoformat(),
             default_on_expiry=default_on_expiry, estimate_usd=estimate_usd,
             hard_cap_usd=hard_cap_usd, what=what, evidence=evidence, options=options)
    errs = g.validate()
    if errs:
        raise ValueError(f"invalid gate: {errs}")
    # The slug becomes a FILENAME. An unsafe one fails silently rather than loudly — on Windows
    # "a:b" writes an NTFS alternate data stream that load_pending can never see, so the gate the
    # operator is owed simply vanishes. Reject it here instead (found while wiring W-005c/F05).
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", slug or ""):
        raise ValueError(f"unsafe gate slug {slug!r}: use [A-Za-z0-9._-] only (it becomes a filename)")
    os.makedirs(queue_pending_dir, exist_ok=True)
    g.path = os.path.join(queue_pending_dir, f"GATE-{created.strftime('%Y%m%d')}-{slug}.md")
    with open(g.path, "w", encoding="utf-8") as f:
        f.write(to_text(g))
    return g


def load_pending(queue_pending_dir) -> list[Gate]:
    out = []
    if not os.path.isdir(queue_pending_dir):
        return out
    for fn in sorted(os.listdir(queue_pending_dir)):
        if fn.startswith("GATE-") and fn.endswith(".md"):
            with open(os.path.join(queue_pending_dir, fn), encoding="utf-8") as f:
                out.append(parse(f.read(), os.path.join(queue_pending_dir, fn)))
    return out


def sweep(queue_pending_dir, queue_decided_dir, today: date) -> list[dict]:
    """Move decided and expired-undecided gates out of pending into decided/{YYYY}/.
    Expired-undecided become 'expired-no-action' — NOTHING ever executes by expiry (SPEC-04 §3).
    Returns the list of moves; the caller (weekly session) executes approvals separately."""
    actions = []
    for g in load_pending(queue_pending_dir):
        outcome = None
        if g.is_decided:
            outcome = g.decision.strip()
        elif g.is_deferred(today):
            continue  # operator deferred; leave in pending, re-surfaces on/after the defer date
        elif g.is_expired(today):
            outcome = "expired-no-action"
        if outcome is None:
            continue
        year_dir = os.path.join(queue_decided_dir, str(today.year))
        os.makedirs(year_dir, exist_ok=True)
        dest = os.path.join(year_dir, os.path.basename(g.path))
        os.replace(g.path, dest)
        actions.append({"slug": g.slug, "outcome": outcome, "executes": _executes(outcome), "dest": dest})
    return actions


def _executes(outcome: str) -> bool:
    """Only explicit approvals execute; rejects/expiries/no-action never do."""
    o = outcome.lower()
    return o.startswith("approve")
