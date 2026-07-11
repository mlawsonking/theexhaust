# 01-VISION — The Observatory, Phase 1 ideation corpus

*Fable, 2026-07-10. Status: complete. Successor document: `02-RESEARCH.md` (Opus).*

---

## 0. Handoff note to Opus

Everything in this document is stated confidently and believed honestly, and **none of it is verified**. Your job is to try to kill it. For every index: confirm the corpus exists at the claimed access level (API? bulk? scrape-tolerant? ToS?), confirm the ground truth exists to retrocast against, cost the retrocast and the steady state at real corpus sizes under the spend covenant (subscription sessions + local 4080 + free compute; metered API gated per-run), map the legal surface (CFAA/ToS, defamation given the naming gate, the obituary constraints), and survey prior art honestly — if someone already does it live and public and well, we link to them instead of competing (§4.5). Mark every index **VIABLE / VIABLE-WITH-CHANGES / DEAD**. Re-score the portfolio in §6 with real numbers; the ranking is my prior, not a commitment — but if you dethrone Shadow Layoffs as index #1, you must beat the argument in §6.2, not just re-add the scores. Also research: the civic-data grant landscape (Knight, Sloan, Reynolds/RJI, Democracy Fund, NNIP and peers), LLC + media-liability insurance for the operator, domain/handle availability for "The Observatory" naming family, and the consolidated kill-question list in §9. The operator has authorized ambition in ideation and ruthlessness from you. Kill without sentiment; what survives you gets built for years.

---

## 1. Thesis and positioning

The full thesis lives in [OBSERVATORY.md](../OBSERVATORY.md). What this section adds: how the Observatory is positioned against the things it will be mistaken for.

**Against official statistics:** not a rival, a pacemaker. Every index is chained to its official number and grades itself against it as it arrives. We are not "alternative facts"; we are the same facts, earlier, with receipts. The Observatory succeeds when the official layer speeds up — an index made redundant retires with a public plaque (lag removed, mission accomplished). Private weather models forced NOAA; that is the template.

**Against ShadowStats-style "alternative statistics":** the name "shadow statistics" sits one step from crankery (shadowstats.com: opaque, unfalsifiable, beloved of goldbugs). We keep the evocative name and become its methodological opposite — every number links to raw receipts, every method is versioned and rerunnable by critics, every index carries its own public scorecard. The moment we publish a number whose derivation a hostile PhD can't rerun, we've become the thing we replaced.

**Against the satellite-data hedge funds:** they already trade on exhaust and keep the shadow statistics private. We drag the asymmetry into the open. This is the Bloomberg move (scattered-but-existing data → indispensable terminal) executed as a public good instead of a terminal.

**Against academic one-offs:** the celebrated studies exist — USA Today's copy-paste-legislation investigation (2019), MIT's Billion Prices Project (wound down ~2016, privatized as PriceStats), obituary-based excess-mortality papers (COVID era). They validated the methods and then *stopped*. The Observatory's differentiator is not cleverness, it's **permanence**: replicate the famous study, then keep it running forever, automatically. "Replicate, then run" is standing doctrine — each launch inherits the original study's credibility and press hook.

**Against crowdsourced trackers (layoffs.fyi, WARN trackers, GVA):** they aggregate what already surfaced. We measure what hasn't surfaced yet, validated retrospectively. Where they're good, we cite and link them (and use them as retrocast ground truth — layoffs.fyi is literally our labels file).

**The one-sentence identity:** *The Observatory reads civilization's exhaust and publishes the numbers early, with receipts, and keeps score on itself in public.*

---

## 2. Covenants as design constraints

The ten operator covenants are in [OBSERVATORY.md](../OBSERVATORY.md) and bind everything below. The four that shape ideation most:

1. **The naming gate** (covenant 2) splits every index into two products: a day-one **aggregate index** plus (where applicable) a gated **named-entity signature feed** unlocked by published track record. Exception that matters enormously for sequencing: *observational facts with receipts* — "Company X pulled 78% of its engineering postings in 3 weeks (here are the diffs)" — are reporting, not inference, and publish day one. Indexes whose day-one artifact is observational-with-receipts have a distribution head start over indexes whose punch is locked behind the gate.
2. **The spend covenant** (covenant 6) means engines must run on a 4080 + free Actions + subscription sessions. This forces (and rewards) the OnScript pattern: deterministic cores (n-grams, diffs, entity tables) carry the product; LLM semantics are an enhancement layer, batched and cached; embeddings run local. Assume Haiku-class batch pricing only inside gated backfills.
3. **The obituary covenants** (covenant 3) are identity-level: aggregate-only, county-month floor, no names ever, nothing from that corpus ever sold.
4. **Zero-organic scar tissue** (covenant 8 + operator answer 12): PlainSpeak and GrantForge died with no organic traffic and literally zero ad click-throughs. Therefore: no artifact ships unless it is *born shareable* (a chart + a sentence + a receipts link that a journalist can paste into a story), and distribution is engineered as newsworthiness + citability, never purchased.

---

## 3. The engine architecture — build engines, not indexes

The universe below looks like ~30 indexes. It is actually **five engines** wearing thirty costumes. This is the insight that makes a solo-operator observatory plausible: every index in a family shares its family's ingestion, matching, and retrocast machinery; a new index in an existing family costs a corpus adapter and a methodology doc, not a new system.

| Engine | What it does | Powers (indexes below) |
|---|---|---|
| **E1 — Posting-Diff** | Snapshots public job boards (Greenhouse/Lever/Ashby JSON endpoints, career pages), diffs postings over time: pulls, freezes, additions, language changes, posted pay ranges | Shadow Layoffs, Shadow Wages, Ghost Jobs, staffing signals feeding Hospital Distress & College Viability |
| **E2 — Text-Provenance** | First-appearance ledger of content n-grams + similarity joins across text corpora; **direct descendant of the proven OnScript engine** (76k-record corpus, two-pass memory-bounded, deterministic citation verifier, adoption curves) | Legislative Authorship, Regulatory Capture, Say-Do Index, school-policy provenance |
| **E3 — Hazard-Language** | Classifies free-text consumer/worker reports against hazard taxonomies; builds "pre-event signatures" from labeled history | Shadow Recalls (consumer products, vehicles, food), Workplace Safety, Nursing-Home Understaffing language leg, App-Scam Signatures, Drug Safety forums leg |
| **E4 — Price/Package** | Extracts product, price, and net-quantity from circulars/listings/menus; entity-resolves products to CPI-basket categories over time | Shadow Grocery Inflation, Shrinkflation, Menu/Delivery-Tax, rent-listing leg of Shadow Shelter |
| **E5 — Filing-Drift** | Monitors structured-ish official filings (EDGAR full-text, CMS cost reports, PBJ payroll, IRS 990s, EMMA municipal bonds, SERFF insurance, FDIC call reports) for drift: language softening, ratio decay, auditor/officer churn | Corporate Distress, Hospital Distress, College Viability, Bank Stress, Insurability Retreat, Utility Reliability |
| Shared services | **Entity resolver** (the semantic-join core: product↔product, company↔company, place↔place, no shared keys), **retrocast harness** (one falsification protocol, reused), **receipts store** (every published number → immutable evidence bundle), **artifact compiler** (index output → chart+sentence+receipts, per surface) | Everything |

