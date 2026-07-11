# 02-RESEARCH — The Observatory, Phase 2 validation

*Opus, 2026-07-11. Status: complete. Predecessor: [`01-VISION.md`](01-VISION.md). Successor: `03-GAMEPLAN.md` (Fable).*

*Method: multi-agent research fan-out — 15 parallel probes against live 2026 sources (WebSearch/WebFetch, live API calls, Wayback CDX, registrar/domain checks), with independent adversarial verification on the six load-bearing "existential" questions. Every material claim below is sourced to a URL in the working notes; the highest-stakes ones are cited inline. Confidence is stated per finding. The mandate was to **kill without sentiment**; where the vision's confident assumptions failed, they are marked failed.*

---

## 0. Handoff note to Fable (Phase 3)

The thesis holds. The engine architecture holds. But three things changed and you must build the gameplan around them:

1. **The #1 index's retrocast is not freely feasible — the escape hatch in vision §6.2 has fired.** Historical job-posting data to backtest Shadow Layoffs against 2022–2025 does not exist at retrocast grade for free (Wayback never systematically archived the ATS JSON endpoints; every deep-history corpus is paid/enterprise). Per §6.2's own conditional, **the "first published retrocast" crown moves off Shadow Layoffs.** Layoffs remains the operator's favorite and the *distribution* flagship (observational WARN Watch + posting-diffs, born-shareable, day one) — but its credibility engine can only forward-validate, ~12–18 months to a first precision/recall. Two indexes can retrocast **today, on already-free-and-archived data, with no scraping and no semantic join**: **NHTSA vehicle-safety recalls** and **Hospital/Care Distress (nursing-home staffing → harm deficiencies)**. One of these should be the first thing published.

2. **Several corpora are dead on access or ethics, and several covenants need amendment.** Legacy.com (obituaries), GoFundMe (medical debt), poweroutage.us (redistribution), SERFF/NAIC (insurance filings), Amazon reviews, Glassdoor/Indeed — all blocked by ToS, ethics, or technical closure. The `$0` spend claim is really `~$0–3/mo`. GitHub cron is unreliable enough to threaten "collect before you can compute." The scraping covenant must be tightened to be legally safe in the 2025–26 CFAA/CDAFA climate. §6 lists every amendment.

3. **"The Observatory" is not a cleanly ownable name, and this needs an operator decision.** It collides head-on with Columbia Journalism Review's own long-running column literally titled *The Observatory*, is near-generic in the disinformation/data-accountability space, and every bare domain is already registered. See §9 — I've asked the operator to choose a direction; his answer is recorded there.

Everything you need to reconcile is in §3 (kill-list answers), §4 (per-index verdicts + re-scored portfolio), §5 (corpus access ledger), and §6 (constitutional amendments). **No implementation code exists** — this phase produced this document only.

---

## 1. Executive summary

**Survives:** the thesis, the five-engine architecture, the retrocast-gate doctrine, the join/entity-resolver moat, the ~$0-compute posture, and a clear legal + funding path. The entity resolver — the deep moat — is **buildable at ~$0 steady state** on free official crosswalks (SEC CIK/ticker, GLEIF LEI, Census FIPS/HUD ZIP) with gated Haiku-batch backfills at **~$90 per ~100k-pair run**.

**The one big strategic change:** separate **"first published retrocast"** (the credibility engine) from **"first published index"** (the distribution flagship). They are no longer the same index.
- **First retrocast → NHTSA Shadow Recalls.** Cleanest falsification of the whole thesis, fully free, both sides official, archived data available *now*, with a killer "we saw the signal N days before the recall" lead-time story.
- **Distribution flagship, launched in parallel → Shadow Layoffs (observational).** WARN Watch + posting-diff receipts are publishable day one as reporting; archival crons must start immediately; the forward-validation scorecard accrues from week one.
- **Cleanest/fastest second retrocast → Hospital/Care Distress.** CMS PBJ nurse-staffing → subsequent harm deficiencies is hard-keyed on CCN (no semantic join), leak-free by construction, 418k dated ground-truth citations.

**Outright kills (removed from the portfolio):**
- **Medical-Debt Distress (GoFundMe)** — ToS §12.3 bans scraping *and* ML use; obituary-grade ethics fails on identifiable medical hardship. **DEAD.**
- **J-14 "poverty-timed pricing"** — already the *published null result* of Goldin/Homonoff/Meckel (AEJ:EP 2022); retrocast data (NielsenIQ/Kilts) is paywalled/academic-gated. **DEAD as pitched** (reframe to promotion-timing or cut).
- **Full-basket grocery retrocast from web archives** — Flipp/retailer pages are JS SPAs; item+price data was never in archived HTML. **DEAD** (index survives forward-first + a narrow shrinkflation retrocast).
- **Consumer-review corpus for recalls (Amazon)** — logged-out review pages 404'd since May 2026, text stripped from product HTML. **DEAD** (recalls survives NHTSA/CPSC/FAERS-first).

**Access-blocked, re-scoped (not dead, but not as vision assumed):**
- **Shadow Mortality:** Legacy.com ToS forbids *all* automated access (even count-only); CDC county-**month** suppression is far worse than the vision assumed (likely a majority of non-metro cells). Re-scope to a CDC-anchored nowcast + a small permissioned funeral-home panel.
- **Insurability Retreat:** SERFF/NAIC is a clickwrap anti-automation wall (403s bots). Re-scope to a per-state, state-portal-only carve-out (California WARFF is the model).
- **Utility Reliability:** poweroutage.us ToS bans redistribution/derivatives. Self-collect raw utility maps; use EIA-861 SAIDI/SAIFI as ground truth.
- **Workplace Safety review-leg:** Glassdoor/Indeed are ToS-hostile/login-walled. Reframe to worker-sentiment-from-public-forums (Reddit non-commercial API), **not** a Glassdoor proxy.

**Link-don't-compete (demote; cite, don't rebuild):** Shadow Wages (ADP Pay Insights + Indeed Hiring Lab already own it) and Small-Business Formation (Census BFS is free, weekly-since-2020). Build only a thin retrocast-scored overlay if it clears the gate.

**New/elevated white space (no live incumbent found):** cross-city **311 Civic-Response Inequality**, **Insurability Retreat** (only a static 2018–2023 Senate report exists), and the **Say-Do semantic gap** (ProPublica Represent died July 2024, leaving a hole). The single field-wide differentiator the *entire* competitive landscape omits is **the published retrocast precision/recall scorecard** — that is the moat, more than data novelty.

