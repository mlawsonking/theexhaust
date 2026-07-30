"""The weekly gate report (SPEC-05) — Michael's ~1 hour, compiled never hand-written.
Decisions are the headline; if there are none, the subject says so and the report is short.
Every claim should link its evidence; unlinked assertions are a smell. Length cap 150 lines.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date, timedelta

from . import gates as gatelib
from . import orphan as orphanlib

LENGTH_CAP = 150


def merged_health(repo_root: str) -> dict:
    """W-002b: per-collector state files `ops/state/health/<collector>.json` are the source of
    truth (each Actions job commits only its own → no write races); legacy `ops/state/HEALTH.json`
    is a fallback for any collector not yet split out. Each per-collector file holds the framework
    shape `{"collectors": {<name>: rec}, "generated": ...}` (usually one entry)."""
    collectors: dict = {}
    unreadable: dict = {}
    generated = ""
    hdir = os.path.join(repo_root, "ops", "state", "health")
    if os.path.isdir(hdir):
        for fn in sorted(os.listdir(hdir)):
            if not fn.endswith(".json"):
                continue
            try:
                d = json.load(open(os.path.join(hdir, fn), encoding="utf-8"))
            except Exception as e:
                # W-007c/G15: a damaged state file is REPORTED, never dropped. Skipping it made
                # "the collector is frozen" and "we cannot tell" indistinguishable downstream, so
                # the site's stale-data banner failed open exactly when state was corrupt.
                unreadable[fn] = f"{type(e).__name__}: {e}"
                continue
            for name, rec in (d.get("collectors") or {}).items():
                collectors[name] = rec                    # per-collector file is authoritative
            generated = max(generated, d.get("generated", ""))
    legacy_p = os.path.join(repo_root, "ops", "state", "HEALTH.json")
    if os.path.exists(legacy_p):
        try:
            legacy = json.load(open(legacy_p, encoding="utf-8"))
        except Exception:
            legacy = {}
        for name, rec in (legacy.get("collectors") or {}).items():
            collectors.setdefault(name, rec)              # legacy only fills gaps
        generated = max(generated, legacy.get("generated", ""))
    return {"_doc": "merged collector health (W-002b: per-collector files + legacy fallback)",
            "collectors": collectors, "unreadable": unreadable, "generated": generated}


def _collector_board(health: dict) -> dict:
    cols = (health or {}).get("collectors", {})
    green = quarantined = paused = 0
    stale = []
    for name, rec in cols.items():
        act = rec.get("last_action")
        if act in ("stored", "unchanged"):
            green += 1
        if act == "quarantined-drift":
            quarantined += 1
        if rec.get("paused"):
            paused += 1
        if rec.get("last_action") == "unchanged" and rec.get("stale"):
            stale.append(name)
    return {"green": green, "total": len(cols), "quarantined": quarantined, "paused": paused, "stale": stale}


def _calendar_next_30(calendar_text: str, today: date) -> list[str]:
    out = []
    horizon = today + timedelta(days=30)
    for line in (calendar_text or "").splitlines():
        for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2})", line):  # check every date token on the line
            try:
                d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                continue
            if today <= d <= horizon:
                out.append(line.strip().lstrip("-* "))
                break  # include the line once if ANY date on it is in-window
    return out


def compile_report(*, health: dict, pending_gates: list, budget_data: dict, calendar_text: str,
                   ack_text: str, today: date, week_num: int, decision_dates=None) -> str:
    # Deferred-in-window gates are hidden from the headline until their defer date (SPEC-04 §3).
    actionable = [g for g in pending_gates if not g.is_deferred(today)]
    gates_sorted = sorted(actionable, key=lambda g: (g.priority_rank(), g.created))
    n = len(gates_sorted)
    wk_start = today - timedelta(days=today.weekday())
    rng = f"{wk_start.isoformat()} … {(wk_start + timedelta(days=6)).isoformat()}"

    L = [f"# The Exhaust — week {week_num:02d}, {rng}"]
    L.append(f"**You need to decide {n} thing{'s' if n != 1 else ''}. Everything else is green.**"
             if n else "**Nothing needs you this week.**")
    L.append("")

    # 1) Decisions (the headline)
    L.append(f"## 1) Decisions ({n})")
    if not n:
        L.append("_None pending._")
    else:
        for g in gates_sorted:
            link = f" · [{os.path.basename(g.path)}]({g.path})" if g.path else ""
            rec = f" · rec: {g.options.splitlines()[0].strip()}" if g.options.strip() else ""
            L.append(f"- **{g.title}** · {g.type} · expires {g.expires} (default: {g.default_on_expiry}){rec}{link}")
    L.append("")

    # 2) Health board
    b = _collector_board(health)
    storage = (budget_data or {}).get("storage", {})
    yyyymm = today.strftime("%Y-%m")
    metered = round(sum(r.get("actual", 0) for r in (budget_data or {}).get("metered_runs", [])
                        if str(r.get("date", "")).startswith(yyyymm)), 4)
    L.append("## 2) Health board")
    L.append(f"Collectors: {b['green']}/{b['total']} green · quarantines: {b['quarantined']} · paused: {b['paused']}"
             + (f" · stale: {', '.join(b['stale'])}" if b['stale'] else ""))
    L.append(f"Storage: {storage.get('r2_gb', 0)} GB (${storage.get('projection_usd_mo', 0)}/mo) · "
             f"metered this month: ${metered}")
    L.append("")

    # 3) The week's output
    L.append("## 3) The week's output")
    L.append("Artifacts posted: 0 (pre-launch) · scorecard movements: none · corrections: none · "
             "citations detected: 0 (stated plainly).")
    L.append("")

    # 4) Flywheel
    L.append("## 4) Flywheel")
    L.append("Pre-launch. NHTSA retrocast pre-registration frozen (`retrocast/nhtsa-recalls/`); "
             "no scorecards yet; no forward-validation labels yet.")
    L.append("")

    # 5) Calendar
    cal = _calendar_next_30(calendar_text, today)
    L.append("## 5) Calendar (next 30 days)")
    L += ([f"- {c}" for c in cal] or ["_Nothing in the next 30 days._"])
    L.append("")

    # 6) Orphan clock — assembled SEPARATELY so it always survives length-cap truncation. It is
    # the safety-relevant line; under a huge gate backlog it must not be the thing that gets cut.
    st = orphanlib.status(today, orphanlib.parse_ack_date(ack_text), decision_dates)
    ol = orphanlib.report_line(st)
    orphan_lines = ["## 6) Orphan clock", ol] if ol else []

    main_lines = "\n".join(L).rstrip().splitlines()
    reserve = len(orphan_lines) + 2
    if len(main_lines) + reserve > LENGTH_CAP:
        main_lines = main_lines[:LENGTH_CAP - reserve] + ["", "_(truncated at length cap; overflow → appendix)_"]
    parts = main_lines + (["", *orphan_lines] if orphan_lines else [])
    return "\n".join(parts).rstrip() + "\n"


def _decision_dates(repo_root: str) -> list:
    """Operator liveness from gate DECISIONs (SPEC-06 §1): the mtime of every decided or deferred
    gate file under QUEUE/{decided,pending}. Without this the orphan clock would rely on ACK alone
    and could falsely freeze an operator who stays active by deciding gates."""
    dates = []
    for sub in ("decided", "pending"):
        base = os.path.join(repo_root, "ops", "state", "QUEUE", sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            for fn in files:
                if not (fn.startswith("GATE-") and fn.endswith(".md")):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    g = gatelib.parse(open(fp, encoding="utf-8").read(), fp)
                except Exception:
                    continue
                if g.is_decided or g.defer_until is not None:
                    dates.append(date.fromtimestamp(os.path.getmtime(fp)))
    return dates


def compile_from_repo(repo_root: str, today: date, week_num: int) -> str:
    state = os.path.join(repo_root, "ops", "state")

    def _read(p, default=""):
        fp = os.path.join(repo_root, p)
        return open(fp, encoding="utf-8").read() if os.path.exists(fp) else default

    health = merged_health(repo_root)
    budget = json.loads(_read("ops/state/BUDGET.json", "{}") or "{}")
    pending = gatelib.load_pending(os.path.join(state, "QUEUE", "pending"))
    md = compile_report(health=health, pending_gates=pending, budget_data=budget,
                        calendar_text=_read("ops/state/CALENDAR.md"), ack_text=_read("ops/state/ACK"),
                        today=today, week_num=week_num, decision_dates=_decision_dates(repo_root))
    out_dir = os.path.join(repo_root, "ops", "reports", str(today.year))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"W{week_num:02d}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    return out