Phase 3 designs these as the actual repo layout; Phase 4 builds E1 + shared services first (see §6.3). The retrocast harness and entity resolver are the deep moat — they amortize across every index and are exactly the parts a copycat won't bother building.

---

## 4. The index universe

Format per entry — **Corpus** (exhaust in) / **Shadows** (official number + lag removed) / **Retrocast** (ground truth + falsification) / **Artifacts** (day-one vs. gated) / **Audience** (who cites / who hates) / **[P2]** kill-questions for Opus.

### 4.1 Tier 1 — flagship candidates (deep entries)

#### I-1. Shadow Layoffs & Hiring Freezes — engine E1

**Corpus:** company job boards via public JSON endpoints (Greenhouse `boards-api.greenhouse.io`, Lever `api.lever.co/v0/postings`, Ashby, SmartRecruiters — thousands of companies expose these unauthenticated because their own career pages consume them), plus raw career-page snapshots for the rest; state WARN notices (all 50 states publish, in gloriously incompatible PDFs/HTML — unifying them is itself a public service nobody has done well); GitHub org commit/actor decay for tech; H-1B LCA & PERM filings (DOL bulk files) as hiring-intent signals; 8-K workforce-action language (EDGAR full-text search).

**Shadows:** BLS JOLTS (≈2-month lag, national/industry only), monthly jobs report (survey), state WARN (60-day legal notice, scattered, tech-press discovers them late). Lag removed: weeks-to-months at company granularity that no official number has at all.

**Retrocast:** the cleanest labels file in the whole universe — layoffs.fyi (crowdsourced, dated, company-level, 2020→present), unified WARN archives, and press-confirmed layoffs 2022–2025. Falsification protocol: for each labeled layoff, was there a posting-pull/freeze signature in the prior 2–12 weeks? Against matched control companies (same size/sector, no layoff), what's the false-positive rate? Publish the full precision/recall curve and the lead-time distribution. This retrocast is a weekend of compute against archived data *if* posting history can be reconstructed — **[P2]** the existential question: does historical posting data exist (Wayback coverage of Greenhouse/Lever endpoints? aggregator archives? academic corpora like LinkUp/Burning Glass have it but are paid — is there a free reconstruction path)? If history is thin, the retrocast runs on 2022–2025 partial archives + a forward-validation year — design the degraded version.
**[P2]** Greenhouse/Lever/Ashby ToS on programmatic access; polling etiquette; coverage bias (these skew tech/white-collar — say so on the index page, or does WARN+8-K coverage de-bias it?).

**Artifacts:** day-one observational (no gate needed): weekly "hiring pulse" per company/sector — postings added/pulled with receipts (the diffs themselves); "WARN Watch," the unified same-day WARN feed with per-state pages (instant utility, currently nobody does this well); sector dashboards (e.g., "games industry postings −34% YoY"). Gated (post-track-record): the signature feed — "Company X's 3-week posting collapse matches the pre-layoff signature of 41/55 historical cases." Bonus artifact with teeth: **ghost-job exposure** — postings open >N months with repost churn and no hire signals, joined to PERM filings (posted-to-satisfy-immigration-law jobs) — every jobseeker in America shares this one.

**Audience:** tech/business press cites layoffs.fyi constantly; a receipts-attached leading version is catnip. Workers, unions, local reporters (WARN is inherently local). Who hates it: PR departments, HR-tech vendors, any company mid-quiet-layoff. Defamation surface is low for the observational layer — the receipts are the company's own public postings.

#### I-2. Shadow Recalls (Product Safety family) — engine E3

**Corpus:** CPSC SaferProducts.gov incident reports (public API — people report injuries months before recalls); CPSC recall archive (API); NHTSA vehicle complaints (VOQ bulk downloads — free, huge, and the join to recalls is by make/model/year, *no fuzzy matching needed*); openFDA FAERS (drugs) and CAERS (food/cosmetics); retail review corpora (the legally grey one — Amazon ToS forbids scraping; **[P2]** resolve: review datasets with licenses? court-tested public-page positions? partner APIs? Reddit product-failure threads as substitute?); customs bills of lading (public records, ImportYeti-style) for factory-provenance joins.

**Shadows:** CPSC/NHTSA/FDA recall announcements. Lag removed: the well-documented months-to-years between injury pattern and recall.

**Retrocast:** the original clean-weekend falsification, and it stays: take all CPSC recalls 2015–2024; for each, did SaferProducts + review hazard language show the signature pre-recall? Precision/recall against never-recalled matched products. **Run the NHTSA version too — it may be cleaner** (both sides official, bulk, keyed) and could be the *first published retrocast* even if the consumer-products version headlines. **[P2]** entity resolution rate between SaferProducts/review text and recall records (this is the hard 20%); FAERS disproportionality prior art (pharmacovigilance is mature science — our addition is *live + public + receipts*, verify that's actually white space).

**Artifacts:** day-one aggregate: hazard-language incidence by product category, quarterly recall-pressure index; the retrocast report itself is a launch artifact ("we backtested a decade of recalls; here's the curve"). Gated: the named watchlist — "products currently matching the pre-recall signature" — the single holiest holy-shit artifact in the universe, unlocked by track record + rubric + operator sign-off. Joins-powered bonus: **the factory map** — "this recalled product's manufacturer also supplies these 12 other brands" (bills of lading ⋈ listings), which turns every recall news cycle into an Observatory citation.

**Audience:** consumer journalists (recall stories are evergreen), class-action attorneys (they'll want the feed — revenue line), parents, CPSC itself (it's understaffed and knows it). Who hates it: manufacturers, marketplaces, eventually the agency if we embarrass it. Defamation surface is the highest in the portfolio — which is exactly why the naming gate exists and why this index's aggregate year buys the track record.

#### I-3. Shadow Legislative Authorship ("Who Wrote This Law?") — engine E2

**Corpus:** state bill text (Open States / LegiScan APIs; 50 states + Congress via GovInfo); model-bill libraries (ALEC publishes its own; SPN affiliates; ALICE and progressive counterparts — assembling the model-text corpus is the real work **[P2]**); lobbying disclosures (federal LDA, state registries); regulations.gov comment letters ⋈ final rule text (the Regulatory Capture sibling, same engine).

**Shadows:** nothing — no official number exists for "who wrote this law." This shadows a number society *should* have. Lag removed: infinite, in a sense.

**Retrocast:** "Replicate, then run" at its purest — reproduce USA Today/Arizona Republic/Center for Public Integrity's 2019 copy-paste-legislation findings (10,000+ model-bill copies, 2010–2018) with our engine, publish agreement/divergence, then run it live forever with adoption curves (which the 2019 team couldn't do — and which OnScript's first-appearance ledger + adoption-curve machinery already does at 76k-document scale for $0 LLM).

**Artifacts:** day-one (all observational — quoting public bill text against published model text is reporting): per-state session scorecards ("31% of introduced bill text this session matches model-library text — receipts"); per-legislator "original authorship rate"; the live adoption map of a specific model bill spreading across statehouses (the artifact statehouse reporters will screenshot); "first appearance" attributions. National wire services and 50 separate statehouse press corps = 51 distribution surfaces. Timing: US statehouses run January–April; launching for the 2027 session is a natural deadline.

**Audience:** statehouse reporters (a starving, shrinking corps that will love us), democracy-reform orgs, political scientists. Who hates it: ALEC, lobbyists, legislators with 4% originality scores — symmetrically, both parties' model-bill machines (engine E2 inherits OnScript's symmetry-audit discipline; nonpartisanship is enforced by construction, same thresholds both directions).

