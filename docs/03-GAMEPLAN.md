# 03-GAMEPLAN — The Exhaust, Phase 3 architecture

*Fable, 2026-07-11. Status: complete. Predecessors: [`01-VISION.md`](01-VISION.md) (ideation), [`02-RESEARCH.md`](02-RESEARCH.md) (validation). Successor: `04-BUILDLOG.md` (Opus, Phase 4).*

---

## 0. Handoff note to Opus (Phase 4)

Build **exactly this**. The gameplan locks the portfolio, the sequence, and the autonomy architecture; the nine specs in [`ops/`](../ops/) are the contracts your code must satisfy — each has acceptance criteria, and a BUILD item is done only when its criteria pass against live sources. Three standing orders: (1) **Re-verify before you depend** — every corpus row in research §5 carries a verified date; re-check a row live before building on it, and if reality has drifted from the spec, STOP and file a gate item rather than improvising silently. (2) **Archival first** — BUILD-01 outranks everything; every week without collectors is perishable data lost forever, and the fleet must be running while you build everything else. (3) **The covenants are code review** — the do-not-collect register, the scraping-hygiene rules, and the naming gate are not guidelines; a pipeline that violates one is a failed build regardless of how well it works. Work the BUILD queue in §6 in order, one or more items per session, to acceptance, verified, committed, logged in `04-BUILDLOG.md` (the OnScript multi-session pattern). No implementation code exists yet; everything before this phase produced documents only.

---

## 1. What changed, and what this document does