**Legal + money:** a defensible shield exists cheaply — single-member LLC as operating shell (**not** the defamation shield), fiscal sponsorship for grant access (TNC 3.5–7%, or NEO Philanthropy which incubated *The Markup*), media-liability insurance (~$500–1,800/yr, deferrable to first publish), and anti-SLAPP statutes (40 states + DC). Funding: **RJI Professional Innovation Fellowship** ($75–100k, individuals eligible, next cycle opens ~Nov 2026 for a 2027 start) is the anchor, bridged by DDRP (≤$35k) + Pulitzer/FIJ/Tarbell reporting grants. Total legal-shield cost: ~$100–500 to start, ~$1–2.5k/yr once insured — inside the covenant.

---

## 2. Method, confidence, and caveats

- **How:** 15 scoped research agents ran in parallel against live sources; each returned structured findings with per-claim source URLs and confidence. Six load-bearing findings (R1 layoffs, R2 recalls, R3 mortality, R4 inflation, R6 infra, R9 legal) were then handed to independent adversarial verifiers instructed to *refute* the optimistic claims. Where the verifier weakened a claim, this document reflects the corrected, more-pessimistic version.
- **Date stamp:** all "live" checks were performed 2026-07-10/11. API statuses, rate limits, ToS, grant deadlines, and domain availability drift — every corpus entry in §5 carries a "verified" date and should be re-checked before Phase 4 depends on it.
- **Single-source caveats:** domain availability is from one registrar backend (Vercel/Namecheap) — the operator must reconfirm at a registrar + USPTO TESS before buying. "No live incumbent" claims for 311/insurability/say-do are medium-confidence (absence of evidence in a web sweep) — Phase 3 should run one deeper vertical prior-art pass before locking them.
- **Present-tense macro fact:** the US federal government has been in an appropriations lapse since **Oct 1, 2025**. Federal APIs (CPSC/NHTSA/FDA/CMS) still returned July-2026 data in live checks, but refreshes can stall without notice. This *reinforces* "collect before you can compute" — start archival crons immediately and prefer archived flat files as the retrocast-of-record.

---

## 3. The load-bearing kill-list (vision §10), answered