**[P2]** LegiScan/Open States free-tier ceilings at 50-state scale; model-bill corpus assembly cost; how much the 2019 dataset is public/reusable as seed ground truth. Brand note: keep Observatory and OnScript separate brands (one measures markets-and-institutions, one measures political speech) — shared engine, separate mastheads, so consumer indexes never inherit political valence.

#### I-4. Shadow Grocery Inflation + Shrinkflation — engine E4

**Corpus:** grocery circulars/weekly ads (aggregated publicly by Flipp and retailer sites — **[P2]** access posture), retailer online prices for a fixed representative basket, printed net-weight/count on listings (shrinkflation is literally printed on the package image), archived menus. Historical: Wayback Machine circular/listing archives — **[P2]** the existential question: is archive depth sufficient to retrocast 2020–2024 against CPI food-at-home per metro?

**Shadows:** CPI (monthly, ~2-week publication lag, metro detail thin and bimonthly for most metros; shelter methodology lags ~12 months by construction). Lag removed: weeks, plus metro granularity CPI doesn't publish weekly anywhere.

**Retrocast:** reconstruct basket series from archives vs. CPI food-at-home (national + available metros) 2020–2024; publish tracking error and lead. This inherits Billion Prices Project credibility (the method is validated academically; BPP tracked CPI beautifully) — and the story writes itself: *the public version died in 2016 and went private; the Observatory brings it back and won't die.*

**Artifacts:** weekly per-metro price pulse ("eggs in [metro] +31% in 6 weeks; CPI prints this in March") — the highest-frequency, broadest-audience artifact in the portfolio (everyone eats); the **Shrinkflation Ledger** — product-level net-weight changes with side-by-side receipts (tabloid-shareable, rigorous underneath, mouseprint.org archives as seed ground truth **[P2]**); a "your grocery basket vs. CPI" divergence chart every CPI release day (piggyback on the official news cycle — guaranteed monthly relevance).

**Audience:** local news (per-metro numbers are pre-localized for them), econ press and econ social media, every household. Who hates it: retailers mildly; mostly nobody — this is the *likable* flagship, the one that buys public goodwill the harsher indexes spend. Prior-art check **[P2]**: Instacart/Numerator/Adobe publish price indexes now — our differentiators are metro-weekly granularity, receipts, shrinkflation unit-honesty, and permanence-with-scorecard; verify that's enough white space.

#### I-5. Shadow Mortality — engine E3-adjacent (its own careful thing)

**Corpus:** the public obituary/death-notice exhaust (Legacy.com claims the large majority of US obits; funeral-home site notices; local paper feeds) — under the binding covenants: aggregate counts only, county-month floor, no names or text ever republished, nothing from this corpus ever sold. **[P2]** the existential question is access ethics + ToS: Legacy.com's position on counting (not copying), the polite-scraping posture, and whether coverage bias (who gets an obit — skews older, whiter, more rural, costs money) can be modeled per-county with CDC historicals as the calibration set.

**Shadows:** CDC WONDER final mortality (~2-year lag); provisional counts (months, county-suppressed under 10 deaths). Lag removed: ~18–24 months at county-month granularity, which is where overdose waves, heat deaths, and pandemic echoes actually live.

**Retrocast:** textbook — obit-derived county-month counts 2015–2023 vs. CDC actuals; publish correlation, coverage-bias model, and where the corpus under/over-counts (by county class). Academic one-offs did this during COVID and validated it; nobody kept it running. Age-band and cause inference stay OUT of v1 (names/text constraints limit inference anyway — count deaths, not people).

**Artifacts:** monthly county-level excess-mortality map ~2 years ahead of official; anomaly flags ("County X deaths running 40% over trend since March") that epidemiologists and health reporters check reflexively; every flag links to methodology, never to individuals. Launch posture: second wave, after the Observatory has a track record — leading with the death index sets the wrong tone; arriving at it with earned credibility sets exactly the right one.

**Audience:** epidemiologists, public-health journalists, county health departments (some will quietly love us). Who hates it: nobody legitimately — the risk is ick, not opposition, and the covenants + a published ethics page are the design answer.

#### I-6. Shadow Hospital & Care-Infrastructure Distress — engines E5 + E1 (the dark horse)

**Corpus:** all-official, no scraping grey zone at all — CMS Hospital Cost Reports (HCRIS, public), CMS Payroll-Based Journal nursing-home staffing (actual payroll data, quarterly, public), EMMA municipal-bond continuing disclosures (hospital borrowers file distress in public), CMS inspection/deficiency records, plus E1 job-posting decay at specific facilities.

**Shadows:** nothing timely — rural hospital and nursing-home failures surprise their communities; official datasets describing the decline publish years late. ~150 rural hospital closures since 2010, each with a paper trail visible in advance *in public filings nobody joins together*.

**Retrocast:** clean and profound — take every closed rural hospital 2010–2024 (closure lists exist, e.g., UNC Sheps Center **[P2]**); reconstruct each one's cost-report trajectory, bond disclosures, and staffing pattern; extract the pre-closure signature; score against surviving matched facilities. Nursing-home sibling: PBJ staffing levels vs. subsequent inspection harm citations (both sides public and keyed — minimal entity-resolution pain).

**Artifacts:** day-one aggregate: county care-fragility map ("14 counties where the sole hospital shows the distress pattern" — county-level framing before facility naming). Gated: the facility watchlist — genuinely life-adjacent information for the towns involved; this is the index where the naming gate earns moral weight, because early warning gives communities time to fight (bond campaigns, mergers, state intervention) instead of waking up to a closed ER. Nursing-home understaffing artifact: "facilities below safe-staffing signature" — families choosing homes will use it.