Phase 2 killed cleanly. The reconciliation in one paragraph: the thesis, five-engine architecture, and retrocast doctrine survived; the **first published retrocast** moved off Shadow Layoffs (no free posting history — vision §6.2's own escape hatch) to **NHTSA Shadow Recalls**, with **Hospital/Care Distress** the immediate second; Layoffs launches in parallel as the **observational distribution flagship** (WARN Watch + posting diffs, publishable day one under the naming-gate exception) and earns its precision/recall the slow way, forward. Five corpora are dead and now constitutionally unrevivable without fresh sign-off (Legacy.com, GoFundMe, poweroutage.us redistribution, SERFF/NAIC automation, Amazon/Glassdoor/Indeed reviews). The name is **The Exhaust** (`theexhaust.org`), "observatory" demoted to descriptor. The spend truth is ~$0–3/month infra, not $0. And the single field-wide differentiator that survived a 132-entity adversarial prior-art sweep is the one we already made constitutional: **the published retrocast precision/recall scorecard — no live public entity in any of our lanes does it.**

This document does three things: **locks the reconciled portfolio and calendar** (§2), **designs the autonomy architecture** — the looping-and-control machine that makes multi-year low-touch operation real (§3–§5), and **hands Phase 4 its marching orders** as a BUILD queue with acceptance criteria (§6). The covenant amendments the research demanded (its §6) are enacted in [OBSERVATORY.md](../OBSERVATORY.md) as of this session; §9 summarizes them.

---

## 2. The reconciled portfolio and calendar (locked)

### 2.1 Launch order

| Slot | Index | Mode | Why this slot |
|---|---|---|---|
| **First retrocast** | **NHTSA Shadow Recalls** | Full retrocast → publish P/R + lead-time distribution | Cleanest falsification of the founding thesis; both sides official + free + archived *now*; "signal N days before the recall" is the strongest press hook in the portfolio; starts the recalls naming-gate clock |
| **Distribution flagship (parallel)** | **Shadow Layoffs (observational)** | WARN Watch + posting-diff receipts; forward-validation scorecard from week one | Operator's favorite; born-shareable observational facts; no retrocast claim made until forward labels accrue (~12–18 mo) |
| **Second retrocast** | **Hospital/Care Distress** | PBJ staffing → CMS harm deficiencies; hard CCN key | Cleanest data in the portfolio; leak-free by construction; rural-closure leg is the year-2 flagship |
| **Session-timed** | **Legislative Authorship** | Replicate the 2019 method → run live Jan–Apr 2027, aggregate/observational framing | Statehouse calendar dictates timing; text-provenance engine ports from OnScript |
| **Journalist gift** | **FOIA Health micro-index** | Tiny build, MuckRock read API | Relationship wedge with the citing class |
| **Q2 2027** | **Grocery/Shrinkflation (forward-first)** + **Say-Do pilot** | Kroger basket (after the human ToS read gate) + mouseprint shrinkflation retrocast; Say-Do differentiates on retrocast + tight same-bill linkage | Full-basket retrocast is dead; forward collection starts at BUILD-01 anyway. Say-Do is the default contested-lane pilot because it reuses the OnScript `congress-press` corpus (cheapest build) — 311 follows in Q3 |
| **Q3 2027** | Track Record page v1, **Bank Stress (aggregate-only, permanently)**, first 311 city, Mortality groundwork (CDC harness + permissioned-panel outreach only, no publication) | The flywheel surfaces |
| **Deferred / link-don't-compete** | Wages, Small-Biz (thin overlays only if a retrocast clears), Insurability (residual-market portals + per-state filings path; NAIC 2027 report as future anchor), Corporate Distress capstone (year 2–3), Mortality publication (year 2, gated on panel + shield) | Per research verdicts |
| **Dead** | Medical-Debt (GoFundMe), J-14 poverty-timed pricing, full-basket inflation retrocast, Amazon-review recalls leg | Do-not-collect register / published null / closed |

### 2.2 Grocery pilot metros (decided)

Anchor: **Dallas–Fort Worth** (operator's Texas proxy; San Antonio isn't a BLS monthly metro). Plus **New York–Newark** (largest, guaranteed monthly cadence) and **Phoenix** (Sun Belt contrast). Phase 4 pre-flight MUST confirm each metro's SAF11 series cadence in the BLS catalog before the workbook freezes; designated swap if Phoenix fails cadence: **Chicago**.

### 2.3 The year-1 calendar (research §10, now with BUILD numbers)

| When | What | Exit criteria |
|---|---|---|
| Now → Q3 2026 | BUILD-00 foundations, **BUILD-01 archival fleet**, BUILD-02 ops core | collectors green 7 consecutive days; heartbeat + gate loop live |
| Q4 2026 | BUILD-03 NHTSA retrocast published; BUILD-04 public launch (site, WARN Watch, posting-diffs) behind the launch gate (LLC + insurance + sign-off) | first credibility artifact public; artifacts self-posting 2 weeks unattended |
| Q1 2027 | BUILD-05 hospital retrocast; BUILD-06 workbook compiler; BUILD-07 legislative authorship (in-session) + FOIA micro | three retrocasts/scorecards public; statehouse artifacts in-session |
| Q2 2027 | BUILD-08 grocery forward pilot + shrinkflation retrocast; BUILD-09 Say-Do pilot | weekly metro artifact; CPI-day divergence chart; Say-Do scorecard v0 |
| Q3 2027 | BUILD-10 Track Record page, bank aggregate index, first 311 city; mortality groundwork | flywheel visibly turning |

**Year-1 definition of done (unchanged from research):** NHTSA retrocast published with P/R + lead-time; Layoffs observational live with forward scorecard; Hospital retrocast published; WARN Watch + one statehouse index + FOIA micro self-posting; one external citation; cash ≈ domains + LLC + ~$2–3/mo R2 + a few gated ~$90 backfills + insurance at launch.

---

## 3. The autonomy architecture

This is the thing that makes the project different: a machine that runs for years, alone, up to decision gates — and *only* up to decision gates. Full contracts live in the nine specs; this section is the map.

### 3.1 Two runtimes

- **R1 — the deterministic runtime (GitHub Actions, public repo, standard runners).** Archival collectors, schema validation, index recomputation on frozen methodology, site builds, artifact compilation and posting, heartbeat pings. **No metered LLM calls, ever** — R1 is pure code. Free compute is a covenant, and cron drift is its known disease: every job over-schedules (15–30 min windows, odd minutes, never `:00`), dedupes by snapshot hash, chunks under the 6-hour cap, and reports to the external heartbeat. → [`SPEC-02`](../ops/SPEC-02-scheduling.md)
- **R2 — the semantic runtime (scheduled Claude Code sessions, operator's box, subscription).** Windows Task Scheduler → `claude -p` headless with a playbook from `ops/playbooks/`. The **weekly ops session** compiles the gate report, triages alarms, spot-verifies pipelines, and dies clean; a **monthly audit session** goes deeper (alarm budget, storage/budget reconciliation, covenant spot-checks). Construction sessions (Phase 4) are operator-started. Every session obeys the session contract: read the constitution → check phase/model → execute playbook → verify → commit → update state → notify → exit. The 4080 carries local embeddings/classifiers; anything needing metered API becomes a **gated run** with a pre-estimate. → [`SPEC-02`](../ops/SPEC-02-scheduling.md)

### 3.2 The state layer (how the machine remembers)

Small machine-readable files in-repo, written by jobs, read by the report compiler and every session: `ops/state/HEALTH.json` (per-collector last-success timestamps — the heartbeat's source of truth), `ops/state/QUEUE/` (gate items pending/decided), `ops/state/BUDGET.json` (metered spend ledger, R2 storage), `ops/state/CALENDAR.md` (deadlines), `ops/state/ACK` (operator liveness for the orphan clock). State is the interface between runtimes: R1 writes facts, R2 writes judgment, the operator writes decisions.

### 3.3 The five loops

1. **Collect** (R1, continuous): archival fleet → R2 object storage, immutable, schema-validated, quarantined on drift. → [`SPEC-01`](../ops/SPEC-01-archival-fleet.md)
2. **Compute** (R1, per-index cadence): frozen-methodology index runs → numbers + receipts bundles → site + feeds + Bluesky. Autonomous for launched aggregate indexes; anything novel queues a gate.
3. **Watch** (R1 + external): heartbeat misses, schema drift, volume anomalies, official-number divergence (the Google-Flu-Trends clause, automated) → ntfy alarms and auto-flags. → [`SPEC-03`](../ops/SPEC-03-alarms-and-drift.md)
4. **Judge** (R2 weekly + operator): gate report compiled from state; operator spends ≤1 hr; decisions land as files; next runs pick them up. → [`SPEC-04`](../ops/SPEC-04-permission-map.md), [`SPEC-05`](../ops/SPEC-05-gate-report.md)
5. **Degrade** (automatic): missed weeks → orphan protocol (freeze gated surfaces, keep collecting, banner, monthly cadence); federal data freezes → stale-data posture. Degraded mode is *boring, not broken*. → [`SPEC-06`](../ops/SPEC-06-orphan-protocol.md)

### 3.4 The scaling mechanism

Adding index N+1 must cost a workbook, not a system: a hand-written `WORKBOOK.md` (the only artisanal artifact, authored at gate time) is compiled into the index's full directory — bounded weekly jobs with acceptance criteria, retrocast harness config, artifact templates, alarm thresholds, cron and heartbeat wiring. The compiler output is itself a gate item; approving it *is* launching the index. → [`SPEC-07`](../ops/SPEC-07-workbook-compiler.md)

Two shared services make every index honest: the **retrocast harness** (one falsification protocol — pre-registered spec committed *before* results are computed, temporal splits, matched controls, published P/R + lead-time + calibration, forward-validation mode for layoffs-class indexes) and the **entity resolver + receipts store** (tiered resolution T0 hard keys → T3 gated LLM adjudication, append-only resolution ledger, every published number backed by an immutable evidence bundle). → [`SPEC-08`](../ops/SPEC-08-retrocast-harness.md), [`SPEC-09`](../ops/SPEC-09-entity-resolver-receipts.md)

---

## 4. The permission map (summary — contract in SPEC-04)

**Runs autonomously, no gate:** archival collection within the approved source list; schema validation and quarantine; index recomputation on frozen methodology; compilation and posting of cadence/anomaly artifacts for **already-launched aggregate indexes**; site and feed rebuilds; heartbeat and alarms; corrections *detection* (auto-flag + auto-log entry); scorecard updates as official numbers arrive; internal drafts of anything.

**Hard-stopped pending the operator (a gate file, ntfy'd, safe default = do nothing):** publishing any **new index** or artifact type; any **methodology or threshold change** on anything published (republishes the backtest by doctrine); any **named-entity** publication or tier unlock (per the naming gate; banks: permanently sealed); **new source onboarding** or any ToS-surface change; revival of any **do-not-collect** item (double-locked: gate + fresh written sign-off); any **metered spend** (pre-estimate attached, ~$90-class backfills included); any **paid service**; anything with **legal surface** (C&D responses — the transparency-log *entry* auto-publishes, the *response* is gated); external communications beyond scheduled artifacts (press replies, the journalist-gift list, permissioned-panel outreach); grant applications in the operator's name.

**The budget governor** enforces the spend covenant in code: steady-state metered spend is $0 by construction (no key in R1; R2 sessions run subscription-side); every gated run carries an estimate, a hard cap, and lands in `BUDGET.json`; monthly reconciliation appears in the gate report; storage alert at >$5/mo.

---

## 5. The operator interface (summary — format in SPEC-05)

One **weekly gate report**, compiled automatically, delivered as a repo file + ntfy link. Fixed shape: decisions needed (each ≤5 lines with evidence links and a stated safe default) → health board (collectors, storage, budget) → the week's numbers (artifacts posted, citations detected, scorecard movement) → calendar (next 30 days) → a single-line "nothing needs you this week" when true. Target: ≤15 minutes to read, ≤45 to decide. Deciding = editing a gate file's `DECISION:` line (GitHub web edit is enough) or telling any Claude session, which commits it. Any operator commit, gate decision, or touch of `ops/state/ACK` resets the orphan clock (threshold: **4 missed weeks**, then the system freezes its gated surfaces and keeps collecting — [`SPEC-06`](../ops/SPEC-06-orphan-protocol.md)). Alarm philosophy: alarms are rare and real; a sustained >5 alarm-events/week for 2 weeks is itself a gate item ("fix root cause or mute with a decision") — alert fatigue is a named failure mode.

---

## 6. Phase 4 BUILD queue (the marching orders)

Each item: scope → acceptance criteria. Opus works them in order; parallelize only where noted. Operator errands (⚑) are interleaved where they block.

**BUILD-00 — Foundations.** ⚑ Operator: buy `theexhaust.org` (WHOIS-private) + TESS check; create public GitHub repo `theexhaust` and push; Cloudflare account (R2 bucket `exhaust-archive` + custom domain for free egress; Pages project); healthchecks.io + ntfy topics (unguessable names); Actions secrets (R2 keys, NTFY, BSKY later). Opus: repo hygiene, state-layer scaffolding, `04-BUILDLOG.md` opened. *Accept:* push + a hello-world Action runs green; R2 write/read via custom domain verified; ntfy test received on the operator's phone.

**BUILD-01 — Archival fleet v1 (outranks everything).** Collectors per [`SPEC-01`](../ops/SPEC-01-archival-fleet.md), priority order: (1) CMS PBJ + Health Deficiencies snapshots (CMS overwrites!), (2) WARN top-10 states by volume, then the rest over subsequent weeks, (3) ATS full-board snapshots for the seed universe (~3–5k boards: layoffs.fyi companies + WARN appearers + major-index lists), (4) NHTSA complaints delta, (5) CPSC recalls CSV, (6) model-bill pages (ALEC current + SiX; ALEC-Exposed via Wayback only), (7) Kroger basket — **collector built but OFF until the human ToS read gate clears** ⚑, (8) EDGAR 8-K stream, FDIC quarterlies, mouseprint, EIA-861 annuals. Every collector: schema contract, quarantine path, heartbeat check, dedupe-by-hash, politeness per covenant (and the 403 ladder in SPEC-01 — datacenter-blocked-but-public sources may fall back to the operator box at identical politeness; bot-challenged sources STOP and gate). *Accept:* 7 consecutive green days across all enabled collectors; a restore drill (pull yesterday's snapshot from R2, revalidate schema) passes; zero covenant violations on review.

**BUILD-02 — Ops core.** State layer, alarm bus + drift detectors ([`SPEC-03`](../ops/SPEC-03-alarms-and-drift.md)), gate mechanics ([`SPEC-04`](../ops/SPEC-04-permission-map.md)), budget governor, gate-report compiler v1 ([`SPEC-05`](../ops/SPEC-05-gate-report.md)), weekly R2 session scheduled and live ([`SPEC-02`](../ops/SPEC-02-scheduling.md)). *Accept:* an injected fake schema-drift quarantines + alarms correctly; a test gate item round-trips (created → ntfy → decided → consumed); two consecutive weekly reports compile with real health data; orphan clock ticks and resets on ACK.

**BUILD-03 — Retrocast harness + the NHTSA retrocast.** Harness per [`SPEC-08`](../ops/SPEC-08-retrocast-harness.md); then: pre-register the NHTSA spec (commit before computing), run complaints→recall signature retrocast on the archived flat files, produce P/R + lead-time + calibration, pass the hostile-review checklist (one adversarial session that tries to break it before publish), publish the retrocast report + scorecard page (site v0 = this page). ⚑ Launch gate: LLC formed (Texas, ~$300, no franchise-tax exposure at this scale) + insurance decision (media policy $500–1,800/yr recommended; GL-with-advertising-injury $350–900/yr acceptable minimum for the observational-only period; **full media policy required before any named-entity tier ever unlocks**) + operator sign-off. *Accept:* pre-registration hash predates results in git history; scorecard JSON validates; hostile checklist zeroed; the report is publicly reachable.

**BUILD-04 — Public launch (the distribution flagship).** Site v1 on Cloudflare Pages (index pages, methodology-as-interview, corrections + transparency logs, receipts links, stale-data banners wired); WARN Watch (unified feed, per-state pages, alerts); posting-diff observational pages + forward-validation scorecard scaffold; `@theexhaust.org` Bluesky via TXT DNS ⚑, RSS/JSON feeds; artifact compiler posting on cadence. *Accept:* two weeks fully unattended — artifacts post on schedule, heartbeats green, zero manual interventions; a WARN notice appearing in a state feed reaches Bluesky/RSS within one collector cycle with receipts attached.

**BUILD-05 — Hospital/Care retrocast.** PBJ staffing → harm-deficiency signature per harness; pre-registered; published with scorecard. County-level care-fragility aggregate page (named-facility tier stays gated). *Accept:* same bar as BUILD-03.

**BUILD-06 — Workbook compiler v1.** Per [`SPEC-07`](../ops/SPEC-07-workbook-compiler.md); compile the Legislative-Authorship and FOIA workbooks as its first two outputs (their launches are the gate items). *Accept:* compiled directories pass spec lint; a dry-run of each index's weekly job meets its own acceptance criteria; diff between two compiler runs on the same workbook is empty (determinism).

**BUILD-07 — Legislative Authorship + FOIA micro (Q1 2027, session-timed).** Port the text-provenance engine from OnScript; reconstruct the 2019 ground truth by re-running the published investigate.ai method (replicate-then-run — this IS the launch artifact); go live aggregate/observational for the statehouse session; FOIA micro-index ships alongside as the journalist gift. LegiScan bulk for haystack, GovInfo/state sources for republished text (never republish LegiScan's compilation). *Accept:* replication report published with agreement/divergence vs. the 2019 findings; live session artifacts posting; FOIA index auto-updating monthly.

**BUILD-08 — Grocery forward pilot + shrinkflation retrocast (Q2 2027).** ⚑ Human ToS read of Kroger developer terms is the hard gate; if it fails, the fallback is a gate item (alternative retailer APIs / permissioned receipt panel), not improvisation. DFW + NY–Newark + Phoenix baskets (BLS cadence pre-flight; Chicago swap); mouseprint shrinkflation retrocast (framed as source-coverage, not population); CPI-day divergence artifact. *Accept:* weekly metro artifacts flowing; retrocast published; first CPI-day chart posted within hours of the BLS release.

**BUILD-09 — Say-Do pilot (Q2 2027, default contested-lane pick).** Reuse `dwillis/congress-press` (the OnScript corpus) + roll-calls (unitedstates/congress + Voteview); tight same-bill statement↔vote linkage; retrocast scored per harness; differentiation = the scorecard + tight linkage + leading signal (CivicAlign exists — cite it as prior art; "nobody does this" language is banned). *Accept:* pre-registered; scorecard v0 published; symmetric-by-construction audit passes (identical thresholds both parties — OnScript discipline).

**BUILD-10 — The flywheel surfaces (Q3 2027).** Track Record page v1 (every published call scored, auto-updating); Bank Stress aggregate index (named tier permanently sealed — constitutional); first 311 city (ground truth: the NYC Comptroller / Houston Title VI audits); mortality groundwork only (CDC WONDER harness + ⚑ operator-gated outreach for the permissioned funeral-home panel). *Accept:* Track Record page regenerates from scorecard JSONs alone; 311 city pipeline green 4 weeks; zero mortality publication surface exists.

---

## 7. Money, legal, and the operator calendar

**Honest budget.** Infra: R2 ~$2–3/mo by late year 1 (alert >$5), domains ~$10/yr, healthchecks/ntfy/Pages/Actions $0. One-time: TX LLC ~$300, domain ~$9. Annual: media-liability $500–1,800 (or GL $350–900 minimum pre-named-tier). Gated: ~$90-class Haiku-batch backfills, a few per year, each operator-approved. Steady cash ex-insurance ≈ **$3–5/mo**. **Floor honesty (constitutional):** the $50/mo floor covers infra with room; insurance is the swing line — in floor/orphan mode named tiers auto-freeze, which is exactly the state in which lapsing to GL-only is a conscious, documented option.

**Legal sequence.** LLC before anything publishes under the brand (BUILD-03 gate) → insurance bound at public launch (BUILD-04 gate) → INN preferred-carrier route once eligible → fiscal sponsorship (TNC/LION or NEO Philanthropy) when the first 501(c)(3)-gated grant is worth it (year 2). Anti-SLAPP: publishing entity and operator sit in Texas (TCPA is a strong fee-shifting statute); note venue exposure is national anyway — insurance is the real blanket.

**Operator calendar (next 12 months).** *(Human action-items that block a build step are tracked in the Vikunja task bus — board `observatory`; the dated grant/gated items below are not current blockers and surface there when they go live. See OBSERVATORY.md "Human tasking → Vikunja".)* ⚑ **Sep 14, 2026** — FIJ deadline (≤$10k; apply with the NHTSA retrocast as the work sample if BUILD-03 lands in time, else the archival-fleet + preregistration story). ⚑ **~Nov 2, 2026** — RJI Innovation Fellowship opens ($100k emerging-tech track is the target; prepare materials through October; the published retrocast is the application's spine). ⚑ **~Jan 2027** — DDRP opens (≤$35k; needs a lightweight newsroom partner — the journalist-gift list is the courtship). **~Early 2027** — NAIC homeowners data-call public report (insurability's future official anchor). **Jan–Apr 2027** — statehouse sessions (BUILD-07 window). Tarbell/Pulitzer data-journalism: rolling, apply opportunistically.

---

## 8. Distribution v2 (The Exhaust)

Brand: **The Exhaust** — "an observatory for shadow statistics." Every artifact carries the mark, one declarative sentence, the receipts link, and `theexhaust.org`. The launch story writes itself in three beats: the NHTSA retrocast report ("we backtested a decade of recalls; here's the precision/recall; here's the lead time"), WARN Watch (daily utility — the feed reporters actually wire into), and the scorecard ("we grade ourselves in public; nobody else in this field does"). Surfaces at launch: site + RSS/JSON + `@theexhaust.org`; the journalist-gift list (50 hand-picked reporters by beat, ⚑ operator approves the list, BUILD-04+2wk); FRED-style embeds when the flywheel justifies (year 2). Piggyback artifacts ride official release days from BUILD-08 on. No ads, no SEO-bait, no growth hacks — the artifact is the marketing; the scorecard is the moat (per the covenants and the 132-entity finding).

---

## 9. Covenant amendments enacted this session

All eight research-§6 amendments are live in [OBSERVATORY.md](../OBSERVATORY.md): (1) spend honesty ~$0–3/mo + infra requirements (R2-with-custom-domain, Pages primary, LFS and raw-hot-serving banned, standard runners only); (2) scheduling-reliability doctrine (over-schedule + dedupe + odd minutes + external dead-man heartbeat, mandatory); (3) scraping hygiene tightened (never circumvent technical controls, never create accounts or accept ToS, publish derived facts not verbatim prose); (4) defamation guardrails as *legal* doctrine (measurement-not-prediction, disclosure-by-construction, accuracy-as-control with a public corrections log, the named-claim firewall); (5) observer-effect hardened (financial-institution indexes permanently aggregate-only, non-waivable; no-perceived-trading-interest discipline); (6) the do-not-collect register; (7) government-continuity/stale-data posture (archived flat files are the retrocast-of-record; stale banners; orphan wiring); (8) naming — The Exhaust, "observatory" as descriptor. Plus one Phase 3 addition: the **prior-art scan rule** (any "novel" join/index claim gets a 15-minute scholarly scan before pre-registration — J-14 taught us).

---

## 10. Failure modes, updated defenses

| Failure | Defense (where) |
|---|---|
| GitHub cron drift/silent skips loses perishable data | over-schedule + dedupe + external heartbeat (SPEC-02/03); the one *mandatory* piece of external infra |
| Datacenter-IP 403s at fleet scale | the 403 ladder: operator-box fallback at identical politeness for generally-blocked-but-public sources; bot-challenged sources stop and gate (SPEC-01) |
| Federal data freeze (appropriations lapse, live since Oct 2025) | stale-data banners; archived flat files as retrocast-of-record; indexes chain to last-good vintage (SPEC-06) |
| Kroger ToS fails the human read | gate item with named fallbacks; inflation is forward-first anyway, so delay costs coverage, not credibility |
| Alert fatigue erodes the 1-hr week | alarm budget: >5 events/wk × 2 wks → root-cause gate item (SPEC-03) |
| Operator attention collapse | orphan protocol: freeze gated surfaces, keep collecting, banner, monthly cadence; recovery = one commit (SPEC-06) |
| A competitor (e.g., CivicAlign) adopts retrocasting | our archives + preregistration git history are unforgeable seniority; accelerate the Track Record page; competition on rigor is mission success |
| Metered-spend creep | budget governor: no key in R1; gated runs pre-estimated + capped + ledgered (SPEC-04) |
| Defamation suit despite guardrails | LLC + media policy + anti-SLAPP + receipts/methodology as the truth defense; transparency log turns threats into artifacts (constitution) |
| The operator's own enthusiasm mid-build (scope creep) | the BUILD queue is the scope; new ideas become workbooks in the gate queue, not detours |

---

*End of Phase 3 gameplan. The specs are the contracts; the constitution binds; Opus builds. What ships from here is autonomous up to decision gates — literally.*