**① Posting-history reconstruction (decides index #1) — PARTIAL KILL.**
All four ATS platforms still expose public, unauthenticated JSON endpoints in 2026 (verified live: Greenhouse `boards-api.greenhouse.io`, Lever `api.lever.co/v0/postings`, Ashby `api.ashbyhq.com/posting-api`, SmartRecruiters `/v1/companies/{id}/postings`). Lever's README *explicitly* permits third-party scraping; the others require no auth but merely lack a prohibition (weaker — do a one-time robots/master-ToS check per platform). Ground truth is intact and free (layoffs.fyi live/dated/company-level; WARN from 49 states, Arkansas excepted). **But the existential question fails:** Wayback archived these endpoints only incidentally (most prominent companies: 0 usable full-board snapshots; the few archived have a handful of captures in scattered years), and every deep-history corpus (LinkUp, Revelio, Lightcast, Coresignal) is paid/enterprise; Revelio's "academic" route needs an institutional WRDS license (one such route expires June 2026). **→ No free retrocast-grade history. Shadow Layoffs must forward-validate; it is the slowest index to credibility despite being the operator's favorite. Start archival crons the first day of Phase 4.** (Caveat from verification: "$0 via GitHub Actions" for the crons may hit datacenter-IP 403s at fleet scale — monitor and budget a fallback.)

**② Review-corpus access (decides recalls' ceiling) — RE-SCOPED, index survives.**
The government spine is real, free, and clean: NHTSA recalls+complaints APIs (make/model/year, full narratives, +367 MB flat file), CPSC Recalls JSON + 18 MB CSV (with importer/manufacturer/country provenance), openFDA FAERS (20.3M reports) + CAERS — all live, no/low-auth. **Three optimistic assumptions die:** (a) `opendata.cpsc.gov`, the raw SaferProducts incident-narrative feed, is **NXDOMAIN/decommissioned** — the "early-signal-before-recall" consumer corpus is gone there (now only via clunkier NEISS/Violations, the Clearinghouse tool, or a UL mirror whose license must be checked); (b) **Amazon review text is closed** (May 2026 hardening 404s logged-out review pages, strips text from product HTML) — strike it from the design; (c) **Reddit** is non-commercial-only (ToS bars commercial/ML use; enterprise is ~$12k/**month**, not year) — cut from any revenue-bearing path. Bills of lading (ImportYeti) are gated-free, paywalled for bulk — keep as optional provenance enrichment only, via direct CBP/FOIA for a $0 path. Entity resolution (complaint→recall) is non-trivial but has named ground truth and direct prior art. **→ Launch recalls as NHTSA-only first; add CPSC recall CSV second; treat FAERS disproportionality as a separately-scoped third index whose moat is *operational* (live + retrocast scorecard + receipts), since the method is textbook.** (Verification note: FAERS lags ~10 weeks; state the actual lag.)

**③ Obituary corpus posture (decides mortality) — RE-SCOPED; the aggregator is off-limits.**
CDC WONDER is solid retrocast ground truth for 2015–2023 **but county-month only via the web interface** (the API is national-only for NVSS mortality) and the <10 suppression rule censors far more than the vision assumed — verification corrected the "~30%" figure: that was county-*year* age-stratified; a related study found ~50% suppressed at annual granularity, so realistic county-**month** suppression is likely a *majority* of non-metro cells and near-total rural. The obituary *signal* side must change: **Legacy.com (~70% of US deaths) ToS forbids ALL automated access** ("scrape, copy, or monitor any portion of the Services") and robots.txt blocks the exact search/finder/JSON endpoints a counter would use — so even ethics-clean count-only collection is a contract violation. The academic method is proven (J. Appalachian Health 2024: count-only funeral-home+newspaper listings, official COVID captured only 51%, ~5-month lead) but that's a best-case single 130k-population county, not proof of rural generalizability. **→ Identity becomes "CDC-anchored county-month mortality nowcast (suppression-robust strata + published imputation) with a small, permissioned, robots-cleared funeral-home/local-paper panel," NOT "scrape Legacy." Gate behind the LLC + insurance. Second-wave launch by design.**

**④ Circular/price archive depth (decides inflation retrocast) — PARTIAL KILL; forward-first.**
Full-basket retrocast from web archives is **DEAD** (Flipp + retailer weekly-ad pages are JS SPAs; a 200k-row Flipp CDX sample held only ~340 flyer_ids and empty item fragments). Forward collection is viable: **Kroger's free Public Products API** (10k calls/day, store-level regular+promo price) is the anchor — *but its ToS on redistributing prices could not be verified (JS SPA blocked all fetches); this is a hard human-read gate before any build.* Ground truth is better than assumed: **BLS food-at-home (SAF11) is MONTHLY for 17+ metros** via API (needs the free registered key for sustained use — keyless is only 25 queries/day). A genuine narrow retrocast survives via **mouseprint.org** (shrinkflation, text-archived to 2007). Prior art is more crowded than the vision hoped (Datasembly *does* publish a free weekly GPI with methodology; Numerator/WaPo publishes a receipt-panel method; plus DataWeave, CBS, USA Today, consumer unit-price apps). **→ The only clean white space is "open methodology + published retrocast scorecard vs BLS + permanent free access + unit-honest price-per-oz shrinkflation." De-hype the pitch; forward-collect now.**

**⑤ Model-bill corpus assembly (decides authorship) — VIABLE-WITH-CHANGES.**
Data supply is free and abundant: LegiScan free bulk datasets (all 50 states + Congress, JSON/CSV/XML, registration-only), GovInfo bulk BILLS XML (public-domain federal, unrestricted), Open States/Plural Policy as backup. Model-bill needle corpus is largely obtainable clean: ALEC's own current library (~1,000 policies, robots-clean), SiX/ALICE (~2,000 bills, robots-clean), the ~500-bill CPI seed on GitHub. **Two changes:** the 2019 USA Today ~10,000-match dataset is **not** downloadable (tracker DNS dead since Aug 2024; only the 500-bill religious-freedom seed survives) — so retrocast ground truth is *reconstructed by re-running the (fully published, investigate.ai) n-gram/Solr method*, which doubles as the "replicate, then run" press hook; and LegiScan ToS bars redistributing "the Services," so republish public-domain bill text + your own computed matches, not LegiScan's compilation. The ALEC Exposed historical 800-bill archive now sits behind a Cloudflare challenge — source it from Wayback/mirrors, don't defeat the challenge (covenant line). **→ Strong "replicate a Goldsmith-winning study, then run it forever" index, but highest legal/editorial sensitivity (named authorship) — sequence after a track record + the LLC/insurance shield exist.**

**⑥ Boring-but-fatal trio (storage / Actions / rate-limits) — GREEN, with honesty edits.**
- *GitHub Actions on public repos:* **still free and unlimited on standard runners**, confirmed by name in GitHub's Jan-2026 pricing page ("Standard GitHub-hosted or self-hosted runner usage on public repositories will remain free"). Keep the repo public; never use "larger runners" (billed even on public repos); chunk under the 6-hr job cap.
- *Storage:* archives overflow every 10 GB free tier within year 1 (~25–40 GB/yr; outage-map snapshots heaviest). Cloudflare R2 at $0.015/GB-mo with **free egress** makes 3-year volumes ~**$2–3/month** — inside the $50 floor but **not literally $0**. R2 free egress requires a (free) **custom domain** on the bucket — never serve from raw `r2.dev`. GitHub Releases (2 GiB/asset, no total-size/bandwidth cap) is a free cold mirror; **ban Git LFS** (bandwidth-metered) and **never hot-serve `raw.githubusercontent.com`** (hard-rate-limited to ~60 req/hr unauthenticated since May 2025).
- *Scheduling (the real threat, and it's operational not fiscal):* GitHub cron is drifting **1–4.5+ hours late and worsening**, with GitHub staff admitting "unacceptable delays" and no fix; runs are silently skipped on inactive repos. **→ Over-schedule (every 15–30 min + dedupe), avoid `:00` schedules, and add an external dead-man heartbeat — mandatory, not optional, because this directly threatens "collect before you can compute."**
- *Hosting:* **Cloudflare Pages** (unlimited bandwidth, commercial-use-safe) is the correct primary host; GitHub Pages bars "primarily commercial" and Vercel Hobby bars commercial use outright.
- *RTX 4080:* 10–1000× over-provisioned. model2vec/MiniLM embed the daily corpus in minutes; reserve the GPU for the cross-encoder rerank + hazard classification. Non-issue.

**⑦ Legal foundation — GREEN, conditional on constitutional guardrails.** See §6 (amendments) and §7 (detail). Defamation: Milkovich killed any blanket "opinion" privilege; the real shield is **opinion-on-fully-disclosed-*true*-facts** (receipts + frozen methodology) + **measurement-not-prediction** (now doing *legal*, not just editorial, work) + accuracy-as-a-control (data bugs become liability events). Scraping: CFAA is off the table for logged-out public pages (Van Buren + hiQ + Meta v. Bright Data), **but** — verification correction — hiQ *lost the war* on contract grounds ($500k, injunction, data destruction), and *X Corp v. Bright Data* revived CFAA/CDAFA/DMCA claims (Nov 2024, on appeal, argued ~June 2026) for **anti-bot circumvention**. So the covenant must forbid *circumventing technical barriers* (IP rotation, CAPTCHA-solving, bot-detection evasion), not merely forbid logging in. Bank observer-effect: truthful commentary is near-absolutely protected, but the theory is untested, the litigation-as-harassment cost is highest here, and the **Andrew Left / Citron criminal conviction (June 1, 2026)** makes any named financial-stress signal from a party who could be *perceived* to benefit legally radioactive — so **bank/financial indexes stay permanently aggregate-only** by constitution, for prudence, not because the law compels it.

**⑧ Prior-art sweep — GREEN; the moat is the scorecard, not the data.** Raw-data and aggregate-nowcast layers are crowded (layoffs.fyi, Revelio, LinkUp, ADP, Indeed, FAERS dashboards, Census BFS, poweroutage.us). **Not one live public tracker publishes an openly falsifiable retrocast precision/recall scorecard** — that is the field-wide white space. Two link-don't-compete (wages, small-biz); three clean no-incumbent lanes (311 cross-city inequality, insurability retreat, say-do semantic gap). Leading-signal-alone is *already sold* commercially (Revelio/LinkUp), so the Observatory's edge must be "free + receipts + retrocast," not "first to lead."

**⑨ Grants landscape — GREEN.** See §8. Anchor = RJI fellowship (individuals eligible, no vessel, $75–100k, next cycle ~Nov 2026 → 2027 start). Marquee foundations (Ford/MacArthur/Democracy Fund/Knight/AJP) are invite-only or 501(c)(3)-gated — reachable only via a fiscal sponsor + published track record, in years 2–3. Open Collective Foundation (US) is dead (dissolved end-2024) — don't plan around it.

**⑩ Naming/domains + the operator's metro — YELLOW; needs an operator decision (§9).** "The Observatory" collides with CJR's column and is near-generic; all bare domains are taken. Recommendation: keep "observatory" as a *descriptor*, lead with a distinctive ownable mark. Operator's metro for the (now lower-priority, forward-first) inflation pilot: recorded in §9/§12.

---

## 4. Per-index verdicts and the re-scored portfolio

### 4.1 Verdicts (vision's required format)

| # | Index | Verdict | The load-bearing reason |
|---|---|---|---|
| I-1 | Shadow Layoffs | **VIABLE-WITH-CHANGES** | Endpoints/ToS/ground-truth all fine; **no free retrocast history** → forward-validation only; launch observational + start archival crons day one |
| I-2 | Shadow Recalls | **VIABLE-WITH-CHANGES** | Govt spine excellent; **NHTSA-only first retrocast** (Amazon reviews + `opendata.cpsc.gov` dead); FAERS as separate operational-moat index |
| I-3 | Legislative Authorship | **VIABLE-WITH-CHANGES** | Free corpora; reconstruct 2019 ground truth by re-running the published method; gate named-authorship framing; legal-sensitive |
| I-4 | Grocery Inflation + Shrinkflation | **VIABLE-WITH-CHANGES** | Full-basket retrocast **dead**; forward-first via Kroger API (ToS unverified — human-read gate) + BLS metro monthly + mouseprint shrinkflation retrocast |
| I-5 | Shadow Mortality | **VIABLE-WITH-CHANGES** | Legacy off-limits (ToS); CDC county-month suppression severe; re-scope to CDC-anchored nowcast + permissioned funeral-home panel; second wave |
| I-6 | Hospital & Care Distress | **VIABLE** | **Cleanest immediate retrocast in the portfolio** — PBJ staffing → CMS harm deficiency, hard CCN key, no scraping, leak-free; closure retrocast via Sheps list |
| I-7 | Shadow Wages | **VIABLE-WITH-CHANGES → LINK-DON'T-COMPETE** | ADP Pay Insights + Indeed Hiring Lab already own the aggregate nowcast; build only a retrocast-scored overlay |
| I-8 | Ghost Jobs | **VIABLE-WITH-CHANGES (observation-class)** | No named ground truth for "never intended to hire"; run as labeled observation |
| I-9 | Insurability Retreat | **VIABLE-WITH-CHANGES** | SERFF/NAIC is a clickwrap anti-automation wall (**do not scrape**); re-scope to per-state portals (CA WARFF); genuine white space |
| I-10 | Small-Business Births/Deaths | **VIABLE-WITH-CHANGES → LINK-DON'T-COMPETE** | Census BFS free/weekly owns births; only a leading *death/closure* exhaust signal is additive; no 50-state SoS index (Delaware et al.) |
| I-11 | Workplace Safety | **VIABLE-WITH-CHANGES (reframe)** | OSHA data GREEN (bulk CSV; API mid-migration); Glassdoor/Indeed dead; reframe review-leg to worker-sentiment-from-forums (Reddit), **not** a Glassdoor proxy |
| I-12 | College Viability | **VIABLE-WITH-CHANGES** | IPEDS + SHEEO/Sheps closure lists GREEN; must freeze one closure definition; verify exhaust leads IPEDS' ~12–18mo lag |
| I-13 | Bank Stress | **VIABLE (aggregate-only, permanently)** | FDIC data clean/retrocastable; **named tier constitutionally sealed** (observer-effect + hostile short-seller enforcement climate) |
| I-14 | Drug Safety | **VIABLE-WITH-CHANGES** | Disproportionality dashboards saturated; build the missing **validation layer** (signals retrocast vs confirmed FDA actions) |
| I-15 | Utility Reliability | **VIABLE-WITH-CHANGES** | poweroutage.us redistribution **banned**; self-collect raw utility maps + EIA-861 SAIDI/SAIFI ground truth |
| I-16 | Say-Do Index | **VIABLE** | ProPublica Represent died July 2024 → clean white space; build on Congress.gov/GovTrack/Voteview roll-calls you control |
| I-17 | 311 Civic-Response Inequality | **VIABLE** | No cross-city incumbent; clean city open-data APIs; normalization is the cost; strong local-press hook |
| I-18 | Medical-Debt Distress (GoFundMe) | **DEAD** | ToS §12.3 bans scraping + ML use; obituary-grade ethics fails on identifiable medical hardship |
| — | Corporate Distress (capstone) | **VIABLE-WITH-CHANGES** | CourtListener/RECAP GREEN (free API + quarterly bulk; FLP membership advisable); EDGAR language-drift free; named tier gated hard |
| — | FOIA Health (micro) | **VIABLE** | MuckRock API free (read); tiny build; run as the year-1 journalist gift |
| J-14 | Poverty-timed pricing (join) | **DEAD as pitched** | Published null result (Goldin/Homonoff/Meckel 2022); retrocast data paywalled; reframe to promotion-timing or cut |

### 4.2 Re-scored portfolio (formula: (Insight × Shareability × Retrocast) ÷ (Build + Legal), each 1–5)

Scores are re-derived from evidence. The biggest movements: **Recalls and Hospital Distress rise to the top** (clean, immediate, free retrocasts); **Layoffs falls** in the *retrocast-led* ranking (R drops to 2 — forward-validation only) while remaining the distribution flagship; several corpora fall on build/legal cost after access reality.

| Rank | Index | I | S | R | B | L | Score | Δ vs vision |
|---|---|---|---|---|---|---|---|---|
| 1 | **I-2 Shadow Recalls (NHTSA-first)** | 5 | 4 | 5 | 2 | 2 | **25.0** | ▲ (20.0) — now the first retrocast |
| 1 | **I-6 Hospital & Care Distress** | 5 | 4 | 5 | 2 | 2 | **25.0** | ▲ (16.0) — cleanest data in the portfolio |
| 3 | I-3 Legislative Authorship | 5 | 4 | 4 | 2 | 3 | **16.0** | ▼ (20.0) — legal sensitivity |
| 4 | **I-1 Shadow Layoffs** | 5 | 5 | 2 | 2 | 2 | **12.5** | ▼ (31.3) — forward-only retrocast; still distribution flagship |
| 4 | I-16 Say-Do Index | 4 | 4 | 3 | 2 | 2 | **12.0** | ▲ (12.0) — Represent's death opened the lane |
| 4 | I-17 311 Inequality | 3 | 4 | 3 | 2 | 1 | **12.0** | ▲ (9.0) — clean no-incumbent white space |
| 7 | I-13 Bank Stress (aggregate) | 5 | 3 | 5 | 2 | 5 | **10.7** | ~ (9.4) — named tier sealed |
| 8 | I-4 Grocery Inflation/Shrinkflation | 4 | 5 | 2 | 3 | 1 | **10.0** | ▼ (20.0) — full retrocast dead; forward-first |
| 9 | I-14 Drug Safety (validation layer) | 4 | 3 | 4 | 3 | 2 | **9.6** | ~ (9.6) |
| 9 | I-12 College Viability | 4 | 3 | 4 | 3 | 2 | **9.6** | ~ (9.6) |
| 11 | I-7 Shadow Wages (overlay only) | 3 | 4 | 3 | 2 | 2 | **9.0** | ▼ (12.0) — link-don't-compete |
| 12 | Corporate Distress (capstone) | 5 | 3 | 4 | 3 | 4 | **8.6** | ~ — CourtListener GREEN |
| 13 | I-10 Small-Biz (death-signal only) | 2 | 4 | 3 | 2 | 1 | **8.0** | ▼ (9.0) — link-don't-compete |
| 14 | I-8 Ghost Jobs (observation) | 3 | 5 | 2 | 2 | 2 | **7.5** | ~ (7.5) |
| 15 | I-15 Utility Reliability | 4 | 3 | 3 | 3 | 2 | **7.2** | ~ — re-sourced off poweroutage.us |
| 16 | I-9 Insurability Retreat | 4 | 4 | 3 | 4 | 3 | **6.9** | ▼ (12.0) — SERFF ToS wall |
| 17 | I-5 Shadow Mortality | 5 | 3 | 3 | 4 | 3 | **6.4** | ▼ (12.5) — Legacy blocked; suppression |
| 18 | I-11 Workplace Safety (reframed) | 3 | 4 | 3 | 3 | 3 | **6.0** | ▼ (10.7) — review corpus dead |
| — | FOIA Health (micro) | 3 | 3 | 4 | 1 | 1 | **18.0** | ~ — flattered by tiny build; journalist gift |
| — | I-18 Medical-Debt | — | — | — | — | — | **DEAD** | ✗ removed |

*Note on the tie at #1:* both are genuine, immediate, free retrocasts. **Recommendation: NHTSA Recalls is the single first *published* retrocast** — it's consumer-facing (higher real shareability than a technical staffing-deficiency story), its "signal detected N days before the recall" lead-time distribution is the strongest press hook in the portfolio, it *is* the original falsification test named in the founding thesis, and it starts the recalls naming-gate clock. **Hospital Distress is the immediate second** (and its rural-hospital-*closure* leg is a year-2 flagship). This is not a demotion of the operator's layoffs preference — §6.2 of the vision explicitly pre-authorized exactly this split when the posting-history conditional fired.

---

## 5. Corpus access ledger (living table — re-verify dates before Phase 4 depends on a row)

**GREEN = free, covenant-clean, build on it. YELLOW = usable with a specific strategy/caveat. RED = blocked; do not build as scoped.** All verified 2026-07-10/11.

| Corpus / source | Powers | Access | Auth | Limit / cadence | Verdict |
|---|---|---|---|---|---|
| NHTSA recalls + complaints API + FLAT_CMPL.zip (367 MB) | Recalls | JSON API + bulk flat file | none | generous; complaints current | **GREEN** |
| CPSC Recalls RestWebServices JSON + 18 MB CSV | Recalls | JSON + CSV, provenance fields | none | current to Jul 2026 | **GREEN** |
| openFDA FAERS / CAERS | Drug/food safety | JSON API | free email key | 120k/day w/ key; ~10-wk lag | **GREEN** (state the lag) |
| `opendata.cpsc.gov` SaferProducts incident feed | Recalls early-signal | — | — | — | **RED** (NXDOMAIN/decommissioned) |
| Amazon review text | Recalls signal | logged-out pages | — | 404'd since May 2026 | **RED** (closed) |
| Reddit Data API | Worker/consumer sentiment | API | OAuth | 100 QPM non-commercial; commercial ~$12k/mo | **YELLOW** (non-commercial only; not for revenue tier) |
| ImportYeti / bills of lading | Factory provenance | search UI (gated free) | login after ~25 views | bulk paywalled | **YELLOW** (enrichment only; use direct CBP/FOIA for $0) |
| Greenhouse / Lever / Ashby / SmartRecruiters JSON | Layoffs, Wages, Ghost Jobs | JSON endpoints | none | Lever explicitly allows scraping; others silent | **GREEN** (live) / no free *history* |
| layoffs.fyi | Layoffs ground truth | Airtable-backed | none | free with attribution | **GREEN** |
| WARN notices (49 states) + aggregators | Layoffs ground truth | heterogeneous PDF/HTML/DB | none | Arkansas excepted | **GREEN** (per-state adapters) |
| CDC WONDER (final + provisional MCD) | Mortality ground truth | **web interface only** (API national-only) | none | <10 suppression severe at county-month | **YELLOW** (metro/multi-month strata) |
| Legacy.com obituaries | Mortality signal | — | — | ToS bans ALL automated access; robots blocks endpoints | **RED** (use permissioned funeral-home panel) |
| BLS Public Data API (CPI food-at-home SAF11) | Inflation ground truth | JSON API | free key for sustained use | 25/day keyless, 500/day keyed; monthly, 17+ metros | **GREEN** |
| Kroger Public Products API | Inflation forward-collection | JSON API | OAuth | 10k calls/day; **redistribution ToS UNVERIFIED** | **YELLOW** (human-read gate) |
| Flipp / retailer weekly-ad pages | Inflation basket | JS SPA | — | no archived item data; no-competing ToS clause | **RED** for retrocast; forward via retailer APIs only |
| mouseprint.org | Shrinkflation retrocast | web, text-archived to 2007 | none | selection-biased (notable shrinks) | **GREEN** (frame as source-coverage, not population) |
| LegiScan bulk datasets | Legislation haystack | JSON/CSV/XML bulk | free registration | 30k API q/mo (bulk sidesteps); ToS bars redistributing "Services" | **GREEN** (republish text from GovInfo/state + own matches) |
| GovInfo BILLS bulk XML | Congress bill text | bulk | none | public domain (17 USC 105) | **GREEN** |
| ALEC / SiX(ALICE) / CPI-seed model bills | Legislation needle | robots-clean HTML / GitHub | none | ALEC Exposed historical behind Cloudflare → use Wayback | **GREEN** |
| SEC EDGAR (submissions + full-text) | Corporate distress, layoffs 8-K | JSON API | none | 10 req/s; **descriptive User-Agent required** | **GREEN** |
| CMS PBJ staffing + Health Deficiencies (r5ix-sfxw) | Hospital/Care Distress | JSON API + CSV | none | quarterly; hard CCN key; 418k dated citations | **GREEN** (cleanest retrocast) |
| CMS HCRIS cost reports | Hospital financial distress | per-FY zipped flat files | none | quarterly; needs SQL ETL | **GREEN** (ETL step) |
| UNC Sheps Center rural-hospital closures | Hospital ground truth | downloadable dated list | none | 197 since 2005 | **GREEN** |
| FDIC BankFind (failures/financials) + FFIEC call reports | Bank Stress | REST API + bulk | none | 4,115 dated failures; quarterly | **GREEN** (aggregate-only publication) |
| FDIC ED&O enforcement orders | Bank Stress | search UI | none | no clean bulk export | **YELLOW** (polite scrape) |
| IPEDS finance + SHEEO closures | College Viability | bulk CSV / downloadable | none | annual; ~12–18mo lag | **GREEN** (freeze closure definition) |
| SERFF / NAIC Filing Access | Insurability Retreat | per-filing search | clickwrap | Use Agreement bans automation; 403s bots | **RED** (per-state portals only, e.g. CA WARFF) |
| DOL OFLC H-1B LCA / PERM (FLAG) | Layoffs/hiring intent | quarterly bulk | none | free | **GREEN** |
| OSHA enforcement/inspection | Workplace Safety | bulk CSV (data.gov) | none | API retired/mid-migration to apiprod.dol.gov/v4 | **YELLOW** (bulk-first; watch migration) |
| Glassdoor / Indeed reviews | Workplace Safety signal | login-walled + Cloudflare | — | ToS bans scraping | **RED** (use Reddit forums instead) |
| Census BFS (business formation) | Small-Biz | Economic Indicators API | **key now required (2026)** | monthly national/state; weekly since 2020 | **GREEN** (validate key early) |
| Census Gazetteer/FIPS + HUD ZIP + SEC CIK/ticker + GLEIF LEI | Entity resolver crosswalks | bulk files | none | GLEIF free OC-to-LEI bi-weekly file (>50% coverage) | **GREEN** (the moat's spine) |
| poweroutage.us | Utility Reliability | site/API | — | ToS bans scraping/redistribution/derivatives | **RED** (self-collect utility maps + EIA-861) |
| EIA-861 (SAIDI/SAIFI) | Utility ground truth | spreadsheets | none | annual census | **GREEN** |
| MuckRock API | FOIA Health | REST API | free account (5-min tokens) | 1 req/s; reads free (filing costs credits) | **GREEN** (read-only) |
| CourtListener / RECAP (Free Law Project) | Corporate Distress dockets | REST API v4 + quarterly bulk | none | May-2026 rate cut → FLP membership advisable | **GREEN** (prefer bulk) |
| MSRB EMMA continuing disclosures | Hospital/muni distress | website (free) / paid feed | none | no free bulk API | **YELLOW** (polite cached scrape) |
| GoFundMe medical campaigns | Medical-Debt | — | — | ToS §12.3 bans scraping + ML; ethics | **RED / DEAD** |
| USDA SNAP issuance schedules | (join input) | published | none | free | **GREEN** (but J-14 thesis dead) |
| NielsenIQ Retail Scanner (Kilts) | J-14 retrocast | paid, tenure-gated | — | ~$800/yr, academics only | **RED** (breaks retrocast on covenant) |

---

## 6. Constitutional amendments required (for Fable to fold into OBSERVATORY.md)

These are the covenant edits the evidence forces. Each is load-bearing.

1. **Spend covenant honesty (covenant 6).** Change "literally $0 marginal" → **"~$0–3/month marginal (Cloudflare R2 storage overage only), well inside the $50/month floor."** Encode as *requirements*, not nice-to-haves: R2 with a **free custom domain** for free egress (never raw `r2.dev`); **Cloudflare Pages** as primary host; **ban Git LFS** and **ban hot-serving `raw.githubusercontent.com`**; standard runners only.

2. **Scheduling reliability (new, → Phase 3 ops).** GitHub cron drift is unbounded and worsening. **Mandatory:** over-schedule + dedupe, avoid `:00`, and an **external dead-man heartbeat** that alerts on missed archive commits. This is a direct defense of the "collect before you can compute" doctrine — a silently-stopped cron loses perishable data forever.

3. **Scraping-hygiene covenant, tightened (covenant 1).** Not just "logged-out + robots-respected." Add: **never circumvent technical access controls** (no IP rotation to evade blocks, no CAPTCHA-solving, no bot-detection evasion), **never create accounts or accept any ToS**, enforce rate-limiting/caching so no server is impaired, and **publish derived facts/statistics — never verbatim scraped prose** (Feist; quote source text only minimally). This is now legally load-bearing: 2025–26 CFAA/CDAFA revival (X Corp v. Bright Data) targets circumvention, not passive reading.

4. **Defamation guardrails made constitutional (covenant 4 / standing doctrine).** (a) **Measurement-not-prediction is a legal doctrine** — every named/signature claim is past/present-tense computed comparison with receipts, never an implied future-conduct assertion. (b) **Full disclosure on every number** — linked receipt + frozen versioned methodology, so "opinion on disclosed true facts" applies by construction. (c) **Accuracy is a legal control** — data-quality/methodology bugs are liability events; pre-publication reconciliation + a public corrections log are required. (d) The **named-claim firewall** (retrocast track record + frozen rubric + operator sign-off) is retained as the single strongest liability shield.

5. **Observer-effect clause, hardened (covenant 2 / I-13).** Bank and financial-institution stress indexes are **permanently aggregate-only, never naming an individual institution** — a non-waivable constitutional guardrail, reinforced by the June-2026 Andrew Left/Citron criminal conviction and the hostile enforcement climate around disclosed-methodology financial research. Extend a "no perceived trading interest / no positioning" discipline to any named financial or market claim.

6. **Permanent "do-not-collect" register (new).** Encode the RED corpora as standing prohibitions so they are never re-litigated: **Legacy.com** (all automated access), **GoFundMe** (§12.3 + ethics), **poweroutage.us** (redistribution), **SERFF/NAIC** (clickwrap anti-automation), **Amazon/Glassdoor/Indeed reviews** (ToS/closure), **Flipp** (SPA + no-competing clause), **NielsenIQ/Kilts** (paywall). Any future revival is a hard stop needing fresh operator sign-off.

7. **Government-continuity / stale-data posture (new, → orphan protocol).** The federal appropriations lapse (since Oct 1, 2025) means official refreshes can freeze. Prefer **archived flat files as the retrocast-of-record**; every index page carries a stale-data banner; the orphan protocol wires this in.

8. **Naming (working name).** "The Observatory" is retained only as a **descriptor**; the defensible primary mark + domain is a distinct, ownable name (see §9). Requires the operator's decision to un-lock/adjust the working name.

---

## 7. Legal foundation (detail)

- **Vessel:** single-member LLC in a low-fee home state (avoid California's $800/yr franchise tax), WHOIS privacy per covenant, ~$50–300 one-time — **as the operating shell only. An LLC does NOT shield the operator from his own defamation** (an intentional tort he commits personally).
- **The real content shield:** **media-liability insurance** (~$500–1,800/yr for $1M limits; general liability covering libel as "advertising injury" is ~$350–900/yr; deferrable until first publish) + **state anti-SLAPP** (40 states + DC with fee-shifting, free) + the receipts/retrocast rigor itself (which *is* the truth/opinion-on-disclosed-facts defense). Route insurance through **INN's preferred-carrier program** (Endless Insurance Services) once the project is INN-eligible.
- **Grant access without a 501(c)(3):** **fiscal sponsorship** — Tiny News Collective via LION (3.5–7%, cheapest journalism-specific), **NEO Philanthropy** (6–10%, best category fit — it incubated *The Markup*, an almost-identical data-journalism-on-tech-harms org), Social Good Fund (6–8%, low upfront) as backup. Defer your own 501(c)(3) until ~$500k/yr justifies it.
- **Scraping law (2026):** CFAA is off the table for logged-out public pages (Van Buren, hiQ, Meta v. Bright Data), **but** favorable rulings are non-final Ninth-Circuit district decisions partly on appeal, and residual **breach-of-contract / CDAFA / DMCA / copyright** exposure is the live risk — mitigated entirely by the tightened scraping-hygiene covenant (§6.3).
- **Total year-one legal cost:** ~$100–500 to start, ~$1,000–2,500/yr once insured. Inside the covenant.

---

## 8. Funding path (detail)

**Year 1 (bridge, no vessel needed):** Data-Driven Reporting Project (≤$35k, freelancers, *explicitly funds server time/data-tools*, opens ~Jan; needs a lightweight newsroom publishing partner) + Pulitzer data-journalism ($10–20k) + Fund for Investigative Journalism (≤$10k, next deadline **Sep 14, 2026**) + Tarbell ($1–20k, covers API/data costs). These pay for exactly the prototype+retrocast work and validate the receipts/retrocast framing publicly.

**Year 2 (anchor):** **RJI Professional Innovation Fellowship** — $75k individual / **$100k emerging-technology track** (target this one, given the LLM-semantic-join core), individuals eligible, no 501(c)(3), open-source deliverable. Current cohort closed (Feb 2026); **next cycle opens ~Nov 2, 2026 for a 2027 start.** Prepare through fall 2026. In parallel, stand up the fiscal-sponsor vessel once one index has a published precision/recall — this converts the invite-only/501(c)(3) tier from closed to reachable.

**Years 2–3 (relationships, not budgeted revenue):** warm 1–2-page LOIs to **Sloan** (Doron Weber / Joshua Greenberg), track **Mozilla** open calls and the **Humanity AI** summer-2026 $10M open call (org-scale, apply via the sponsor), and get on Knight/Democracy Fund's radar by *being cited*, not cold-applying. **Do not budget year-2 survival on any invite-only foundation.**

---

## 9. Naming & domains — operator decision recorded

**The problem:** "The Observatory" is a category label, not a defensible mark. Sharpest collision: **Columbia Journalism Review's own long-running column literally titled "The Observatory"** (media/science/accountability — direct audience overlap). Also live in-sector: NYU Ad Observatory, EU EDMO, the Observatory on Information and Democracy (RSF/Forum), IPI's disinformation observatory, Digital Watch Observatory. Every bare domain — `observatory.com/.org/.io/.us/.institute`, `theobservatory.com/.org`, `the-observatory.org`, `observatory.report` — is **taken** (I verified live). Only weak-TLD and coined/qualified variants remain open.

**Recommendation:** keep "observatory" as a *descriptor* ("an observatory for shadow statistics") and lead with a distinctive, ownable mark. Ranked shortlist (all availability operator-to-reconfirm at a registrar + USPTO TESS before buying; buy the domain, then set it as the Bluesky handle via TXT DNS):

1. **The Exhaust → `theexhaust.org`** (open, ~$8.49/yr). Encodes the core "reads civilization's exhaust" metaphor; zero sector collisions; clean handle `@theexhaust.org`. **Strongest.**
2. **The Leading Indicator → `theleadingindicator.org` / `leadingindex.org`** (open). Econometrically resonant ("measures before the official number"); professional; collision-free.
3. **Observatory Data → `observatorydata.org`** (open). Least-bad way to *retain* "Observatory"; still search-diluted.
4. **`observatory.news` / `theobservatory.news`** ($17.99/yr, open) — fallback only if "The Observatory" is kept unqualified; accept the CJR collision and search burial.
- **Avoid** the `shadowstats*` family — `shadowstats.com/.org` are taken *and* it's the exact crank-adjacent brand the anti-ShadowStats clause defines the project against.

**Operator decision (this session — DECIDED):**
- **Naming direction: "The Exhaust" → `theexhaust.org`.** The public/brand mark is **The Exhaust**; "observatory" is retained only as a descriptor ("an observatory for shadow statistics"). Operator must reconfirm availability at a registrar, register with WHOIS privacy (covenant 5), run a USPTO TESS + common-law check, and set the domain as the Bluesky handle via TXT DNS. *(The repo folder `observatory/` and the constitution filename `OBSERVATORY.md` are left unchanged for now — renaming them is a cosmetic Phase-3+ task, not worth the churn mid-project.)*
- **Home metro: San Antonio, TX.** San Antonio is **not** among BLS's 17 monthly food-at-home CPI metros, so the clean-ground-truth anchor is **Dallas–Fort Worth** (same-state Texas proxy, "most relatable" per the operator). Pilot triad = Dallas–FW (Texas anchor) + two diverse metros (e.g., a coastal high-cost metro like NY–Newark and a Sun Belt metro like Phoenix) — final pair is a Phase-3 detail.

---

## 10. Revised year-1 sequence (supersedes vision §6.3)

| When | What | Exit criteria |
|---|---|---|
| **Now (Phase 3, Fable)** | Reconcile this doc → `03-GAMEPLAN.md`: fold in the §6 amendments; design the archival-cron fleet, the dead-man heartbeat, the entity-resolver spec, the retrocast harness, and the orphan protocol | gameplan + ops specs exist |
| **Immediately post-Phase-3** | **Archival crons first, everywhere** — ATS full-board snapshots, WARN, NHTSA complaints deltas, CMS PBJ/deficiency snapshots (CMS overwrites!), ALEC/SiX model-bill pages, Kroger basket, circulars. Every uncollected week is lost forever, and cron drift means over-schedule + heartbeat | perishable corpora flowing to R2 at ~$0 |
| **Phase 4 opens (Q4 2026)** | Shared services core + **NHTSA Shadow Recalls retrocast** → publish P/R + lead-time distribution (the first credibility artifact). **Shadow Layoffs observational** (WARN Watch + posting-diffs) launches in parallel; forward-validation clock starts | first retrocast published; WARN Watch auto-posting |
| **Q1 2027** | **Hospital/Care Distress retrocast** (PBJ staffing → harm deficiency) — the cleanest second. **Legislative Authorship** ports the text-provenance engine, replicates the 2019 study, goes live for the Jan–Apr statehouse session (aggregate/observational only). **FOIA micro-index** ships as the journalist gift | two more retrocasts public; statehouse artifacts in-session |
| **Q2 2027** | **Grocery/Shrinkflation forward pilot** (Kroger basket across BLS metros — *after* the human ToS read; operator's metro + 2 diverse) + mouseprint shrinkflation retrocast. First **311 inequality** city or **Say-Do** pilot as a clean no-incumbent win | weekly per-metro artifact; CPI-divergence chart on release days |
| **Q3 2027** | Track Record page v1 (every call scored); Bank Stress **aggregate** index; Mortality re-scoped groundwork (CDC harness + permissioned funeral-home panel, no publication); Corporate Distress via CourtListener bulk | the credibility flywheel visibly turning |

**Year-1 definition of done (revised):** **NHTSA recalls retrocast published with P/R + lead-time; Shadow Layoffs observational + forward-validation scorecard live; Hospital Distress retrocast published; WARN Watch + one statehouse index + the FOIA micro-index self-posting; one external citation; total cash ≈ domains + LLC + ~$2–3/mo R2 + a couple of gated ~$90 backfill runs.**

---

## 11. New/reframed indexes surfaced by the research

- **Cross-city 311 Civic-Response Inequality (I-17, elevated):** no live cross-city incumbent; clean city open-data APIs; "potholes fixed in 4 days in [rich zip], 38 in [poor zip]" is pre-localized local-press candy. Strong early win. (Medium-confidence "no incumbent" — do one deeper prior-art pass.)
- **Say-Do semantic gap (I-16, elevated):** ProPublica Represent + its Congress API died July 2024, leaving a hole; the receipts-attached *semantic* say-vs-vote join is genuinely new. Build on roll-calls you ingest yourself (Congress.gov/GovTrack/Voteview) — Represent's death is the cautionary tale about single-source dependence.
- **Drug-Safety validation layer (I-14, reframed):** don't build another FAERS disproportionality dashboard (saturated); build the missing layer — signals **retrocast against confirmed FDA label changes/recalls with published precision/recall**.
- **Worker-Sentiment-from-Forums (I-11 review-leg, reframed):** Reddit non-commercial API, retrocast against an independent labor-stress ground truth (WARN/JOLTS quits), explicitly **not** a Glassdoor proxy.
- **SNAP promotion-timing (J-14, reframed if kept):** shelf-price gouging is a published null result, but *marketing/display/promotion* timing around issuance is less-covered — build only if a free-data retrocast against a named ground truth is feasible, else cut.

---

## 12. Open decisions for the operator (and errata for the vision doc)

**Decisions made by Michael (this session):**
1. **Naming → "The Exhaust" (`theexhaust.org`)**, "observatory" retained as descriptor. Remaining operator errands: registrar reconfirm + WHOIS-private buy, USPTO TESS check, Bluesky handle via TXT DNS.
2. **Home metro → San Antonio, TX.** Not a BLS monthly-CPI metro → use **Dallas–Fort Worth** as the relatable Texas anchor for the inflation pilot (+ 2 diverse metros, Phase-3 detail).

**Errata the vision doc asserted confidently that turned out false (for the record):**
- "layoffs.fyi is literally our labels file" ✅ true — but the *posting-history* side to backtest against it is not freely reconstructable.
- "Wayback Machine circular/listing archives" sufficient for inflation retrocast ❌ — SPAs; no archived item data.
- SaferProducts "public API — people report injuries months before recalls" ⚠️ — the raw incident feed (`opendata.cpsc.gov`) is decommissioned; use NEISS/Violations/Clearinghouse or the NHTSA-first path.
- "Amazon ToS forbids scraping… resolve" — resolved: **closed entirely** (May 2026), not merely gray.
- Legacy.com "position on counting (not copying)" ⚠️ — ToS forbids *all* automated access; counting-not-copying satisfies ethics but not the contract.
- BED "(the vision corpus conflates them)" — BED is a **BLS** product, not Census; separate API/key.
- J-14 "nobody has looked" ❌ — Goldin/Homonoff/Meckel (2022) looked and found a null result. **New standing rule for Phase 3 join-scoring:** run a 15-minute Scholar/NBER/AEA prior-art scan on any "novel" join before pre-registering it.

---

*End of Phase 2 research. The constitution lives in [OBSERVATORY.md](../OBSERVATORY.md); the ideation corpus in [01-VISION.md](01-VISION.md). What survived this phase is real, sourced, and buildable. Fable: reconcile, amend the covenants (§6), and encode the archival-first, dead-man-guarded, retrocast-gated machine.*