**Audience:** health-policy press, state legislators, hospital associations (grudgingly), families. Who hates it: hospital chains and nursing-home operators, plus the observer-effect worry (does flagging a hospital accelerate its death? — the counter: bond markets already know; only the town doesn't; we equalize). Score high, build second — it needs E5+E1 mature. Year-2 flagship.

### 4.2 Tier 2 — second wave (solid entries, medium detail)

**I-7. Shadow Wages & the Pay-Transparency Corpus (E1).** Posted salary ranges (now legally mandated on postings in CA/WA/NY/CO and spreading) → real-time wage index by metro/occupation vs. ECI (quarterly) and OES (annual, ~1-year lag). The corpus *didn't exist before 2023* — genuinely new instrument. Artifacts: "Shadow Pay" lookup (median posted range per title/metro — every jobseeker's negotiation page) + wage-growth nowcast. Retrocast: short history; validate against Indeed/ADP published indexes + first OES overlap. **[P2]** range-inflation gaming ("$40k–$400k") detection.

**I-8. Ghost Jobs Index (E1).** Postings open >N months, repost churn, no-hire signals, PERM-linked postings. Shadows: nothing official (BLS assumes postings are real demand — JOLTS "openings" are self-reported). Artifact: sector ghost-rate leaderboard. Extremely shareable with jobseekers. Retrocast is the weak spot **[P2]**: ground truth for "never intended to hire" is inferential — design a defensible proxy (posting outcome tracking over 12 months) or keep it a labeled *observation*, not a signature index.

**I-9. Shadow Insurability Retreat (E5).** SERFF rate filings (public per state), nonrenewal/moratorium notices, listing-language drift ("cash only," "insurance available" disappearing). Shadows: NAIC annual reports, state DOI approvals — the climate-repricing of America, visible quarterly instead of retrospectively. Retrocast: known market exits (State Farm/Allstate CA 2023, Florida carrier collapses) vs. prior filing signals. Artifact: county "insurance retreat" map. Cites: climate press, housing economists, state legislators. **[P2]** SERFF bulk access varies by state — how many states are machine-readable?

**I-10. Shadow Small-Business Births & Deaths (E4/E5-adjacent).** Secretary-of-State registrations (many states: bulk/API), liquor/health/sign permits (city open data), Google-Maps-closure signals (**[P2]** ToS — probably out; permits carry it). Shadows: BLS Business Employment Dynamics (~8-month lag); Census BFS (weekly but formations-only). Artifact: metro storefront churn index — local news candy. Retrocast vs. BED historicals.

**I-11. Shadow Workplace Safety (E3).** Employer-review language ("unsafe," "understaffed," "OSHA" mentions) + OSHA inspection/violation history (public API). Retrocast: review-language signature vs. subsequent serious OSHA violations 2016–2024 — both sides public. Gated named tier; aggregate sector index day one. **[P2]** Glassdoor/Indeed review access is ToS-hostile — is there a viable corpus (their own public pages? court positions? worker-forum substitutes)?

**I-12. Shadow College Viability (E5 + E1).** IPEDS (public, lagging), IRS 990s, EMMA bond filings, posting decay, enrollment-deposit chatter. Shadows: accreditor warnings that arrive months before abrupt closures stranding students (a real 2023–2026 phenomenon). Retrocast: closed colleges 2016–2025 (closure lists exist) vs. financial trajectories. Artifact: gated watchlist + day-one sector fragility index. Families choosing schools = mass audience moment each spring.

**I-13. Shadow Bank Stress (E5) — the ethics case study.** FDIC call reports (quarterly, public, keyed!), branch-closure filings, deposit-rate desperation signals. Retrocast: failure list + enforcement actions vs. prior call-report drift — textbook-clean data. **But:** naming a bank as matching a failure signature can *cause* the failure (SVB was a Twitter run). This index exists in the universe to force the constitution to grow an **observer-effect clause**: some signature feeds stay aggregate-only permanently, regardless of track record. Build the aggregate regional-bank-stress index; the named tier may be permanently sealed. **[P2]** legal exposure for bank-run-adjacent speech is its own research item.

**I-14. Shadow Drug Safety (E3).** openFDA FAERS disproportionality (established pharmacovigilance science) + patient-forum language, live and public, vs. eventual label changes/boxed warnings (retrocast ground truth: openFDA label-change history). Prior art is academic/industry-internal; white space is *public + live + receipts*. **[P2]** confirm no one already publishes this well (RxISK et al.).

**I-15. Shadow Utility Reliability (E5).** Archive ephemeral outage maps (poweroutage.us aggregates; raw utility maps vanish — "collect before you can compute") vs. utilities' self-reported SAIDI/SAIFI reliability filings to PUCs (annual, self-graded homework). Artifact: "Utility X actual outage-hours run 2.1× its filed reliability number." Cites: PUC intervenors, local press during storm season. Hates: utilities, precisely and deservedly.

**I-16. Shadow Say-Do Index (E2).** Politicians' press-release positions ⋈ their roll-call votes (both public, semantic join — "said X, voted not-X"). OnScript-adjacent machinery, Observatory framing (institutional accountability, both parties, symmetric thresholds). **[P2]** check against existing vote-tracking prior art (ProPublica sunset, etc.); the *semantic* say-do join at scale is the new part.

**I-17. Shadow Civic Response Inequality (311 family).** ~100 cities publish 311 open data: pothole-fix latency, streetlight repair, dumping cleanup — by neighborhood income/race ⋈ assessed property values. Artifact per city: "potholes fixed in 4 days in [rich zip], 38 in [poor zip]." Retrocast: internal consistency + city auditor reports. Cites: local press, councilmembers. Build cost low (clean APIs); expansion is embarrassingly parallel city-by-city.

**I-18. Shadow Medical-Debt Distress.** GoFundMe medical campaigns (public pages) as an uninsurance/underinsurance distress index, aggregate-only by metro (obituary-grade ethics: no individuals, ever) vs. Census insurance data (annual, lagging) and medical-bankruptcy studies. Humane, damning, and nobody runs it live. **[P2]** ToS + ethics review to obituary standard.

### 4.3 Tier 3 — the long tail (sketches, one line each)

