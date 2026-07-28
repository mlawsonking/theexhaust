#!/usr/bin/env python
"""Injected-schema-drift drill (SPEC-01 §6 acceptance; SPEC-03 §2 drift table).

Proves the drift path END-TO-END on the REAL production collector object — not a unit-test
stand-in: `collectors.cms_deficiencies.build()` with its real name, real CsvSchema, real
`Collector.run`, a real on-disk state file, and the real weekly gate/alarm chain
(`opscore.weekly.file_collector_gates` + `opscore.alarms.AlarmBus`).

SAFETY (NEXT.md W-005 catch): the drill NEVER touches live R2. It builds a throwaway
LocalFSBackend root under a temp dir and a fetch() that returns bytes from memory — no network,
no R2 credentials read, nothing written inside the repo. Re-runnable any time:

    python ops/playbooks/drift_drill.py [--keep]

Asserts, in order:
  1. firing 1-3, drifted payload -> action=quarantined, alarm=True, heartbeat WITHHELD,
     object lands under quarantine/ and NOTHING is written under raw/ (no pollution);
  2. firing 3 -> drift_streak=3, paused=True, needs_gate='schema-drift-3x' (SPEC-03 §2);
  3. an identical drifted payload recurring -> quarantined-dup, alarm=False (anti-storm, §4);
  4. the weekly driver reads that state and files exactly ONE source gate + emits it on the
     gate topic; a second weekly pass files nothing (idempotent);
  5. recovery: a schema-clean payload -> stored, drift_streak reset, paused cleared
     ("collector keeps running (next firing may recover)", SPEC-03 §2).
Exit 0 = drill PASS.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from collectors import cms_deficiencies                       # noqa: E402
from collectors.framework import LocalFSBackend               # noqa: E402
from opscore import gates, weekly                             # noqa: E402
from opscore.alarms import AlarmBus, NullNtfySender           # noqa: E402

HEADER_OK = (",".join(cms_deficiencies.REQUIRED)).encode()
# The realistic drift: CMS renames one required column in a new vintage. Everything else is intact,
# so only the schema contract catches it — exactly the failure the quarantine exists for.
HEADER_DRIFTED = HEADER_OK.replace(b"Scope Severity Code", b"Scope/Severity Code")
ROW = b"015009,ACME NURSING,TX,2026-01-15,Health,F0684,Quality of Care,G\n"


def payload(header: bytes, n: int) -> bytes:
    return header + b"\n" + ROW * n


def check(label: str, cond: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}{(' — ' + detail) if detail else ''}")
    if not cond:
        raise SystemExit(f"DRILL FAILED at: {label}")


def keys(root: str, prefix: str) -> list[str]:
    base = os.path.join(root, prefix)
    out = []
    for dirpath, _d, files in os.walk(base):
        for f in files:
            out.append(os.path.relpath(os.path.join(dirpath, f), root).replace(os.sep, "/"))
    return sorted(out)


def run(root: str) -> None:
    archive = os.path.join(root, "archive")
    health_path = os.path.join(root, "ops", "state", "health", "cms-deficiencies.json")
    pend = os.path.join(root, "ops", "state", "QUEUE", "pending")
    os.makedirs(pend, exist_ok=True)
    os.makedirs(os.path.join(root, "ops", "state", "QUEUE", "decided"), exist_ok=True)

    storage = LocalFSBackend(archive)
    col = cms_deficiencies.build(storage=storage, health_path=health_path,
                                 heartbeat_url=None, repo_root=".")

    print("1. inject drift (first firing)")
    res = col.run(lambda max_bytes=None: (200, {}, payload(HEADER_DRIFTED, 1), "drill://cms-vintage"))
    check("firing 1: quarantined", res["action"] == "quarantined", json.dumps(res["missing"]))
    check("firing 1: alarm raised", res["alarm"] is True)
    check("firing 1: heartbeat withheld", res["heartbeat"] == "withheld(drift)", res["heartbeat"])
    check("firing 1: drift_streak=1", res["drift_streak"] == 1)

    print("2. anti-alarm-storm: the SAME drifted payload recurring (SPEC-03 §4)")
    dup = col.run(lambda max_bytes=None: (200, {}, payload(HEADER_DRIFTED, 1), "drill://cms-vintage"))
    check("quarantined-dup", dup["action"] == "quarantined-dup")
    check("no second alarm", dup["alarm"] is False)
    check("no new quarantine object", len(keys(archive, "quarantine")) == 1)

    print("3. two more DISTINCT drifted vintages -> 3 consecutive drifts")
    for i in (2, 3):
        res = col.run(lambda max_bytes=None, i=i: (200, {}, payload(HEADER_DRIFTED, i), "drill://cms-vintage"))
        check(f"firing {i}: quarantined", res["action"] == "quarantined")
        check(f"firing {i}: drift_streak={i}", res["drift_streak"] == i)

    print("4. raw/ not polluted; quarantine/ holds every DISTINCT drifted vintage")
    check("no raw/ objects at all", keys(archive, "raw") == [], str(keys(archive, "raw")))
    q = keys(archive, "quarantine")
    check("3 quarantined objects", len(q) == 3, "; ".join(q))
    check("quarantine path is quarantine/cms-deficiencies/YYYY/MM/DD/",
          all(k.startswith("quarantine/cms-deficiencies/") for k in q))

    print("5. auto-pause + gate request on the 3rd consecutive drift (SPEC-03 §2)")
    check("paused", res["paused"] is True)
    rec = json.load(open(health_path))["collectors"]["cms-deficiencies"]
    check("needs_gate=schema-drift-3x", rec.get("needs_gate") == "schema-drift-3x", str(rec.get("needs_gate")))
    check("state file has no last_hash promotion", "stored" not in (rec.get("last_action") or ""))

    print("6. the pause is ENFORCED — a paused collector does not fetch at all (W-005c/F07)")
    fetched = []

    def counting_fetch(max_bytes=None):
        fetched.append(1)
        return 200, {}, payload(HEADER_OK, 5), "drill://cms-vintage"

    while_paused = col.run(counting_fetch)
    check("action=paused", while_paused["action"] == "paused", while_paused["action"])
    check("no fetch was made", fetched == [])
    check("heartbeat withheld(paused)", while_paused["heartbeat"] == "withheld(paused)")
    check("a clean payload does NOT silently un-pause it", col.run(counting_fetch)["action"] == "paused")
    check("still no fetch", fetched == [])

    print("7. weekly driver files exactly one source gate + emits it (idempotent)")
    bus = AlarmBus(sender=NullNtfySender(), topics={"alarm": "t", "gate": "t", "pulse": "t"},
                   ledger_path=os.path.join(root, "ops", "state", "ALARMS.jsonl"))
    from datetime import date
    today = date(2026, 7, 28)
    health = {"collectors": {"cms-deficiencies": rec}}
    filed = weekly.file_collector_gates(root, health, today)
    check("one gate filed", filed == ["collector-cms-deficiencies-schema-drift-3x"], str(filed))
    pending = gates.load_pending(pend)
    check("gate is pending, type=source", len(pending) == 1 and pending[0].type == "source",
          f"{pending[0].slug} / {pending[0].type}")
    check("gate is undecided on arrival", not pending[0].is_decided)
    bus.alarm(f"Collector cms-deficiencies quarantined 3x — {rec['drift_missing']}", pending[0].path, today=today)
    check("alarm recorded on the alarm topic", bus.sender.sent[0]["topic"] == "t"
          and bus.sender.sent[0]["priority"] == "high")
    check("re-run files nothing (no gate spam)", weekly.file_collector_gates(root, health, today) == [])

    print("8. operator re-enables via the gate -> collection resumes and the streak clears")
    h = json.load(open(health_path))
    h["collectors"]["cms-deficiencies"].update(paused=False, needs_gate=None)   # the operator's decision
    json.dump(h, open(health_path, "w"))
    ok = col.run(lambda max_bytes=None: (200, {}, payload(HEADER_OK, 5), "drill://cms-vintage"))
    check("stored", ok["action"] == "stored", json.dumps({k: ok[k] for k in ("rows", "volume_band")}))
    rec2 = json.load(open(health_path))["collectors"]["cms-deficiencies"]
    check("drift_streak reset to 0", rec2["drift_streak"] == 0)
    check("stays un-paused", rec2.get("paused") is False)
    check("raw/ now holds exactly the recovered vintage + manifest", len(keys(archive, "raw")) == 2,
          "; ".join(keys(archive, "raw")))
    # (volume_band='anomaly' is expected here: a 5-row fixture is below the real 100k row_floor.)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="keep the throwaway drill root for inspection")
    args = ap.parse_args()
    root = tempfile.mkdtemp(prefix="drift-drill-")
    print(f"DRIFT DRILL — throwaway root {root} (LocalFS only; live R2 untouched)")
    try:
        run(root)
    finally:
        if args.keep:
            print(f"kept: {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)
    print("\nDRIFT DRILL: PASS — quarantine + alarm + no raw/ pollution + 3x auto-pause + gate + recovery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
