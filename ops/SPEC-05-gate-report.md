# SPEC-05 — The weekly gate report (operator interface)

*Contract for Michael's ~1 hour. Compiled, never hand-written. If the report takes him >1 hr/week sustained, the report is wrong, not Michael.*

## 1. Delivery

- Compiled by the weekly R2 session → `ops/reports/{YYYY}/W{ww}.md`, committed; ntfy `exhaust-pulse` with title + counts + link.
- Also readable cold: every report is self-contained (no "see last week").

## 2. Fixed shape (in this order)

```
# The Exhaust — week {ww}, {date range}
**You need to decide {N} things. Everything else is green.**   ← or: "Nothing needs you this week."

## 1) Decisions ({N})
For each pending gate, ≤5 lines: title · type · why-now · recommended option ·
default-if-ignored + expiry date · link to the gate file.
Ordered: legal > spend > named-entity > methodology > new-index > source > comms.

## 2) Health board
Collectors: {green}/{total} ✅ | quarantines this week | heartbeat misses | paused collectors.
Storage: {GB} (${proj}/mo). Budget: metered ${x} this month vs ${est}; annual lines next due.
One line per non-green item with its alarm link. Alarm budget status.

## 3) The week's output
Artifacts posted per index (counts + one example link) · scorecard movements
(official numbers arrived; divergence flags if any) · corrections log entries ·
citations/mentions detected (search + referrer sweep; zero is stated plainly).

## 4) Flywheel
Retrocast/scorecard pages updated · forward-validation labels accrued (layoffs) ·
Track Record deltas. One paragraph max.

## 5) Calendar (next 30 days)
Grant deadlines, statehouse dates, official release days, renewals (from CALENDAR.md).

## 6) Orphan clock
"Operator last active {date} ({n} weeks). {4-n} weeks to autonomous freeze."  (omit when n=0)
```

## 3. Rules

- **Decisions are the headline.** If §1 is empty, the subject line says so and the operator can archive unread — that is a *successful* week, not a failure of the report.
- Every claim links: gate file, HEALTH entry, artifact, receipt. No unlinked assertions.
- Length cap: 150 lines. Overflow goes to appendix files, linked.
- Reading the report is optional; **acting on gates is the only required operator labor.** ACK semantics: any operator commit / gate decision / touch of `ops/state/ACK` resets the orphan clock. The report never demands a reply.
- Monthly audit (SPEC-02) appends a one-page section to that week's report: budget reconciliation, mute review, ToS re-verify rotation result, covenant spot-check.

## 4. Acceptance criteria (BUILD-02)

- Two consecutive real reports compile with live state, inside format + length caps, links resolving.
- A week with zero pending gates produces the "nothing needs you" subject and a ≤40-line report.
- Operator dry-run: Michael reads one report and decides all gates in ≤1 hr, measured; format friction he reports becomes a BUILDLOG fix before BUILD-04.