- **FOIA Health Index** — MuckRock API response-time distributions per agency vs. agencies' self-reported annual FOIA reports; tiny build, journalist-audience perfect; candidate "gift to the citing class" micro-index in year 1.
- **Menu & Delivery-Tax Index (E4)** — same-item menu price vs. delivery-app price per metro; "the delivery markup is X%."
- **School-Board Exhaust (E2)** — minutes/agendas corpus: policy-text provenance (model policies spreading district-to-district), teacher-churn from postings; year-3 (thousands of scattered districts).
- **Shadow AI Displacement (E1)** — occupation-level posting collapse (copywriters, support reps) vs. OES lagging a year; topical, retrocast-weak, run as observation not signature.
- **Startup Deathwatch (E5/CT logs)** — cert expirations, app-update cadence decay, status-page death; niche fun, feeds Corporate Distress.
- **App-Scam Signatures (E3)** — app-store review language vs. FTC actions/store removals; consumer-protection adjacent.
- **Court-Delay Index** — case-age distributions from RECAP/state portals; speedy-trial violations; hard corpus, year 3+.
- **News-Desert Accountability Vacuum** — local-news death (UNC data) ⋈ 311 latency ⋈ muni borrowing costs (academic finding: news deserts pay more to borrow — run it live); the meta-index: measuring what happens where nobody measures.
- **Disaster Recovery Velocity** — permit issuance + contractor postings post-disaster vs. FEMA self-reports; humane, episodic.
- **Traffic-Death Nowcast** — local crash reporting ⋈ FARS (~1-year lag); moderate white space (states publish some).
- **Corporate Quiet-Pivot Feed** — CT-log new subdomains, trademark filings, HSR early terminations, integration-manager postings; a signals *feed*, not an index; feeds Corporate Distress.
- **Shadow Shelter/Rents (E4)** — listing-derived rent index vs. CPI shelter's built-in ~12-month methodological lag; prior art strong (Zillow ZORI, academic marginal-rent indexes) — our angle is receipts + the CPI-divergence artifact each release day.
- **Product Quality Decay ("Enshittification Index") (E3)** — star-trajectory + "used to be better" language drift by category; shadows a number that barely exists (ACSI, survey, annual, paid); retrocast-weak, shareability-extreme; run as observation.
- **Shrinkflation Ledger** — broken out above under I-4; listed here because it could stand alone if grocery-price access dies.
- **Public-Company Language Drift (E5)** — going-concern softening, auditor changes, 8-K exec-departure clusters (EDGAR full-text is free and glorious); feeds Corporate Distress index; named tier heavily gated.

### 4.4 Corporate Distress (the operator's personal pick) — where it fits

