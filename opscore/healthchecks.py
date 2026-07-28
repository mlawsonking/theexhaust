"""healthchecks.io provisioning (SPEC-03 §1). The external dead-man heartbeat is the one mandatory
piece of non-GitHub infra: a clock GitHub doesn't own, so a silently-stopped collector is an alarm,
never a discovery. This module turns the per-collector cron schedules (`.github/workflows/collect-*.yml`)
into healthchecks *cron checks* with a grace window sized to the firing cadence, creates/updates them
via the healthchecks API, and stores each ping URL as the `HC_<COLLECTOR>` Actions secret the live
`_collector.yml` already consumes.

Design notes:
- **Outcome-based:** collectors ping only after a validated snapshot is stored OR a same-hash dedupe
  (`unchanged` still pings success — see collectors/framework); a drift/failure withholds the ping.
  So the check's expected cadence == the *firing* cadence, and grace keys off the firing gap.
- **Grace = 1.5 x the max gap between consecutive firings** (SPEC-03 §1: "cadence x over-scheduling").
  This tolerates exactly one skipped/drifted firing without a false alarm (GitHub cron drift is
  unbounded and skips silently — the whole point of over-scheduling) while still catching a true stop.
- **Only create a check for a runner that is actually running.** A check for a not-yet-scheduled job
  goes 'down' the moment its grace elapses and false-alarms — so the weekly-session and site-publish
  checks in the SPEC-03 §1 budget are created only once those runners exist (see `--include` in the CLI).
- **`channels: "*"`** assigns every configured integration (add ntfy once in the HC dashboard and all
  checks inherit it). The topic strings stay in HC + Actions secrets, never in the repo.

The pure spec computation (`collector_specs`, `_cron_max_gap_hours`, `_grace_seconds`) is import-safe
and network-free so it is unit-tested offline; only `create_or_update_check` / `set_actions_secret`
touch the network, and only when an API key is supplied.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request

HC_API = "https://healthchecks.io/api/v3/checks/"
# cron day-of-week: 1=Mon..6=Sat, 0 or 7 = Sun. Python-week index Mon=0..Sun=6.
_DOW_TO_IDX = {0: 6, 7: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}


def _expand_field(field: str, lo: int, hi: int) -> list[int]:
    """Expand a cron field limited to the forms our fleet uses: '*' or a comma list of ints."""
    field = field.strip()
    if field == "*":
        return list(range(lo, hi + 1))
    out = []
    for part in field.split(","):
        part = part.strip()
        if not re.fullmatch(r"\d+", part):
            raise ValueError(f"unsupported cron field '{field}' (only '*' or int lists are handled)")
        out.append(int(part))
    return out


def _cron_max_gap_hours(cron: str) -> float:
    """Max gap (hours) between consecutive firings of a weekly-periodic cron. Requires dom='*' and
    month='*' (every collector in the fleet is day-of-week/hour based); raises loudly otherwise so a
    future collector using day-of-month can't get a silently-wrong grace."""
    parts = cron.split()
    if len(parts) != 5:
        raise ValueError(f"expected 5 cron fields, got {len(parts)}: {cron!r}")
    minute, hour, dom, month, dow = parts
    if dom.strip() != "*" or month.strip() != "*":
        raise ValueError(f"only dom='*' month='*' crons are supported (got dom={dom} month={month})")
    mins = _expand_field(minute, 0, 59)
    hours = _expand_field(hour, 0, 23)
    dows = _expand_field(dow, 0, 7)
    idxs = sorted({_DOW_TO_IDX[d] for d in dows})
    # firing offsets in hours from Monday 00:00, over one weekly period [0, 168)
    offsets = sorted(di * 24 + h + m / 60.0 for di in idxs for h in hours for m in mins)
    if not offsets:
        raise ValueError(f"cron matches no firings: {cron!r}")
    gaps = [offsets[i + 1] - offsets[i] for i in range(len(offsets) - 1)]
    gaps.append((offsets[0] + 168.0) - offsets[-1])  # wrap-around to next week
    return max(gaps)


def _grace_seconds(max_gap_hours: float) -> int:
    """Grace = 1.5 x max firing gap, rounded to whole hours, floor 1h."""
    hours = max(1, round(max_gap_hours * 1.5))
    return int(hours * 3600)


def _collector_name(filename: str) -> str:
    return re.sub(r"^collect-(.+)\.ya?ml$", r"\1", os.path.basename(filename))


def _secret_name(collector: str) -> str:
    return "HC_" + collector.upper().replace("-", "_")


def collector_specs(workflows_dir: str) -> list[dict]:
    """One healthchecks cron-check spec per `collect-*.yml`, derived from its cron. Sorted by name."""
    specs = []
    for fn in sorted(os.listdir(workflows_dir)):
        if not (fn.startswith("collect-") and fn.endswith((".yml", ".yaml"))):
            continue
        text = open(os.path.join(workflows_dir, fn), encoding="utf-8").read()
        m = re.search(r"cron:\s*['\"]([^'\"]+)['\"]", text)
        if not m:
            continue  # e.g. a dispatch-only collector — no dead-man cadence to size
        cron = m.group(1).strip()
        collector = _collector_name(fn)
        gap = _cron_max_gap_hours(cron)
        specs.append({
            "collector": collector,
            "secret": _secret_name(collector),
            "name": f"exhaust-collect-{collector}",
            "cron": cron,
            "tz": "UTC",
            "max_gap_hours": round(gap, 3),
            "grace": _grace_seconds(gap),
            "channels": "*",
            "tags": "exhaust collector",
        })
    return specs


def create_or_update_check(spec: dict, api_key: str) -> dict:
    """POST the check to healthchecks (idempotent via unique=['name']); returns the API JSON
    (carries `ping_url`). Network — only called under --apply with a real key."""
    body = json.dumps({
        "name": spec["name"], "schedule": spec["cron"], "tz": spec["tz"],
        "grace": spec["grace"], "unique": ["name"], "channels": spec["channels"],
        "tags": spec["tags"],
    }).encode("utf-8")
    req = urllib.request.Request(HC_API, data=body, method="POST",
                                 headers={"X-Api-Key": api_key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def set_actions_secret(secret_name: str, value: str, repo: str | None = None) -> None:
    """Store the ping URL as a GitHub Actions secret via the gh CLI (write-only; never printed)."""
    cmd = ["gh", "secret", "set", secret_name]
    if repo:
        cmd += ["--repo", repo]
    subprocess.run(cmd, input=value.encode("utf-8"), check=True)


def apply(workflows_dir: str, api_key: str, *, set_secrets: bool = True, repo: str | None = None) -> list[dict]:
    """Create/update every collector check and (optionally) store its ping URL as HC_<COLLECTOR>.
    Returns per-collector results {collector, secret, ping_url, secret_set}."""
    results = []
    for spec in collector_specs(workflows_dir):
        data = create_or_update_check(spec, api_key)
        ping_url = data.get("ping_url", "")
        secret_set = False
        if set_secrets and ping_url:
            set_actions_secret(spec["secret"], ping_url, repo=repo)
            secret_set = True
        results.append({"collector": spec["collector"], "secret": spec["secret"],
                        "ping_url": ping_url, "grace": spec["grace"], "secret_set": secret_set})
    return results
