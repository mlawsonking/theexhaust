# 05-SCOPE-LEDGER — everything ideated, accounted for

*Fable, 2026-07-17. The reconciliation of the full Phase-1 vision ([`01-VISION.md`](01-VISION.md)) against what exists, so nothing ideated is silently lost and nothing enters the build except deliberately. **Rule: work enters [`ops/state/WORKPLAN.md`](../ops/state/WORKPLAN.md) only via (a) its scheduled BUILD slot, (b) a TRIGGER below firing, or (c) an operator gate.** The monthly audit reviews this ledger's triggers and files gates for any that fired. Statuses: `BUILT` · `IN-QUEUE(W-xx)` · `SCHEDULED(slot)` · `TRIGGERED(condition)` · `GATED(⚑ operator)` · `KILLED(reason)`.*

*Trigger discipline: triggers are checkable facts, not vibes. Firing a trigger files a gate — the operator (or the orchestrator under his standing priorities) still decides; a trigger never auto-builds. Before ANY new index/join is pre-registered: the 15-minute prior-art scan (constitutional).*

---

## 1. Engines (vision §3)

| Engine | Status | Trigger / slot |
|---|---|---|
| E1 Posting-Diff | **BUILT** (normalize 4 ATS + diff + fleet archiver) | universe expansion to ~3–5k boards = gate at W-007 launch |
| E2 Text-Provenance | TRIGGERED — port from OnScript | **calendar-armed Nov 2026** (W-011 prep for Jan–Apr statehouse session) |
| E3 Hazard-Language | SCHEDULED — v0 lexicon lives inside the NHTSA signal (W-006) | full E3 (taxonomies, classifiers on the 4080) when NHTSA scorecard publishes AND a second E3 index (drug-safety or workplace) clears its trigger below |
| E4 Price/Package | SCHEDULED (W-012, Q2 2027) | hard gate first: ⚑ Kroger ToS human read; fallbacks pre-named (alt retailer APIs / shrinkflation-only) |
| E5 Filing-Drift | PARTIAL — corpora collectors built (C1 CMS, C9 FDIC) | drift *analytics* arm at W-008 (hospital) — trigger: ≥2 PBJ vintages archived |

## 2. Shared services (vision §3, §5)

| Service | Status | Trigger |
|---|---|---|
| Retrocast harness | **BUILT** (synthetic-verified; leak-catcher proven) | first real exercise = W-006 |
| Entity resolver T0–T2 (company axis) | **BUILT** (live vs 9,304-issuer SEC crosswalk) | **GLEIF/Census/HUD crosswalks**: when the first cross-corpus join runs (WARN↔ATS at W-007) · **T2 local embeddings (4080)**: when the ambiguity queue exceeds ~500 pairs · **T3 gated batch**: first ambiguous backlog worth ~$90 → spend gate |
| Product↔product / place↔place axes | TRIGGERED | product axis: CPSC-leg of recalls (below); place axis: first geo join (311 or insurability) |
| Receipts store (fail-closed) | **BUILT** | first real bundles = W-007 artifact compiler |
| Artifact compiler | IN-QUEUE (W-007) | — |
| Workbook compiler | SCHEDULED (W-010 / BUILD-06) | trigger: two indexes live |

## 3. The index universe (vision §4) — all ~30, accounted for

**Flagships / year-1:**

| Index | Status | Trigger / gate |
|---|---|---|
| I-1 Shadow Layoffs — observational (WARN Watch + posting diffs) | IN-QUEUE (W-004 corpus, W-007 surfaces) | signature tier: forward-validation only — **naming gate opens solely at the pre-registered label count** (workbook fixes n before launch); ~12–18 mo |
| I-2 Shadow Recalls — NHTSA | IN-QUEUE (W-006) | ⚑ launch gate = LLC + insurance + sign-off |
| I-2b Recalls — CPSC consumer leg | TRIGGERED | NHTSA scorecard published AND UL-mirror/NEISS license verified AND product-axis resolver ready |
| I-2c Recalls — FAERS validation layer (I-14 merged here) | SCHEDULED (year 2) | trigger: 4 quarterly FAERS archives + harness idle capacity; differentiator is the scorecard, not the (saturated) dashboard |
| I-6 Hospital/Care Distress | IN-QUEUE (W-008) | rural-closure leg (Sheps) = year-2 flagship, trigger: staffing→deficiency scorecard published |
| I-3 Legislative Authorship | SCHEDULED (W-011, session-timed) | calendar-armed Nov 2026; aggregate/observational only at launch |
| FOIA Health micro | SCHEDULED (W-011) | — |
| I-4 Grocery + Shrinkflation | SCHEDULED (W-012) | ⚑ Kroger ToS gate; mouseprint retrocast rides along |
| I-16 Say-Do | SCHEDULED (W-012) | reuses OnScript `congress-press`; CivicAlign cited as prior art (never "nobody does this") |
| I-13 Bank Stress — aggregate | SCHEDULED (W-013) | named tier **PERMANENTLY SEALED** (constitutional observer-effect clause) |
| I-17 311 Inequality — first city | SCHEDULED (W-013) | expansion = one workbook per city (post-compiler) |