Not a single index but the E5+E1 **family capstone**: bankruptcy/distress signatures from filings-drift + posting collapse + docket activity (vendor lawsuits precede bankruptcies **[P2]** — CourtListener/RECAP corpus) + quiet-pivot signals. Retrocast vs. Chapter 11 filings 2015–2024 (Altman-Z prior art on ratios; the LLM-era addition is language-drift + exhaust joins). Highest defamation surface after recalls; named tier arrives late, gated hard; short-sellers would pay for it (revenue-doctrine tension — they get nothing the public doesn't). Sequenced year 2–3: it inherits E1 (built for layoffs) + E5 (built for hospitals) nearly free — which is the engine architecture working as designed, and the operator's personal itch getting scratched by the same machinery the public-benefit ranking chose anyway.

### 4.5 Deliberately not building (prior art owns it — link, don't compete)

Gun Violence Archive (live incident tracking) · TRAC Syracuse (immigration courts/FOIA litigation analytics) · Eviction Lab (academic eviction tracking — we may *cite into* it) · wastewater surveillance (WastewaterSCAN/CDC NWSS do it well) · Unusual Whales (congressional trading) · flight/ship live tracking (ADS-B Exchange, existing AIS aggregators) · layoffs.fyi and WARN trackers *as aggregators* (we consume them as ground truth and add the leading layer they don't have). The Observatory links out generously — being a good citizen of the civic-data ecosystem is cheap and compounding.

---

## 5. The join map — the deep moat

Single-corpus indexes are copyable (an aggregator with an intern catches up). Semantic joins across corpora with **no shared keys** — meaning-matched by LLM/embedding entity resolution — are the post-2024 unlock and the durable moat: a copycat needs both corpora, the resolver, *and* the retrocast harness. The named joins, ⋈ = semantic join:

| # | Join | Yields | Why impossible before ~2024 |
|---|---|---|---|
| J-1 | consumer reviews ⋈ recall descriptions | pre-recall signatures (I-2) | hazard language ↔ recall text has no key; product entity resolution across marketplaces is semantic |
| J-2 | model-bill libraries ⋈ 50-state bill text | authorship attribution (I-3) | scale (100k+ bills/session) × paraphrase detection |
| J-3 | comment letters ⋈ final rule text | regulatory capture measurement (I-3 sibling) | same engine, agencies edition |
| J-4 | job-posting diffs ⋈ WARN ⋈ 8-K language ⋈ commit graphs | the layoff signature itself is a 4-corpus join (I-1) | company entity resolution across four corpora with different names for the same employer |
| J-5 | circular items ⋈ CPI basket categories | shadow inflation's semantic core (I-4) | "Kraft Singles 12oz" ↔ "processed cheese, per lb." is a meaning match |
| J-6 | obituary counts ⋈ CDC county-month actuals | the mortality calibration model (I-5) | the join is easy; the *coverage-bias model* per county class is the LLM-era part |
| J-7 | cost reports ⋈ bond disclosures ⋈ facility job postings | hospital pre-closure signature (I-6) | three corpora, three naming schemes for one facility |
| J-8 | bills of lading ⋈ retail listings | the factory map: recalled product → sibling brands from the same factory (I-2 bonus) | importer/consignee names ↔ brand names is pure entity resolution |
| J-9 | SERFF filings ⋈ listing language ⋈ parcel geography | insurance retreat map (I-9) | filings are per-carrier-per-state; retreat is per-place — the join is geographic-semantic |
| J-10 | posted pay ranges ⋈ OES occupation codes | shadow wages (I-7) | job-title → SOC code mapping at posting scale is semantic |
| J-11 | press-release positions ⋈ roll-call votes | say-do gap (I-16) | stance detection + bill-to-statement matching |
| J-12 | review language ⋈ OSHA violations / CMS deficiencies | workplace & care safety signatures (I-11, I-6) | employer/facility resolution + hazard-language classification |
| J-13 | GoFundMe medical campaigns ⋈ census insurance geography | medical-debt distress (I-18) | campaign text → condition/cost/place extraction, aggregate-only |
| J-14 | grocery price timing ⋈ SNAP disbursement calendars | **poverty-timed pricing detection** — do prices rise when benefits hit, per chain per state? | nobody has looked; both corpora public; explosive if real, publishable either way (**[P2]** flag: pre-register the analysis — this is the kind of finding that must survive hostile review) |
| J-15 | local-news death ⋈ 311 latency ⋈ muni borrowing | the accountability vacuum (tail) | the meta-join; academic one-offs exist, live version doesn't |
| J-16 | FAERS disproportionality ⋈ patient-forum language | drug-safety early signal (I-14) | forum slang ↔ MedDRA adverse-event terms |
| J-17 | CT-log subdomains ⋈ trademark filings ⋈ postings | corporate quiet-pivot feed (tail) | three exhausts, one intention |

Doctrine: every flagship index should carry at least one join (J-column) by year 2 — the single-corpus version launches for speed, the join version builds the moat. The **entity resolver** (shared service, §3) is therefore the single highest-leverage engineering artifact in the whole project; Phase 3 specs it first-class with its own accuracy retrocast (resolver precision is publishable methodology, not plumbing).

---

## 6. The ranked portfolio

### 6.1 Scoring

Formula per the constitution: **(insight quality × shareability × retrocast-ability) ÷ (build cost + legal surface)**, each axis 1–5 (cost/legal: higher = worse). Scores are my calibrated priors; Opus re-scores with evidence. A floor rule applies: no score rescues an index below insight 3 (cheap-but-thin doesn't lead), and retrocast-weak indexes (R ≤ 2) can publish only as *observations*, never signatures.

| Rank | Index | I | S | R | B | L | Score | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | **I-1 Shadow Layoffs** | 5 | 5 | 5 | 2 | 2 | **31.3** | day-one observational artifacts; labels file exists; E1 is the cheapest engine |
| 2 | **I-2 Shadow Recalls** | 5 | 4 | 5 | 3 | 2 | **20.0** | aggregate year 1; the gated watchlist is the long-game artifact; NHTSA variant may retrocast first |
| 3 | **I-3 Legislative Authorship** | 5 | 4 | 4 | 2 | 2 | **20.0** | OnScript engine transfer makes B=2; session-timed (Jan–Apr) |
| 4 | **I-4 Grocery Inflation + Shrinkflation** | 4 | 5 | 4 | 3 | 1 | **20.0** | the likable flagship; weekly cadence = weekly artifact |
| 5 | **I-6 Hospital/Care Distress** | 5 | 4 | 4 | 3 | 2 | **16.0** | all-official corpus; year-2 flagship once E5+E1 exist |
| 6 | **I-5 Shadow Mortality** | 5 | 3 | 5 | 3 | 3 | **12.5** | textbook retrocast; second-wave launch posture by design |
| 7 | I-9 Insurability Retreat | 5 | 4 | 3 | 3 | 2 | 12.0 | SERFF access is the swing variable |
| 8 | I-7 Shadow Wages | 4 | 4 | 3 | 2 | 2 | 12.0 | new-corpus advantage; short history caps R |
| 9 | I-16 Say-Do Index | 4 | 4 | 3 | 2 | 2 | 12.0 | engine transfer; check prior art |
| 10 | I-14 Drug Safety | 4 | 3 | 4 | 3 | 2 | 9.6 | white-space check pending |
| 11 | I-12 College Viability | 4 | 3 | 4 | 3 | 2 | 9.6 | seasonal mass-audience moments |
| 12 | I-11 Workplace Safety | 4 | 4 | 4 | 3 | 3 | 10.7 | corpus access is the kill question |
| 13 | I-17 311 Inequality | 3 | 4 | 3 | 3 | 1 | 9.0 | city-parallel; local-press machine |
| 14 | I-10 Small-Biz Churn | 3 | 4 | 3 | 3 | 1 | 9.0 | BED backtest is clean |
| 15 | I-13 Bank Stress | 5 | 3 | 5 | 3 | 5 | 9.4 | observer-effect clause; named tier likely sealed forever |
| 16 | I-18 Medical-Debt Distress | 4 | 4 | 2 | 3 | 3 | 5.3 | obituary-grade ethics; observation-class |
| 17 | I-8 Ghost Jobs | 3 | 5 | 2 | 2 | 2 | 7.5 | observation-class until a defensible outcome proxy exists |
| — | FOIA Health (micro) | 3 | 3 | 4 | 1 | 1 | 18.0 | ratio flattered by tiny build; run it as the year-1 *gift to journalists*, not a flagship |

### 6.2 First index: Shadow Layoffs — arguing with the operator's prior

The founding prompt's prior was Shadow Recalls first ("clean one-weekend falsification"). The interrogation answers changed the calculus, and I'm exercising the invitation to argue:

1. **The naming gate (covenant 2) hits recalls hardest.** Recalls' holy-shit artifact — the named watchlist — is exactly what the gate locks behind a published track record and rubric. Its permitted day-one product ("hazard language in kitchen appliances +40%") is the weakest artifact among the flagships. Layoffs' day-one product is *observational fact with receipts* — posting diffs, WARN unification — publishable and shareable from week one under the covenant's explicit exception.
2. **Zero-organic scar tissue demands day-one distribution.** An index whose best artifact arrives in month 9 repeats the PlainSpeak failure shape (build → silence). Layoffs emits citable material immediately: WARN Watch alone is a public service the tech press will use, and tech/business press is the *easiest* citing class to reach — they already cite layoffs.fyi weekly; we hand them the leading version with receipts.
3. **The retrocasts are equally clean, so the tiebreaker is the artifact.** Layoffs' labels file (layoffs.fyi + WARN + press archive, 2022–2025) is as falsifiable-in-a-weekend as recalls' — *if* posting history reconstructs (the one existential [P2] question). Recalls keeps its clean retrocast regardless of launch order.
4. **Corpus friction favors layoffs.** Greenhouse/Lever/Ashby JSON endpoints are machine-readable and low-drama; recalls' best corpus (marketplace reviews) is the most ToS-contested corpus in the whole portfolio. Don't stake index #1 on the grayest corpus.
5. **Operator preference (covenant 10) agrees** — he wants the layoffs/corporate-behind-the-scenes family most, and index #1 is the one that must survive his sustained attention.

**Therefore:** publication order = Layoffs first. **But retrocast order ≠ publication order:** the recalls retrocast (SaferProducts/NHTSA vs. recall archive) runs early in parallel — it's cheap, it's the original falsification test of the whole thesis, and its published *report* is itself a launch artifact and starts the clock on recalls' naming gate. If Opus finds posting-history reconstruction is impossible at retrocast grade, recalls resumes the #1 slot and layoffs launches observation-first with a forward-validation year.

### 6.3 Year-1 sequence (Q3 2026 → Q3 2027)

| When | What | Exit criteria |
|---|---|---|
| Q3 2026 | **Phase 2** (Opus, ~2–4 sessions): validate everything; **Phase 3** (Fable): gameplan + autonomy architecture | `02-RESEARCH.md`, `03-GAMEPLAN.md`, ops/ specs |
| Q3 2026, immediately post-Phase-3 | **Archival crons first** ("collect before you can compute"): posting snapshots, WARN, circulars, outage maps begin accumulating even before any index exists | perishable corpora flowing to storage at $0 marginal |
| Q4 2026 | **Phase 4 opens:** shared services core + E1 → **Shadow Layoffs retrocast** vs. 2022–2025 labels → publish retrocast report + live index + WARN Watch | retrocast published with P/R curve; first artifacts auto-posting; *first external citation is the year-1 finish line and could land here* |
| Q1 2027 | **Recalls retrocast published** (research-artifact launch + aggregate index live; naming-gate clock starts). **Legislative Authorship** ports E2 from OnScript, replicates the 2019 study, goes live for the Jan–Apr statehouse session. FOIA micro-index ships as the journalist gift. | two retrocast reports public; statehouse artifacts flowing in-session |
| Q2 2027 | **Grocery/Shrinkflation pilot**: 3 metros (operator's own + 2 diverse — operator metro TBD, Phase 2 errand), forward collection + Wayback retrocast in parallel | weekly per-metro artifact; CPI-divergence chart on release days |
| Q3 2027 | Consolidate: Track Record page v1 (every call scored), mortality backfill begins quietly (no publication), E5 groundwork for hospitals | the credibility flywheel visibly turning; year-2 flagships staged |

Year-1 definition of done: **two published retrocasts, three live indexes + one micro-index, artifacts self-posting on schedule, one external citation, total cash cost ≈ domains + a handful of gated backfill runs.**

---

## 7. The 5–10 year map

### Year 1 — *prove the method* (above).

### Years 2–3 — *the flywheel*
Portfolio: 5–8 indexes across ≥4 families (add Hospital Distress, Mortality, Insurability, Wages; Corporate Distress capstone late). Every index page carries the family track record; every artifact links the scorecard; every scorecard win makes the next citation cheaper — that's the flywheel, and it needs **no marginal operator effort** because artifacts and scorecards are compiled, not written. First "the Observatory flagged it first" news moment (statistically near-certain across 5+ indexes by year 3 — one hospital closure, layoff wave, or recall called early, receipts shown). First revenue: a grant (Phase 2 maps the funders) and/or memberships covering all cash costs. First methodology fight survived in public (this is a *milestone*, not a risk — the first hostile audit we answer well is worth ten friendly citations). Named-entity tiers begin unlocking behind their gates: recalls watchlist first.

### Year 5 — *the reflex check*
"Reflex check" operationalized: beat reporters in 2–3 verticals (consumer safety, labor/tech, statehouse) check the Observatory *before writing*, the way econ reporters check FRED. Embeds of Observatory charts appear in other people's stories (FRED-style embed is the growth vector — every embed is an ad we didn't buy). Indexes cited in at least one official proceeding (PUC intervention, CPSC comment docket, state hearing). The official layer responds somewhere — an agency accelerates a series or publishes its own nowcast in an Observatory-shaped hole; we claim the win loudly and retire nothing yet. Operations: fully autonomous steady state, operator at ~1 gate-hour/week; revenue (grants + memberships + format-tier feeds for newsrooms/attorneys/insurers) covers costs with margin; maybe first contractor-hours bought for corpus adapters.

### Year 10 — *institutional endgames and branch points*

The serious version of "what does it mean for this to outlive my involvement":

| Branch point | Options | My prior |
|---|---|---|
| **Legal vessel** (decide ~year 2–3, forced earlier by first grant — most funders require a vessel or fiscal sponsor) | LLC → 501(c)(3); fiscal sponsorship (cheap 501(c)(3) veneer, year 2-appropriate); stay personal (bad — liability) | fiscal sponsorship early, own 501(c)(3) when grant volume justifies |
| **Governance** (year 3–5) | solo-with-constitution → small board of methodologists/journalists → community | the constitution is already the governance seed: covenants + gates + public scorecards *are* bylaws-in-waiting |
| **Succession** (design now, cheap) | orphan protocol (constitution) → named successor operator → institutional home (university data center, press-freedom org, library consortium) | encode orphan protocol in Phase 3; court institutional homes passively from year 3 (they should come to us) |
| **Protocolization** (year 5+) | keep centralized; OR publish the retrocast-gate spec as an open standard others must meet to call their number "retrocast-certified" — the Observatory becomes reference implementation + certifier, not sole producer | protocolize — it's the only path that scales past one operator's corpus list, and certification authority is the deepest institutional moat there is |
| **Dataset-of-record** (year 5+) | Zenodo DOIs per index per vintage; university library mirrors; the corpus archives (circulars! outage maps! postings!) become primary sources historians use | do all of it — archival value accrues even if every index dies |
| **The victory condition** | official layer speeds up; indexes retire with plaques; the Observatory's residual role is watching the watchers' latency forever | the Retirement Plaques page is designed year 1, even while empty — it declares what winning means |

### Failure modes (named now so Phase 3 designs the defenses)

1. **Punditry drift** — the death of a thousand hot takes. Defense: "never predict, only measure" is constitutional; artifacts are compiled from numbers, no freeform editorial surface exists.
2. **Methodology rot / silent decay** (the Google Flu Trends death). Defense: permanent chaining to official numbers with public divergence flags; drift alarms are Phase 3 deliverables.
3. **Operator burnout / attention collapse.** Defense: the floor + orphan protocol; the system's degraded mode is *boring, not broken*.
4. **Platform rug-pulls** (a corpus dies, an endpoint closes). Defense: corpus redundancy per index where possible; archives mean death is graceful (index freezes with its history intact, plaque of a sadder kind); §4.5-style ecosystem citizenship makes some rug-pulls negotiable.
5. **Capture by revenue** (the feed customers start shaping the numbers). Defense: format-not-information doctrine; banned-category sponsorship; public free core is identity-level.
6. **The ShadowStats slide** (confirmation-audience capture — becoming beloved of one tribe). Defense: symmetry audits where politics-adjacent (inherited from OnScript); publishing numbers that annoy *every* constituency in turn is the tell of health.
7. **A lost defamation fight.** Defense: naming gate, signature framing, receipts, transparency log, LLC + insurance (Phase 2), and the observer-effect clause for the genuinely dangerous cases (banks).

---

## 8. Distribution architecture — engineered against the scar tissue

Prior products died of: built-it-nobody-came, zero organic, ads at 0% CTR. Root cause: no shareable unit and no reason for anyone with an audience to carry it. The Observatory's answer is structural, not promotional: **the artifact is the product, the citation is the distribution, the scorecard is the moat.** No ads, ever. No SEO-bait. Nothing that requires the operator to "do marketing."

**The artifact spec (per index, compiled automatically):**
- One chart (static SVG/PNG, brand-consistent, embeddable) + one declarative sentence (the measurement, no adjectives) + the receipts link + CSV/JSON of the underlying series. Alt text always (accessibility = quotability).
- Every artifact is **born local where possible** — per-metro, per-county, per-state variants compiled from the same run, because local news is the under-served, high-conversion citing class (a "your county" number gets picked up where a national number doesn't).
- Cadence artifacts (weekly/monthly pulse) + **anomaly artifacts** (threshold-crossing posts — inherently newsy; named-entity anomalies queue for the gate, aggregate anomalies auto-post).
- **Piggyback artifacts:** every official release day (CPI day, JOLTS day, recall announcements) auto-emits the divergence/lead chart — riding news cycles that already exist instead of manufacturing attention.

**Surfaces:**
- **The site:** per-index pages (number + chart + methodology + scorecard + receipts), per-place pages (the local front door), the **Track Record page** (the flagship — nobody shares a methodology PDF; everyone cites a scoreboard), the transparency log (legal threats, corrections, methodology versions). Static, fast, embeddable — FRED-envy is the explicit design target, down to the embed widget.
- **Feeds:** RSS/JSON per index, free, forever — journalists and tinkerers wire themselves to us and become distribution.
- **Bluesky:** proven pattern from OnScript (free API, bots welcome, self-labeled automation) — one flagship account + per-family accounts when volume justifies. X only via manual cross-post if ever (its API economics are dead for us — established by OnScript research).
- **The weekly digest** (email): one page, every index's sentence, gate-report adjacent; the operator's own 1-hour week starts from the same digest the public gets.
- **GitHub:** corpus archives + engine code public — developers and academics become distribution; Zenodo DOIs make citations *academically countable*.
- **The journalist gift program:** free named-beat alert feeds (recalls for consumer reporters, WARN for metro reporters, session scorecards for statehouse reporters) + a "for reporters" block on every number (error bars, methodology quote, contact). Cold-start answer: the first 50 journalists are hand-picked recipients of a personally useful free tool, not targets of a pitch.

**The credibility-compounding loop, explicitly:** artifact → citation → scorecard win → authority → cheaper next citation → (nothing in this loop requires operator hours) → repeat. Phase 3's job is to make every arrow in that loop a compiled, automated step with a drift alarm on it.

---

## 9. The sustainability model

### Cost curves (design targets under the spend covenant, Phase 2 validates)

| Stage | Compute posture | Cash/month |
|---|---|---|
| Archival-only (Q3 2026) | Actions cron + object storage in public repos/Releases (OnScript-proven pattern) | ~$0 |
| 1 engine + 1 index live | Actions + 4080 (local embeddings/classifiers, scheduled Code sessions) + static hosting | ~$0–10 + domains (~$30/yr) |
| 3 engines, 3–4 indexes | same + occasional gated Haiku-batch runs for semantic legs | ~$10–30, spikes gated per-run |
| 5 engines, 8+ indexes (year 2–3) | same + storage growth (circular/posting archives get big — **[P2]** cost the corpora honestly at real sizes; Releases/R2/B2 tiering) | target < $50 steady; backfills gated |
| The floor (constitutional) | $50/month + 1 hr/wk: everything keeps running degraded (monthly cadence, no backfills, archival never stops) | survives indefinitely |

Retrocast backfills are the spiky exception (a decade of reviews vs. recalls could be a $50–200 Haiku-batch run) — always a per-run operator gate with a cost estimate attached, per covenant 6. The 4080 earns its keep on embeddings, entity-resolution candidate generation, and classifier inference; scheduled Claude Code sessions (subscription) carry orchestration, verification, and the weekly compile.

### Revenue ladder (doctrine in constitution; sequencing here)

- **Year 1: $0 by design.** Credibility is pre-revenue capital; selling before the scorecard exists would spend trust we haven't earned.
- **Year 2: grants + memberships.** Civic-data philanthropy exists for exactly this shape (Knight, Sloan, RJI, Democracy Fund, Data & Society orbit — **[P2]** maps the real list, deadlines, and vessel requirements; most require a 501(c)(3) or fiscal sponsor → forcing function for the legal-vessel branch point). Memberships are the Guardian model: "keep the receipts public," no paywall ever.
- **Year 2–3: format-tier feeds.** Webhooks, bulk API, custom cuts, SLAs — sold to newsrooms, plaintiff firms, insurers, libraries. Same information, same moment, better plumbing. Hedge funds may buy the same tier anyone can; they get nothing exclusive, nothing early — the asymmetry-destruction mission *is* the product's integrity.
- **Year 3+: sponsorship, firewalled.** Named per-index sponsorship ("the [X] Foundation supports the Shadow Mortality Index") under published firewall + banned-category rules (no sponsor from a measured sector). Nothing from the obituary corpus is ever sold, full stop (covenant 3).
- **Never:** ads, exclusivity, early access, pay-to-influence-methodology, obituary-derived products.

Sustainability definition: **costs covered by year 3 with revenue that a hostile journalist could audit and admire.** The upside case (feeds + grants meaningfully exceeding costs) funds contractor corpus-adapters and the certification/protocol future — not lifestyle; the operator has a day job and said so.

---

## 10. Consolidated Phase 2 research agenda (the kill-list)

Everything above stands or falls on these. Per-index kill-questions are inline as **[P2]**; the load-bearing ones, consolidated:

1. **Posting-history reconstruction** (decides index #1): Wayback/aggregator/academic paths to 2022–2025 Greenhouse/Lever/Ashby history; ToS posture of each ATS on polling; coverage census (how many companies, what sector skew).
2. **Review-corpus access** (decides recalls' ceiling): legally durable paths to marketplace review text at scale; SaferProducts + NHTSA-only fallback design; entity-resolution feasibility rate on a 100-recall sample.
3. **Obituary corpus posture** (decides mortality): Legacy.com/funeral-home ToS vs. count-only polite scraping; coverage-bias literature; CDC WONDER retrocast data pull.
4. **Circular/price archive depth** (decides inflation retrocast vs. forward-only launch): Wayback coverage of circulars/Flipp/retailer pages 2020–2024; Flipp ToS; per-metro feasibility census.
5. **Model-bill corpus assembly** (decides leg-authorship cost): what's public from ALEC/SPN/ALICE; 2019 investigation dataset reusability; LegiScan/Open States free-tier ceilings at 50-state session scale.
6. **The boring-but-fatal trio:** storage costs at real corpus sizes; Actions minutes/artifact quotas at our cron density; rate-limit maps for every official API named in §4.
7. **Legal foundation:** LLC/fiscal-sponsorship options + media-liability insurance cost; defamation exposure analysis of the signature framing (opinion-based-on-disclosed-facts doctrine); CFAA/ToS posture per corpus under covenant 1; the bank observer-effect question (I-13).
8. **Prior-art sweeps** per flagship (who publishes what, how live, how public) — especially inflation (Instacart/Numerator/Adobe), drug safety, wages (Indeed/ADP), say-do.
9. **Grants landscape:** funders, cycles, vessel requirements, realistic award sizes for a working-prototype-with-retrocast applicant.
10. **Naming/domains:** availability sweep for "The Observatory" family (domains, Bluesky handles); collision check (existing "Observatory"-named data orgs); the operator's metro (ask him — one line, needed for the inflation pilot).

**Verdict format Opus must return:** per index — VIABLE / VIABLE-WITH-CHANGES (with the changes) / DEAD (with the evidence), plus re-scored §6 table, plus any *new* indexes the research surfaces (Phase 2 may add, not just kill — exhaust maps beget exhaust maps).

---

*End of Phase 1 corpus. The constitution lives in [OBSERVATORY.md](../OBSERVATORY.md). Opus: kill without sentiment. What survives you, we build for a decade.*
