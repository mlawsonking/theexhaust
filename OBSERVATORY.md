# OBSERVATORY.md — the constitution

*Every session of any model reads this file first and self-orients. If your session's model or task doesn't match the current phase, stop and say so.*

---

## Status

| | |
|---|---|
| **Current phase** | Phase 2 **COMPLETE** (2026-07-11) |
| **Next phase** | Phase 3 — Fable architecture session. Gate artifact: `docs/03-GAMEPLAN.md` + `ops/` specs |
| **Operator** | Michael King (mlawsonking@gmail.com) |
| **Working name** | **The Exhaust** (chosen Phase 2; `theexhaust.org`; "observatory" kept as a descriptor, e.g. "an observatory for shadow statistics"). Operator errand pending: registrar-confirm + WHOIS-private buy, USPTO TESS check, Bluesky handle via TXT DNS. Repo folder / this filename left as-is (cosmetic rename is a later task). |
| **Repo** | `C:\Users\bobdo\projects\observatory`, main box. No remote yet. |

**Handoff note (Phase 2 → Phase 3):** The full research is `docs/02-RESEARCH.md`; read its §0 first. The thesis, the five-engine architecture, and the retrocast/moat doctrine all survived — but three things changed: (1) **the "first published retrocast" moves off Shadow Layoffs** (no free posting history to backtest — vision §6.2's escape hatch fired); the first retrocast is **NHTSA Shadow Recalls**, with **Hospital/Care Distress** the cleanest second, and Layoffs launches observational-first + forward-validation. (2) **Several corpora are DEAD** (Legacy.com obituaries, GoFundMe, poweroutage.us, SERFF, Amazon/Glassdoor reviews) and **the covenants need amendment** — see §6 of the research doc (spend honesty `~$0–3/mo`; mandatory dead-man heartbeat for cron drift; tightened scraping-hygiene covenant; defamation-as-legal-doctrine; hardened bank observer-effect clause; a do-not-collect register). (3) The name changed to **The Exhaust**. Fable's job: reconcile vision + research into `03-GAMEPLAN.md`, fold in the §6 amendments, and spec the archival-cron fleet, the entity-resolver, the retrocast harness, the dead-man switches, and the orphan protocol. The gate is **archival-first**: every uncollected week is data lost forever (§10 sequence).

---

## Thesis (compressed)

Official statistics are slow, self-reported, and politically filtered — every official number is a press release about reality issued by the entity with the least incentive to issue it fast. Reality leaks constantly through public exhaust data (reviews, obituaries, job postings, circulars, filings, dockets, minutes, logs). Since ~2024, LLMs make semantic joins across corpora with no shared keys cheap. Nobody has built the public institution that reads the exhaust.

The Observatory is a permanent, automated, public observatory that ingests free exhaust streams and publishes **shadow statistics** — live, unofficial, receipts-attached versions of the numbers society currently waits for. The credibility engine is **retrocasting**: every index is validated by running history backwards, with precision/recall published openly. Never predict, only measure. Calibrated trust accumulating in public where it can't be faked IS the product. Victory is measured in lag removed from civilization's feedback loops; the endgame is being the reflex check for journalists the way Fed data is for economists — and forcing the official layer to speed up.

---

## The four phases

| Phase | Model | Job | Gate artifact |
|---|---|---|---|
| 1 — Ideation | Fable | Interrogate operator, full-scale ideation, constitution, repo skeleton | `docs/01-VISION.md` ✅ |
| 2 — Research | Opus | Validate every load-bearing assumption against reality; VIABLE/CHANGES/DEAD per index; cost model; legal map; prior art; grants landscape | `docs/02-RESEARCH.md` |
| 3 — Architecture | Fable | Reconcile vision with research; workbook compiler; scheduling architecture; permission map; dead-man switches; operator interface (~1 hr/wk) | `docs/03-GAMEPLAN.md` + `ops/` specs |
| 4 — Implementation | Opus | Build exactly what Phase 3 specifies, starting with the first index's retrocast. Verified against live sources. "Should work" is not done. | `docs/04-BUILDLOG.md` + working pipelines |

Phase gates are file-existence checks. Phases 1–3 produce documents and specs only — **no implementation code before Phase 4.**

---

## Operator covenants (Michael's answers, 2026-07-10 — binding on all phases)

1. **Scraping posture:** official APIs and licensed bulk data, plus polite scraping of public pages (rate-limited, cached, robots.txt-respected, nothing behind auth or CAPTCHA). Aggressive within legal boundaries and ethical good taste. This is a public good; annoyance to the exposed is acceptable; malice is not.
2. **Naming gate:** aggregate-only indexes first. Named-entity signature claims ("X matches the pre-recall signature of N historical cases at similarity Y") unlock **only after** that index's retrocast track record is published, a fixed editorial rubric exists, and the operator explicitly signs off. Named claims are always signature-framed measurements with receipts, never predictions. Exception: **observational facts with receipts** (e.g., "Company X removed 78% of its engineering postings in 3 weeks," with the diffs) are publishable day one — they are reporting, not signature inference.
3. **Obituary ethics (binding, identity-level):** the mortality corpus is IN, with constraints — no names or obituary text ever republished; aggregate counts only; county-month granularity floor; nothing derived from the obituary corpus is ever sold; ethically decent to the grieving, always.
4. **Legal-threat posture:** do not design into a crouch. When a cease-and-desist arrives against receipts-attached public-interest measurement, the reflex is to respond publicly — every legal threat is published in a site transparency log. (Fight-publicly ≠ recklessness: valid legal process is honored and counsel consulted; Phase 2 researches an LLC + media-liability insurance as the operator's shield.)
5. **Identity:** institutional brand front-and-center; Michael's real name on the About/methodology page. Voice decisions delegated: methodology pages are written as the canonical interview; press contact is an Observatory address, not personal; operator quotable on the record at his discretion only for indexes with a published retrocast; all legal threats published; WHOIS privacy on domains.
6. **Spend:** steady state runs on subscription Claude Code sessions + local RTX 4080 + free compute (GitHub Actions public repos, static hosting). **Metered API spend is gated per-run by the operator — never ambient.** Design every steady-state pipeline to run at ~$0 marginal cash cost.
7. **Time:** ~10 hrs/wk across 3–4 concurrent projects; the Observatory gets a few, more as it earns importance. Autonomous-by-default with decision gates; the system must tolerate zero-touch weeks without dying. Steady-state operator target: ~1 hr/wk of judgment, not labor.
8. **Revenue doctrine (delegated, decided):** public free access to every published number is identity-level and non-negotiable. Ladder: grants/philanthropy and memberships first; then professional conveniences (webhook alerts, bulk API, custom cuts) sold as **format-not-information** — no exclusivity, no early access, nobody (including hedge funds) gets anything the public doesn't get at the same moment; per-index sponsorship only with a published firewall policy and banned-category rules (no sponsor from a sector its index measures). **No ads, ever** (operator's prior products proved ads convert at zero and the incentive rot isn't worth it).
9. **Geography:** US-only through ~year 3; architecture must not preclude international later.
10. **Portfolio preference:** operator personally wants shadow layoffs / corporate behind-the-scenes most, but directs: highest immediate public benefit and ROI wins the ranking.

## Standing doctrine

- **The retrocast gate.** No index publishes without: (1) a historical backtest against named ground truth, (2) published precision/recall and calibration, (3) a frozen versioned methodology doc, (4) a receipts link on every number. Methodology changes republish the full backtest under the new version.
- **Replicate, then run.** Where a celebrated one-off study exists (USA Today copy-paste legislation, Billion Prices Project, academic obituary excess-mortality), an index launches by reproducing the known result, then keeps it running forever. Reproduction is both validation and press hook.
- **Collect before you can compute.** Perishable corpora (circulars, outage maps, job postings, death notices) are archived from day one — archival crons precede index launches, because every uncollected week is data lost forever.
- **Never predict, only measure.** "Matches the pre-X signature of N historical cases at similarity Y," never "will be X'd." The site never editorializes beyond the measurement.
- **The anti-ShadowStats clause.** shadowstats.com is the cautionary tale: opaque, unfalsifiable, crank-adjacent "alternative statistics." The Observatory is its methodological opposite — open methods, open receipts, open scorecard — and never publishes a number whose derivation a critic can't rerun.
- **The Google-Flu-Trends clause.** Correlation mining without ground-truth discipline decays silently. Every index is permanently chained to its official number as it arrives; divergence beyond calibration bands triggers an automatic flag on the index's own page. The Observatory grades itself in public before anyone else can.
- **Retirement plaques.** If an official number gets fast enough that an index is redundant, the index retires with a public plaque: lag removed, mission accomplished. Forced obsolescence is the victory condition, not a loss.
- **The floor.** The system must survive on $50/month and one operator-hour a week: free compute, subscription sessions, no backfills, monthly cadence — everything keeps running, nothing rots. Phase 3 encodes this as a tested degraded mode, including an **orphan protocol** (gates unattended N weeks → freeze new publications, keep validated pipelines and archival crons running, post a status banner).

---

## Session log

- **2026-07-10 — Phase 1 (Fable).** Operator interrogated (10 covenants above). Constitution, repo skeleton, `docs/01-VISION.md` written: ~30-index universe in 6 families powered by 5 shared engines, 15-join map, ranked portfolio (recommendation: Shadow Layoffs first — argued over the operator's recalls prior; recalls retrocast runs in parallel), 10-year map, distribution architecture built around the operator's zero-organic scar tissue, sustainability model. Git initialized, committed. **Next session: Phase 2, Opus.**
- **2026-07-11 — Phase 2 (Opus, ultracode).** Ran a 15-probe multi-agent research fan-out against live 2026 sources with adversarial verification on the 6 load-bearing questions; wrote `docs/02-RESEARCH.md`. Key results: thesis/engines/moat survive; **first retrocast moves off Layoffs → NHTSA Recalls** (no free posting history; §6.2 conditional fired), Layoffs launches observational + forward-validates; **Hospital/Care Distress** is the cleanest immediate retrocast (PBJ staffing → CMS harm deficiency, hard CCN key). **Kills:** GoFundMe/Medical-Debt (ToS+ethics), full-basket inflation retrocast (SPAs), J-14 poverty-timed-pricing (published null result), Amazon reviews (closed). **Re-scoped on access:** Mortality (Legacy ToS + CDC county-month suppression), Insurability (SERFF clickwrap wall), Utility (poweroutage.us ToS), Workplace-review→Reddit-forums. **Link-don't-compete:** Wages (ADP/Indeed), Small-biz (Census BFS). **New white space:** 311 cross-city inequality, Say-Do (Represent died 2024), Insurability. Infra GREEN (`~$0–3/mo`; cron drift needs a dead-man heartbeat). Legal GREEN with constitutional guardrails; funding GREEN (RJI fellowship anchor). Portfolio re-scored (§4.2). Operator decisions: **name → The Exhaust**; **metro → San Antonio (use Dallas–FW as BLS anchor)**. Covenant amendments listed in research §6 for Phase 3 to fold in. Then, at the operator's request, ran a **deeper prior-art pass** (2nd workflow, 24 agents, 132 entities, adversarially verified) on the 3 medium-confidence white-space claims → all **CONTESTED, none occupied** (nothing dropped): 311 has a live fast-follower (`balt311-service-equity`), Insurability has static national maps + a 2027 NAIC anchor, and Say-Do has a **live competitor (CivicAlign)** so the "clean hole" framing is dropped — but the retrocast-scorecard wedge is unoccupied in all three. Written up as research **§13**; no open prior-art questions remain for Phase 3. **Next session: Phase 3, Fable.**
