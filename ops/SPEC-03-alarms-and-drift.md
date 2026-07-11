# SPEC-03 — Alarms, dead-man switches, drift detectors

*Contract for the watching layer. Philosophy: alarms are rare and real; silence is information only if its absence is alarmed.*

## 1. The external dead-man heartbeat (mandatory, constitutional)

- **Provider:** healthchecks.io free tier (20 checks). Checks are **outcome-based**: a collector pings its check only after a validated snapshot is stored (never "workflow started").
- **Check budget:** ≤18 collector/logical checks (group low-stakes collectors into shared logical checks with per-collector detail in `HEALTH.json`), +1 site-publish check, +1 weekly-session check.
- **Grace windows:** per-collector, sized to cadence × over-scheduling (e.g., daily target → 36 h grace). A missed grace → healthchecks fires → ntfy `exhaust-alarm`.
- **Why external:** GitHub cron drift is unbounded and silently skips; only a clock GitHub doesn't own can catch a full stop. This is the one mandatory piece of non-GitHub infrastructure.

## 2. Drift detectors (run inside R1 jobs)

| Detector | Trigger | Action |
|---|---|---|
| **Schema drift** | field missing/renamed/retyped vs. contract | quarantine snapshot; alarm; collector keeps running (next firing may recover); 3 consecutive drifts → auto-pause collector + gate item |
| **Volume anomaly** | row count < 50% or > 300% of trailing 8-week median | store (data is data) + flag in manifest + alarm at < 25% or > 500% |
| **Silence upstream** | source returns 200 but content hash unchanged for 3× expected refresh | stale flag in `HEALTH.json`; feeds the stale-data banner (SPEC-06); no alarm unless an official release date was missed |
| **Divergence (Google-Flu-Trends clause)** | on official release days, index vs. official outside the published calibration band | auto-flag on the index page + gate item for methodology review; **never** silent recalibration |
| **Budget** | R2 projection > $5/mo; any gated-run actual > estimate | gate report line; alarm if > 2× estimate |
| **Orphan clock** | no operator activity 3 weeks | warning in report + ntfy; at 4 weeks → SPEC-06 engages |

## 3. ntfy taxonomy

Three topics, unguessable names (topic strings are the only auth on ntfy.sh — generate long random suffixes, store as secrets):

| Topic | Content | Priority | Volume target |
|---|---|---|---|
| `exhaust-alarm-<rand>` | heartbeat misses, schema drift, collector 3-strikes, divergence flags, budget breaches | high (phone-audible) | **≈ 0/week in steady state** |
| `exhaust-gate-<rand>` | new gate items (title + one-line + link) | default | a few/week max |
| `exhaust-pulse-<rand>` | weekly report ready; monthly audit summary; retrocast/publish successes | low | ~1–2/week |

## 4. The alarm budget (anti-fatigue, constitutional intent)

> 5 alarm events/week sustained 2 consecutive weeks → automatic gate item: **fix the root cause or mute with a recorded decision**. Muting without a decision file is prohibited. The monthly audit reviews every active mute.

## 5. Corrections detection

A recomputation that changes an already-published number beyond its stated tolerance auto-creates: a corrections-log entry (auto-publishes — accuracy-as-control covenant), a flag on the affected page, and a gate item if the cause implies methodology or data-quality fault. The *narrative* response, if any, is operator-gated.

## 6. Acceptance criteria (BUILD-02)

- Kill one collector for a simulated week → healthchecks fires within grace + ntfy alarm received.
- Injected schema drift quarantines, alarms, and auto-pauses after 3 consecutive.
- Volume detector flags a synthetic 10× snapshot.
- A forced divergence beyond band flags the (test) index page and files a gate item.
- All three ntfy topics deliver to the operator's phone; alarm topic silent otherwise for 7 days.
