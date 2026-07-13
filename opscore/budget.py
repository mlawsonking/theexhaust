"""Budget governor (SPEC-04 §4). Steady-state metered spend is structurally $0 (no Anthropic
key in R1; R2 sessions are subscription-side). This module enforces the covenant on the only
two cash surfaces: gated metered runs (cap enforced in code, actuals ledgered) and R2 storage
(projection from manifests, alert at >$5/mo)."""
from __future__ import annotations

import json
from datetime import date

# Cloudflare R2 (SPEC-01 §3 / research §6): 10 GB-month free, then $0.015/GB-month, egress free.
R2_FREE_GB = 10.0
R2_USD_PER_GB_MONTH = 0.015
STORAGE_ALERT_USD_MONTH = 5.0


class CapExceeded(Exception):
    pass


class GatedRun:
    """Token-cost accountant for one approved metered run (SPEC-02 §3). Aborts in code at the
    hard cap so a runaway can never exceed the operator-approved ceiling."""

    # Haiku 4.5 batch pricing (research §15 / R15), USD per token.
    IN_PER_TOK = 0.50 / 1_000_000
    OUT_PER_TOK = 2.50 / 1_000_000

    def __init__(self, run_id: str, gate_id: str, estimate_usd: float, hard_cap_usd: float):
        self.run_id = run_id
        self.gate_id = gate_id
        self.estimate_usd = estimate_usd
        self.hard_cap_usd = hard_cap_usd
        self.actual_usd = 0.0

    def charge(self, in_tokens: int, out_tokens: int) -> float:
        cost = in_tokens * self.IN_PER_TOK + out_tokens * self.OUT_PER_TOK
        if self.actual_usd + cost > self.hard_cap_usd:
            raise CapExceeded(
                f"run {self.run_id}: ${self.actual_usd + cost:.4f} would exceed cap ${self.hard_cap_usd:.2f}"
            )
        self.actual_usd += cost
        return self.actual_usd

    def to_ledger(self, today: date) -> dict:
        return {"run_id": self.run_id, "gate_id": self.gate_id, "estimate": self.estimate_usd,
                "cap": self.hard_cap_usd, "actual": round(self.actual_usd, 4), "date": today.isoformat()}


class Budget:
    def __init__(self, data: dict):
        self.data = data
        self.data.setdefault("metered_runs", [])
        self.data.setdefault("storage", {"r2_gb": 0.0, "projection_usd_mo": 0.0,
                                         "alert_threshold_usd_mo": STORAGE_ALERT_USD_MONTH})
        self.data.setdefault("annual_lines", [])

    @classmethod
    def load(cls, path: str) -> "Budget":
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))

    def save(self, path: str, today: date | None = None):
        self.data["updated"] = (today or date.today()).isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def record_run(self, run: GatedRun, today: date):
        self.data["metered_runs"].append(run.to_ledger(today))

    @staticmethod
    def storage_cost(gb: float) -> float:
        return max(0.0, gb - R2_FREE_GB) * R2_USD_PER_GB_MONTH

    def set_storage(self, gb: float):
        self.data["storage"]["r2_gb"] = round(gb, 4)
        self.data["storage"]["projection_usd_mo"] = round(self.storage_cost(gb), 4)

    def storage_alarm(self) -> bool:
        return self.data["storage"]["projection_usd_mo"] > self.data["storage"].get(
            "alert_threshold_usd_mo", STORAGE_ALERT_USD_MONTH)

    def overrun_alarms(self) -> list[dict]:
        """Gated runs whose actual exceeded estimate — alarm if > 2x (SPEC-03 §2)."""
        out = []
        for r in self.data["metered_runs"]:
            est = r.get("estimate") or 0
            if est and r.get("actual", 0) > 2 * est:
                out.append(r)
        return out

    def month_metered_usd(self, yyyymm: str) -> float:
        return round(sum(r.get("actual", 0) for r in self.data["metered_runs"]
                         if str(r.get("date", "")).startswith(yyyymm)), 4)
