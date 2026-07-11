# SPEC-06 — Orphan protocol & degraded modes

*Contract for grace under neglect. The system's degraded modes are designed states, not failures: boring, not broken.*

## 1. The orphan clock

- **Activity** = any operator-authored commit, any gate `DECISION:`, or a touch of `ops/state/ACK`.
- Week 3 without activity → warning line in the report + one ntfy `exhaust-gate` nudge.
- **Week 4 → orphan mode engages automatically.** No operator consent needed to *enter* (entering is safe); exiting is instant: any activity.

## 2. Orphan mode (autonomous freeze)

| Keeps running | Freezes |
|---|---|
| **All archival collectors** (the mission's spine — never stops) | Execution of anything gate-shaped: no new indexes, no methodology changes, no named-entity items (pending gates hold; nothing expires *into* action — expiry is always no-action anyway) |
| Frozen-methodology recomputation + aggregate artifact posting + scorecard chaining | Named-entity **tiers**: new named items stop publishing; existing named pages hold with a paused banner |
| Heartbeats, alarms (rerouted: alarm digest weekly instead of instant, except heartbeat-total-failure which stays instant) | Journalist-gift sends, external comms |
| Site + feeds, with a banner: *"The Exhaust is operating autonomously since {date}. Aggregate indexes update automatically under frozen, published methodologies. Named-entity tiers and new launches are paused."* | Gated spend (nothing to approve it) |
| Monthly digest replaces the weekly report | Weekly R2 session drops to monthly |
| A monthly keepalive commit (prevents GitHub's 60-day cron disablement) | |

**Insurance interplay (constitutional honesty):** orphan mode freezes exactly the surfaces that make media-liability insurance load-bearing. At the policy's renewal date while orphaned, the renewal gate defaults to *lapse-to-GL-only with named tiers frozen* — documented, conscious, and reversible on return.

## 3. Floor mode (operator-chosen austerity, $50/mo covenant)

Distinct from orphan (operator is present, money is tight). A config flag: collectors continue; cadence drops to weekly/monthly tiers; no backfills; monthly report; named tiers optional-frozen (drives the insurance decision); R2 lifecycle keeps raw immutable but pauses derived rebuilds. Everything restartable without data loss — the archive never degrades.

## 4. Stale-data posture (government-continuity, live issue since Oct 2025)

- Upstream silence detection (SPEC-03 §2) marks a source stale after 3× its expected refresh with no official release.
- Every index page renders a stale banner naming the last-good vintage: *"{Official source} last updated {date}; this index chains to that vintage."*
- Retrocasts always run against **archived flat files** (the retrocast-of-record), never against live endpoints, so upstream freezes cannot corrupt published history.
- If an official series *resumes* with revisions, the divergence detector treats the revision like any official arrival: rechain, flag if out of band.

## 5. Recovery & succession

- **Recovery:** one operator action exits orphan mode; the next weekly report includes an "while you were out" digest (gates held, alarms digested, anything auto-paused).
- **Succession seed (year-3 material, encoded now):** because every decision is a public gate file, every method is versioned, and every pipeline is spec'd in `ops/`, a successor operator's onboarding is: read `OBSERVATORY.md` → read the specs → claim the ntfy topics + secrets. The constitution's covenants bind them; the do-not-collect register survives them. Nothing lives only in Michael's head — this spec exists so that sentence stays true.

## 6. Acceptance criteria (BUILD-02 for the clock; BUILD-04 for banners)

- Simulated 4-week silence: freeze engages, banner renders, collectors uninterrupted, alarm rerouting verified, keepalive commits.
- One operator commit exits orphan mode; "while you were out" digest generated.
- Stale-banner test: freeze a test source's fixture → banner appears with correct vintage; unfreeze → banner clears.
- Floor-mode flag flips cadences without data loss; flipping back restores.