**Gated / deferred (triggers arm them):**

| Index | Status | Trigger |
|---|---|---|
| I-5 Shadow Mortality | GATED (year 2, by design) | ALL of: LLC+insurance live · permissioned funeral-home panel ≥3 counties consented · CDC WONDER harness built. Legacy.com stays do-not-collect forever |
| I-9 Insurability Retreat | TRIGGERED | ≥10 states with machine-readable state-portal filings (CA WARFF model) OR the NAIC 2027 public report lands (CALENDAR-armed) |
| I-7 Shadow Wages overlay | TRIGGERED (link-don't-compete stands) | E1 fleet ≥1k boards AND posted-range coverage measured ≥30% — else keep citing ADP/Indeed |
| I-8 Ghost Jobs (observation-class only) | TRIGGERED | 12 months of posting archive accrued |
| I-10 Small-Biz death-signal | TRIGGERED | ≥5 free SoS bulk states wired; births stay Census-BFS-cited |
| I-11 Workplace Safety (reframed: forums, not Glassdoor) | TRIGGERED | OSHA DOL-portal migration lands AND Reddit non-commercial corpus v0 validated vs an independent ground truth |
| I-12 College Viability | SCHEDULED (year 2) | E5 drift analytics mature + one closure definition frozen (SHEEO-anchored) |
| I-15 Utility Reliability | TRIGGERED | 6 months of self-collected outage-map aggregates + first EIA-861 vintage (poweroutage.us stays do-not-collect) |
| Corporate Distress capstone | SCHEDULED (year 2–3) | E1+E5 mature + CourtListener quarterly-bulk pipeline; named tier gated hard |
| I-18 Medical-Debt (GoFundMe) | **KILLED** (register; research §3) | revival = do-not-collect double-lock only |

**Tail sketches (vision §4.3):** BACKLOG, one line each in the vision; none enters WORKPLAN without prior-art scan + a workbook + a gate. The join-map doctrine (§5) governs: single-corpus versions may launch for speed; joins build the moat.

## 4. The join map (vision §5) — J-1…J-17

**Zero joins computed yet** (the resolver that enables them is built). Standing rule: a join enters WORKPLAN only when (a) both corpora are archived, (b) the resolver axis it needs is ready, (c) its 15-minute prior-art scan is logged. First expected: **J-4 partial** (ATS↔WARN company resolution) at W-007; **J-1** rides I-2b; **J-7** rides W-008. **J-14 KILLED as pitched** (published null result); the promotion-timing reframe is TRIGGERED on a feasible free-data retrocast design, else stays dead.

## 5. Distribution & institution (vision §8, §7)

| Element | Status | Trigger / gate |
|---|---|---|
| Site (5 core pages, theme-aware, receipts links) | **BUILT** (skeleton) | index pages arrive with their indexes |
| Feeds (RSS/JSON), WARN Watch, posting-diff pages | IN-QUEUE (W-007) | — |
| Bluesky `@theexhaust.org` | GATED ⚑ (handle via TXT DNS at launch) | — |
| Journalist-gift list (50 hand-picked) | GATED ⚑ (BUILD-04 + 2 wk) | operator approves the list — external comms gate |
| Weekly public digest | TRIGGERED | ≥2 indexes posting on cadence |
| FRED-style embeds | TRIGGERED | first external citation detected (the flywheel's own signal) |
| Piggyback artifacts (CPI-day etc.) | SCHEDULED (W-012+) | — |
| Grants: FIJ / RJI / DDRP | on the Vikunja board (hard-dated) | CALENDAR-armed |
| Fiscal sponsorship | TRIGGERED | first 501(c)(3)-gated grant worth pursuing (per research §8 ladder) |
| LLC + insurance | GATED ⚑ (W-006/W-007 launch gates) | vtask fires when reached |
| Protocolization / certification / succession / Zenodo DOIs | year-3+ by design | constitution §SPEC-06 succession seed already encodes the floor; revisit at the futility-clause review 2027-12-31 |

## 6. The governance spine (already constitutional — listed for completeness)

Retrocast gate · naming gate + observer-effect seal · do-not-collect register (CI-enforced) · scraping hygiene (no circumvention) · spend structure (no LLM key in R1; gated runs capped in code) · heartbeat mandate · orphan protocol + floor mode · stale-data posture · corrections auto-publish · prior-art scan rule · adversarial review before BUILD acceptance · **futility clause (hard kill, 2027-12-31)** — the whole ledger above answers to that date.
