# 04-BUILDLOG — The Exhaust, Phase 4 implementation

*Opus, opened 2026-07-11. Predecessors: [`01-VISION`](01-VISION.md) · [`02-RESEARCH`](02-RESEARCH.md) · [`03-GAMEPLAN`](03-GAMEPLAN.md). Contracts: [`ops/SPEC-01…09`](../ops/).*

The multi-session build log (OnScript pattern). Standing orders (gameplan §0): **build exactly what the specs say · archival first · re-verify before you depend · the covenants are code review**. One BUILD item at a time, to acceptance, verified, committed, logged here.

---

## BUILD status

| Item | Scope | Status |
|---|---|---|
| **BUILD-00** | Foundations (repo, state layer, R2, healthchecks, ntfy, secrets) | **Opus scaffolding DONE; acceptance BLOCKED on operator errands ⚑ — tracked in Vikunja (board `observatory`, #9–#13)** |
| BUILD-01 | Archival fleet v1 (collectors → R2) | **in progress** — C1 + C5 + C4-recalls + C9 + **C3 ats-boards (E1 engine)** live-verified; nhtsa-complaints HEAD-verified (367 MB → Actions); C2/C6/C8/C10/C11 next; R2 deploy + fleet-green pending BUILD-00 |
| BUILD-02 | Ops core (state, alarms, gates, budget, gate-report, weekly session) | **built & tested** — gates + budget + orphan + report + **alarm/ntfy bus** + **weekly-ops driver** + playbooks (17 tests); live ntfy/heartbeat delivery inert until BUILD-00 topics exist |
| BUILD-03 | Retrocast harness + NHTSA retrocast (⚑ LLC + insurance gate) | **pre-registration FROZEN** + **harness code built & tested** (`retrocast/harness.py`; synthetic: dumb-baseline beaten, planted-leak caught, scorecard validates); NHTSA run pending C4 archive + LLC/insurance gate |
| BUILD-04 | Public launch (site, WARN Watch, posting-diffs, Bluesky) | **in progress** — static-site generator built & tested (home / Track Record / Retrocasts / Methodology / Transparency; theme-aware; renders scorecards + pre-registrations); WARN Watch + posting-diffs + Bluesky + Cloudflare Pages deploy remain |
| BUILD-05 | Hospital/Care retrocast | queued |
| BUILD-06 | Workbook compiler v1 | queued |
| BUILD-07 | Legislative Authorship + FOIA micro (Q1 2027, session-timed) | queued |
| BUILD-08 | Grocery forward pilot + shrinkflation retrocast (Q2 2027) | queued |
| BUILD-09 | Say-Do pilot (Q2 2027) | queued |
| BUILD-10 | Track Record page, bank aggregate, first 311 city, mortality groundwork (Q3 2027) | queued |

## Standing follow-ups for Opus sessions

> **Superseded 2026-07-17:** the live queue is now [`ops/state/WORKPLAN.md`](../ops/state/WORKPLAN.md) (single source; the items below are folded in as W-003 and the acceptance rule). Worker sessions take their orders from [`ops/state/NEXT.md`](../ops/state/NEXT.md) under [`ops/BUILD-PROTOCOL.md`](../ops/BUILD-PROTOCOL.md).

- **Wire the futility clause (constitution, 2026-07-13) into the machinery:** the report compiler auto-files the 2027-12-31 project-kill gate from `CALENDAR.md` (gate template + a date check in `opscore/weekly.py`), and launched indexes get the 12-month zero-traction retire-or-rescope auto-gate once indexes exist. Small, offline-testable.
- **Adversarial review before BUILD-item acceptance** is now a constitutional standing rule — run one per BUILD item before marking it accepted (the BUILD-02 pass caught 9 defects, 2 severe).

## Environment (dev box, verified 2026-07-11)

- Python **3.13.13**, Windows 11 main box; miniconda at `C:\ProgramData\miniconda3\python.exe`. `requests` ✅, `zstandard` ✅ (for `.zst` per SPEC-01), `boto3` ❌ (add for the R2 backend at BUILD-01), `urllib3` ✅.
- Git: local repo, **no remote yet** (operator errand). Collectors target R1 (Actions Ubuntu) + R2 (this box); keep them portable.

---

## Session log

### Session 1 — 2026-07-11 (Opus) · BUILD-00 scaffolding

**Bootstrap & verify.** Confirmed the Phase 3 gate: `docs/03-GAMEPLAN.md` + `ops/SPEC-01…09` exist; `6f40d5b` is HEAD, clean tree; the constitution's covenant amendments are enacted. Phase/model check: Phase 4 = Opus = this session. Read the constitution, the gameplan (§0 standing orders, §6 BUILD queue), and the ops-core contracts SPEC-01…06.

**Re-verify before depend (standing order) — C1 sources, live 2026-07-11:**
- CMS Health Deficiencies datastore `r5ix-sfxw` → HTTP 200, **418,479 rows**, 23 fields incl. `cms_certification_number_ccn`, `survey_date`, `survey_type`, `deficiency_tag_number`, `deficiency_category` — matches research §5 exactly (the hard-CCN key + survey date + harm-tier fields are present).
- CMS PBJ provider-data metastore → HTTP 200, live. (Exact PBJ dataset id pinned when C1 is built.)
- Verdict: C1's ground-truth side is re-confirmed; no drift from spec. `verified` date refreshed to 2026-07-11.

**Built (BUILD-00 Opus portion):**
- Opened this build log.
- Repo hygiene: `README.md` renamed to **The Exhaust**; `.gitignore` extended (Python caches, local secrets/env, local archive scratch); `requirements.txt` added (`requests`, `zstandard`, `boto3`).
- **State layer** per SPEC-03/04/05/06: `ops/state/HEALTH.json`, `ops/state/BUDGET.json`, `ops/state/CALENDAR.md`, `ops/state/ACK` (orphan-clock marker), `ops/state/QUEUE/{pending,decided}/`, `ops/state/README.md`; plus `ops/reports/` and `ops/playbooks/` scaffolds.
- **CI foundations guardrail** (SPEC-04 §5 seed): `ci/do_not_collect.txt` (the constitution's register) + `ci/covenant_guard.py` — fails CI if any collector references a do-not-collect source or if any R1 workflow references an Anthropic key. Verified locally: passes (collectors dir empty; no key in workflows).
- **R1 hello-world + guard workflow** `.github/workflows/ci.yml` (standard runner only; runs the covenant guard + a liveness echo). Runs green once the repo is pushed.
- `collectors/README.md` — the SPEC-01 collector contract, statuses, and the do-not-collect enforcement note (framework + collectors built at BUILD-01 against real R2).

**BLOCKED — BUILD-00 acceptance needs the operator errands ⚑** (see the handoff below): buy `theexhaust.org`; create public GitHub repo `theexhaust` + push; Cloudflare (R2 bucket `exhaust-archive` + custom domain; Pages); healthchecks.io + ntfy topics (unguessable); Actions secrets. Acceptance criteria (Action green, R2 read/write via custom domain, ntfy on phone) can only pass after those exist. **These five errands are the ledger-of-record in the Vikunja task bus** (board `observatory`, tasks #9–#13, filed 2026-07-13) — this doc no longer tracks them as a to-do; `vtask list` is the live status.

**Why the fleet wasn't built this session:** BUILD-01's acceptance (7 green days, restore drill from R2 via the custom domain) is 100% gated on the above infra, and `boto3`/R2 aren't in place — building collectors against a throwaway local backend would be unverifiable rework that violates "verify against live sources/infra." The perishable-data clock is bounded by the ~30-min operator errand turnaround, not by collector code (durable storage needs R2 regardless). C1's live sources are already re-verified, so no design risk remains. **Next session builds the fleet end-to-end against real R2 and drives it to the 7-green-day acceptance.**

**Next:** operator completes BUILD-00 errands → Session 2 builds BUILD-01 (collector framework + storage abstraction with the R2 backend + collectors C1→C6/C8→C11, C7 dark) verified against live sources and R2.

### Session 2 — 2026-07-13 (Opus) · BUILD-01 construction (meantime, account-independent)

While BUILD-00 operator errands are pending, built and **live-verified** the BUILD-01 collector framework + first collector — archival-first is the top standing order, and *construction* needs no operator infra (only *deployment* does).

**Built:**
- `collectors/framework.py` — runtime-agnostic: `StorageBackend` (`LocalFSBackend` now + lazy `R2Backend`), `CsvSchema` (drift vs. anomaly), `Collector` (fetch → hash → dedupe → validate → `.zst` → store immutable raw + per-day manifest → HEALTH → heartbeat; quarantine + alarm on drift). SPEC-01 storage layout exactly.
- `collectors/cms_deficiencies.py` — C1 ground-truth side (CMS Health Deficiencies `r5ix-sfxw`); resolves the vintage CSV URL from the CMS metastore each run (CMS overwrites), display-name schema contract on CCN / Survey Date / Deficiency Tag / Scope Severity.
- `collectors/run.py` — CLI; picks the R2 backend from env when secrets exist, else LocalFS; heartbeat from env; exits nonzero on alarm (SPEC-02 job contract).
- `collectors/tests/test_framework.py` — offline: store→dedupe, schema-drift→quarantine. Both pass; wired into `ci.yml`.

**Re-verified live (2026-07-13):** C1 bulk CSV `NH_HealthCitations_Jun2026.csv` → 200, 165 MB, 23 display-name cols (all 8 required present).

**Verified end-to-end (live, 3 MB read-cap):** run 1 → `stored` (7,546 sample rows; zstd 3,000,000 → 94,935 = **~31.6×**; SPEC-01 path; manifest with full sha256 + source_url + git_ref); run 2 → `unchanged` (content-hash dedupe). `anomaly:true` is the read-cap artifact (7.5k < 100k floor); production full-fetch is ~418k rows. ~31.6× compression ⇒ ~5 MB/vintage ⇒ ~$0 storage — consistent with the covenant.

**Pending (blocked on BUILD-00 infra, not on construction):** swap `LocalFS`→`R2` backend + verify the S3 round-trip (needs operator R2 creds + `boto3`); the fleet-green 7-day acceptance runs in Actions once the repo is pushed; full-corpus fetch (no cap) is the same code path.

**Next meantime grind:** C4 `nhtsa-complaints` + C5 `cpsc-recalls` (the NHTSA-retrocast signal sources), then C8/C9/C10/C11; then draft the NHTSA retrocast pre-registration (SPEC-08, required before results).

**Session 2 continued —** did C5 + the NHTSA pre-registration:
- **C5 `cpsc-recalls`** (`collectors/cpsc_recalls.py`, registered in `run.py`): fixed-URL CPSC recall listing CSV, provenance schema (Importers/Manufacturers/Distributors/"Manufactured In"). **Verified live end-to-end (FULL 18 MB, no cap):** run 1 → stored, **9,932 recalls**, raw 17,990,689 → 3,247,624 (~5.5×), no anomaly, correct path + manifest; run 2 → unchanged (dedupe). Covenant guard still green.
- **NHTSA retrocast — pre-registration FROZEN before any result** (SPEC-08 §2): `retrocast/README.md` (harness layout), `retrocast/nhtsa-recalls/PRE-REGISTRATION-v1.md` (signal spec, labels, matched controls, train≤2020/test 2021-25 split with 5 explicit leak controls, mandatory dumb-baseline, pre-registered pass bars: PR-AUC ≥ volume-only+0.05, precision ≥0.30 @ recall ≥0.50, median lead-time ≥60d, calibration band), `retrocast/nhtsa-recalls/prior-art-scan.md` (fresh 2026-07-13 sweep: method established = replicate-then-run; live-public falsifiable scorecard unoccupied), `retrocast/DEAD-REGISTRATIONS.md` (autopsy log, empty per SPEC-08 §7). Committing this **before** results is the unforgeable git-ordering that is the field-wide differentiator. C4 (NHTSA flat files — 367 MB zip, pipe-delimited; needs a DelimitedSchema + zip handling) is the next collector; its bulk vintage is the retrocast-of-record the harness will run against.

**Session 2 continued — BUILD-02 ops-core (pure logic, offline-verified):** the autonomous-machine brain, built as `opscore/` (no accounts needed; external I/O behind interfaces, inert until BUILD-00):
- `opscore/gates.py` — gate-file parse/validate/serialize (SPEC-04 §3); `new_gate`, `load_pending`, `sweep` (decided → `decided/{YYYY}/`; expired-undecided → `expired-no-action`). Hard invariant enforced + tested: **nothing ever executes by expiry**, and `default_on_expiry` must be a safe option.
- `opscore/budget.py` — `GatedRun` token accountant that **aborts in code at the hard cap** (Haiku-batch rates), ledger append, R2 storage projection ($0.015/GB past 10 GB free) + >$5/mo alarm (SPEC-04 §4).
- `opscore/orphan.py` — the orphan clock (active/warn@3wk/orphan@4wk) from ACK + gate-decision dates; no-signal → treated as orphaned (safe) (SPEC-06 §1).
- `opscore/report.py` — the weekly gate-report compiler (SPEC-05): fixed shape, decisions-as-headline, priority-ordered, 150-line cap; compiles a real report from repo state (`ops/reports/2026/W29.md`).
- `opscore/tests/test_opscore.py` — **11 tests pass** (gate round-trip/decide/sweep/expiry-never-executes/unsafe-default-rejected/priority; budget cap-abort/storage-math/ledger; orphan states+reset+report-line; report nothing-needed + decisions-headline+order). Wired into `ci.yml`.
- **Pending (need BUILD-00 ntfy/healthchecks for live delivery):** the ntfy alarm sender + alarm-budget counter, the weekly/monthly R2 session playbooks (SPEC-02 §2), and live drift→alarm wiring. The *logic* is done; only the outbound I/O is stubbed.

**Adversarial review** (workflow: 4 independent reviewers — spec-compliance / correctness / covenant-safety / test-adequacy → synthesis). 18 raw findings → **9 confirmed** (deduped), **3 dismissed** with sound reasoning (health-board completeness = BUILD-02 follow-up not a defect; `http_get` SSRF needs a compromised .gov + self-rated low-confidence; `overrun_alarms` has zero callers). **All 9 fixed + locked with tests** (now 4 framework + 14 opscore + guard tests, all green):
- **HIGH** — `report.compile_from_repo` ignored gate DECISIONs (drove the orphan clock from ACK alone → could falsely freeze a present operator who decides gates but never touches ACK). Fixed: `_decision_dates()` gathers decided/deferred gate mtimes and feeds the clock.
- **HIGH** — `gates.is_decided` treated spec-valid `defer <date>` and free-text notes as terminal → gates swept out of pending forever. Fixed: terminal-verb vocabulary only; `defer` is non-terminal (stays pending, hidden until the date, re-surfaces after); free text stays pending.
- **MEDIUM** — collector schema-drift had no streak/pause/dedupe → unbounded alarm storm on a permanently-drifted source. Fixed: `drift_streak` + auto-pause at 3 + `needs_gate` flag + same-drifted-payload dedupe (no re-alarm).
- **MEDIUM** — volume anomalies were computed but never manifest-flagged or alarmed (a 10× snapshot stored at exit 0). Fixed: `extreme` tier (<0.25×/>5× median) → `alarm=True` (nonzero exit) + `volume_band` in the manifest.
- **LOW ×5** — orphan clock accepted future-dated signals (fail-safe defeat) → filtered to `≤ today`; R1 key guard matched only the literal `ANTHROPIC_API_KEY` → broadened to any `ANTHROPIC_*` / `CLAUDE_*KEY/TOKEN`; calendar parser dropped multi-date lines → iterates all tokens; the 150-line truncation could cut the orphan safety line → orphan section now always appended after truncation; the do-not-collect guard would false-fail a SPEC-01-sanctioned Wayback ALEC reference → Wayback allowance added. Each has a regression test.

**Session 2 continued — BUILD-03 retrocast harness code (the credibility engine, offline-verified):** `retrocast/harness.py` — generic and data-shape-agnostic (every index feeds `(entity, t, score)` + `(entity, event_t)`): `label_cells` (positive = event strictly in `(t, t+H]`), full `pr_curve`/`pr_auc`, event-level recall + `operating_threshold_event` (op point chosen on TRAIN only — the leak control), `lead_time_days` + Wilson CIs + `calibration_deciles`, the `leakage_scan` guard, `evaluate` (train/test split, dumb-baseline comparison, pass/fail vs pre-registered bars), and `scorecard`/`write_scorecard` (the Track Record page renders only from these). **A build-time modeling fix:** an 8-week-lead signal can't hit high *cell* recall over a 26-week horizon, so recall is graded at the **event level** (fraction of events led), not cell level. `retrocast/tests/test_harness.py` (4 tests, wired into `ci.yml`) verifies the SPEC-08 §7 acceptance on synthetic data: a genuine signature **passes and beats the dumb baseline** (PR-AUC 0.737 vs 0.071, 56-day median lead), a **planted leak** (fires only at the event → lead ≤ 0) is **caught and blocked**, impossible bars fail, and the scorecard validates. The harness is generic and ready to run against the archived NHTSA vintages the moment C4 lands (BUILD-03's data dependency).

**Session 2 continued — BUILD-02 closed out (alarm bus + weekly driver + playbooks):**
- `opscore/alarms.py` — the ntfy bus (SPEC-03 §3): `NtfySender` interface with `HttpNtfySender` (POST `ntfy.sh/<topic>`, inert if the topic is unset, never crashes the caller) and `NullNtfySender`; `AlarmBus.alarm/gate/pulse` route to the three topics, append to an alarm ledger, and enforce the **alarm budget** (>5 events/week × 2 weeks → gate item, SPEC-03 §4). Topics come from env (secrets); with none set the bus is silently inert.
- `opscore/weekly.py` — the deterministic weekly-ops driver (SPEC-02 §2): sweep decided/expired gates, **file a source gate for any collector auto-paused on drift-3x** (wiring the collector→gate flow the review flagged, de-duped by logical slug — also fixed `gates.parse` to return the logical slug not the filename), compile the report, alarm-budget check, pulse. CLI: `python -m opscore.weekly`.
- `ops/playbooks/weekly-ops.md` + `monthly-audit.md` — the R2 session scripts wrapping the driver with the bounded judgment steps (triage, rotating spot-verify, ToS re-verify) under the session contract; execute only operator-decided approvals, never anything gate-shaped.
- Tests: +3 (alarm routing/budget, inert-without-topics, weekly run files-then-doesn't-double-file) → **17 opscore tests**. What remains for BUILD-02 is purely the live outbound I/O (ntfy topics + healthchecks URLs), which is a BUILD-00 operator errand — the logic is done and tested.

**Session 2 continued — C4 NHTSA (the first-retrocast corpus):** `collectors/nhtsa.py` — two collectors from one source. **Re-verify-before-depend caught two spec errors:** the flat files are **TAB-delimited (not pipe)**, and the recalls file is `FLAT_RCL_POST_2010.zip` (the pre-registration's assumed `FLAT_RCL.zip` 404s) — both corrected. Added `ZipTabSchema` (unzip → validate the primary `.txt` member's TAB field count vs. the documented layout: recalls 29 fields, complaints 51) and a `recompress=False` path (zips are already compressed → store the raw ZIP immutably). **`nhtsa-recalls` live-verified end-to-end (full 14.7 MB download): 242,659 recall campaigns, 29-field schema validated, raw zip stored byte-identical + manifest.** `nhtsa-complaints` (367 MB, 51 fields) shares the identical path and is HEAD-verified (200); its full pull defers to Actions. Framework test `test_ziptab_schema_and_zip_collector` proves the zip path offline. This makes the recalls **ground truth** collectible; the NHTSA retrocast now needs only the archived complaints vintage to run through the (already-built) harness.

**Session 2 continued — C9 FDIC (Bank Stress ground truth):** added a reusable `JsonSchema` (record-list at a top-level key, required-key check on the sampled record, envelope-unwrap) and `collectors/fdic.py` (`fdic-failures`). **Live-verified end-to-end: 4,115 failed banks, JSON schema validated (RESDATE/COST/PSTALP/CLOSCD), raw 2.4 MB → 241 KB (~10×), manifest.** The failed-bank list is the named ground truth for the (permanently aggregate-only) Bank Stress retrocast; call-report *quarterlies* (the drift signal) are a later expansion. Framework now has **3 schema types** (CSV / ZIP-tab / JSON) and **6 tests**; the fleet spans 6 collectors.

**Session 2 continued — BUILD-04 static-site generator (the public face):** `sitegen/` (named to avoid shadowing Python's `site` builtin) — stdlib-only, theme-aware, self-contained (no external asset refs), emits 5 pages to `site/dist/` (git-ignored, rebuilt by the Cloudflare Pages build): **Home**, **Track Record** (renders *only* from scorecard JSONs — SPEC-08 §3; currently "no scorecards yet, here's our first pre-registration"), **Retrocasts** (auto-discovers + renders the frozen pre-registrations — the "method committed before results" story), **Methodology** (retrocast gate, never-predict-only-measure, anti-ShadowStats, Michael's name), **Transparency** (corrections + legal-threat log scaffold). Stale-data banner supported. `sitegen/tests/test_site.py` (2 tests, in `ci.yml`) builds against the real repo and asserts structure + that the NHTSA pre-registration renders; verified visually in-browser (a11y tree). Fixed the Phase-1 `site/README` (said Vercel; the covenant host is Cloudflare Pages). This makes the whole project publishable the moment the retrocast lands and Cloudflare exists — launch becomes one step.

**Session 2 continued — E1 Posting-Diff engine + C3 ats-boards (the layoffs distribution flagship):** the first shared engine (`engines/`), powering the operator's favorite index. Re-verified all 4 ATS shapes live (Greenhouse 516 / Lever 388 / Ashby 127 / SmartRecruiters envelope). `engines/ats.py` normalizes each vendor's JSON to a common Posting record; `engines/posting_diff.py` computes the **observational artifact** — what a board pulled/added between two snapshots, with the moved postings as receipts and a born-shareable headline ("Company X removed N of M postings (P%)…"). Publishable day one as *reporting* under the naming-gate carve-out — no signature inference, no prediction. `collectors/ats_boards.py` is the fleet archiver (per-board content-hash dedupe, one shared `ats-boards` heartbeat with per-board HEALTH detail, quarantine on parse failure) over a seed board universe (`seed_boards.json`; expansion to ~3–5k boards is a gate item). **Live-verified end-to-end: the fleet archived 3 seed boards (Stripe/Lever/Ramp) immutably.** 4 engine tests (normalize all vendors, diff+receipts, headline, fleet archive+dedupe), in `ci.yml`. Hardened `covenant_guard` to also scan `engines/` (any code that fetches sources). This is the corpus for Shadow Layoffs' WARN-Watch-adjacent observational launch — its retrocast forward-validates (no free posting history), but the posting-diff *reporting* ships day one.

**Session 2 continued — SPEC-09 entity resolver + receipts store (the deep moat):** `resolver/` — the semantic-join moat and the immutable number→exhaust trail. Tiered resolution (`resolve.py`): **T0** hard keys (CIK/ticker exact), **T1** deterministic crosswalk (exact normalized legal name; same-CIK share classes collapse to one entity), **T2** normalized-name token-Jaccard with a conservative auto-accept band + margin and an **ambiguity band that queues rather than guesses** (T3 LLM adjudication is gated, never auto-invoked). `crosswalks.py` loads the free SEC `company_tickers.json` (CIK↔ticker↔name; GLEIF/Census/HUD slot behind the same interface). `ledger.py` — the append-only resolution ledger (a pair is never re-adjudicated at cost). `receipts.py` — the **fail-closed** evidence bundle: an un-receipted number physically cannot render (the compiler refuses; corrections create successor bundles, never mutations). **Live-verified against the real 9,304-company SEC crosswalk:** AAPL→T0, Apple/NVIDIA/Block→T1, Alphabet/JPMorgan(9 classes)/Ford→T1 (share-class collapse), genuine name collisions + typo-band→queue. 4 tests (tiers, ledger cache, fail-closed receipts, normalize), in `ci.yml`; guard extended to scan `resolver/`. Local-embedding T2 enhancement (4080) and GLEIF/Census crosswalks are noted follow-ups.

---

## 2026-07-27 — W-000 · BUILD-00 acceptance gatecheck (WORKER) → **BLOCKED (precise stop)**

First build-grind WORKER session under the two-session contract. Read-list only (`OBSERVATORY.md` status/covenants, `docs/03-GAMEPLAN.md` §6 BUILD-00, `ops/SPEC-02` §1, `WORKPLAN.md` W-000/W-001, `NEXT.md`). Model check OK (Opus 4.8 = Phase-4 implementation class). Mission: **verify** the five operator BUILD-00 errands (Vikunja `observatory` #9–#13) actually completed before the next session builds on real infra. **Wire nothing.** Verdict: **none are complete; the foundation does not yet exist.** This is a §3-step-4 STOP condition — a precise stop is a successful session. **Nothing wired, no workaround, did NOT proceed to W-001.** Evidence per check (all read-only probes):

1. **Git remote `theexhaust` + push + green `ci` Action — FAIL (#9 incomplete).** `git remote -v` is **empty**; `main` has no upstream. `gh repo view theexhaust` → *"Could not resolve to a Repository with the name 'mlawsonking/theexhaust'"* — the public GitHub repo **does not exist**. Therefore no push has occurred and the `ci` workflow has **never run on GitHub** (it exists locally at `.github/workflows/ci.yml`, and the suite it runs is green locally — see below — but "green on GitHub" is unverifiable until the repo exists). `gh` itself is authed fine (account `mlawsonking`).
2. **R2 Actions secrets present + boto3 round-trip — FAIL (#10 + #13 incomplete/unverifiable).** All four SPEC-02 env-contract creds **unset** locally (`R2_BUCKET`, `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`). No `.env`/secrets file in the repo. Actions-secret presence is **unverifiable** — the repo (#9) doesn't exist to hold secrets. `boto3` is declared in `requirements.txt` (`boto3>=1.34`, already present — the "add to requirements" note is satisfied) but **not installed** in the miniconda base env; with no creds and no bucket a live list/put/get round-trip is impossible. Not attempted (would be wiring).
3. **Custom domain serves a test object over HTTPS — FAIL/untestable (#10 incomplete).** No bucket, no custom domain, no creds → nothing to fetch. Untestable until #10 lands.
4. **ntfy — three topics accept a test publish — UNVERIFIABLE (#12 unconfirmed).** Topic names are unguessable by design (SPEC-03) and are **not present anywhere** available to this session: not in env, not in any repo config (`grep` for `ntfy`/topic names hits only spec-doc references, not real topics). With no topic names I cannot send a test publish, and there is no operator phone-receipt confirmation on record. Per the item's rule, **unconfirmed ≠ passed** — reported plainly as not passed.
5. **healthchecks.io project + one test check pinged — UNVERIFIABLE (#11 unconfirmed).** No `HEALTHCHECK_URL`/`HC_PING_URL` (or any ping URL) in env or repo config. No evidence a project or check exists.

**Full §5 suite re-run before this doc-only commit — all green** (miniconda base `python 3.13.13`; the Windows `python`/`py` PATH resolves only to the MS-Store shim — real interpreter is `C:\ProgramData\miniconda3\python.exe`, recorded here for the next worker): covenant_guard OK · covenant_guard tests PASS · framework 6/6 · opscore 17/17 · retrocast 4/4 (pr_auc 0.737 vs baseline 0.071) · sitegen 2/2 · engines 3/3 · resolver 3/3. **0 failures.**

**Operator action required (all five errands #9–#13 open):** create+push public repo `theexhaust`; Cloudflare R2 bucket `exhaust-archive` **behind a custom domain** (never raw `r2.dev` — egress covenant) + the four R2 secrets as Actions secrets under the SPEC-02 names; three unguessable ntfy topics (health/pulse/gate) + confirm phone receipt; healthchecks.io project + one check. These are **already filed** as Vikunja `observatory` #9–#13 (BUILD-00 setup errands) — **not re-filed** (reuse rule; also the `vtask` bus was unreachable this session — Tailscale endpoint `desktop-vsro8kt…ts.net:3456` timed out — so no board mutation was possible regardless). **W-000 stays `blocked` and `NEXT.md` stays pointed at W-000**: the next worker re-runs this same gatecheck once the operator reports the errands done. Do not advance to W-001 until W-000 passes.

**Same session, continued — operator completed errands #9–13 live; W-000 re-run → all five checks PASS. W-000 DONE.** The operator stood up the infra interactively and this session verified each piece end-to-end (not "should work" — actually exercised):
1. **Repo + push + CI — PASS.** `origin` → `github.com/mlawsonking/theexhaust` (public); pushed `main`; the `ci` workflow ran **success on GitHub in 17s** (`gh run list`).
2. **R2 secrets + boto3 round-trip — PASS.** Live boto3 **list→put→get** against `exhaust-archive` succeeded (endpoint `112ede6f…r2.cloudflarestorage.com`, `region_name=auto`); left a stable `test/roundtrip.txt` (30 B) for check #3. All four SPEC-02 creds set as **Actions secrets** (`R2_BUCKET/ENDPOINT/ACCESS_KEY_ID/SECRET_ACCESS_KEY`) — set via `gh secret set` extracting values from a scratch file so they never entered chat/logs. `select_storage` (collectors/run.py) reads exactly these four env names → the fleet will pick up R2 automatically.
3. **Custom domain over HTTPS — PASS.** `theexhaust.org` moved to Cloudflare NS (`dorthy/ricardo.ns.cloudflare.com`); `archive.theexhaust.org` connected to the bucket (proxied). `https://archive.theexhaust.org/test/roundtrip.txt` → **HTTP 200, cert verified, `Server: cloudflare` (DFW edge), exact body** — served through the custom domain, **not** `r2.dev` (dev URL left disabled per the egress covenant).
4. **ntfy — PASS.** Test publish accepted by `theexhaust.sh/theexhaust-75Z` (msg id returned) **and operator confirmed the phone buzzed** (subscribed in the ntfy app). Wired to all three role env vars (`NTFY_ALARM/GATE/PULSE` → the one topic; per-message priority still differentiates alarm=high / gate=default / pulse=low).
5. **healthchecks — PASS.** Project + one check; ping returned HTTP 200. Bound to `HC_NHTSA_RECALLS` (the flagship collector's heartbeat); the remaining per-collector checks are W-002/W-003.

boto3 1.43.57 installed into the working interpreter (`C:\ProgramData\miniconda3\python.exe`). Full §5 suite re-run green before commit. **Handoff: W-000 `done`; `NEXT.md` now carries W-001** (R2 backend live + restore drill). **Env-propagation gotcha for the next worker:** `setx` writes the registry but a fresh interpreter is needed to see it, and this session's spawned shells never inherit it — the four R2 creds validated here live in this session's scratchpad `r2-creds.env` (session-scoped, gone next session). W-001 must ensure the four `R2_*` names are in the environment of whatever process runs the collectors (operator persists via `setx` for future sessions + Task Scheduler; a same-session run sources the scratch file). Nothing further required from the operator until the W-006 retrocast launch gate.

---

## 2026-07-28 — W-001 · R2 backend live + restore drill (WORKER) → **DONE**

The fleet now writes to **real R2**, and byte-integrity restore is proven through the custom domain. All work against live sources (re-verify-before-depend standing order satisfied — every collector hit its real source today, schema-validated, zero drift).

**Fleet-to-R2 wiring (new code, tested):** moved `select_storage` from `run.py` into `framework.py` (its shared home beside the backends) so both `run.py` and the `ats-boards` fleet can select R2. **`ats_boards.py` was hardcoded to `LocalFSBackend`** even in production (bug for BUILD-01) → now uses `select_storage` when not `--verify`. Regression test `test_select_storage_switches_on_env` (creds present → `R2Backend`, absent → `LocalFSBackend`) added → framework suite 6→7.

**6 collectors stored to real R2** (`--verify` off, env creds; one full vintage each, live today):
| collector | rows | raw | stored | R2 key ext |
|---|---|---|---|---|
| cms-deficiencies | 418,479 | 165.0 MB | 4.09 MB (.zst) | csv.zst |
| cpsc-recalls | 9,960 | 18.1 MB | 3.27 MB | csv.zst |
| nhtsa-recalls | 243,097 | 14.76 MB | 14.76 MB (raw zip) | zip |
| nhtsa-complaints | 2,228,766 | 367.9 MB | 367.9 MB (raw zip) | zip |
| fdic-failures | 4,115 | 2.41 MB | 0.24 MB | json.zst |
| ats-boards | 3 boards / 1,038 postings | — | 3 objects | json.zst |

R2 inventory confirmed: **14 objects, 390,535,823 bytes** under `raw/` (+ manifests per collector; ats-boards keys by `ats/token`). `HEALTH.json` records all 6 `stored`, band `ok`, none paused. (The 367 MB complaints pull ran to completion locally in 166 s — W-002 still owns the *scheduled* Actions cron for its recurring delta; the first full vintage is now archived.)

**Restore drill (SPEC-01 §6) — PASS through `https://archive.theexhaust.org`:** for a zst CSV (cms-deficiencies: fetched 4.09 MB → decompressed 165.0 MB → **sha256 matches the manifest**, schema revalidates, 418,479 rows) and a raw ZIP (nhtsa-recalls: 14.76 MB, sha256 match, schema valid). Both `Server: cloudflare` — served over the custom domain, never `r2.dev`.

**Finding — Cloudflare Bot Fight Mode 403s the bare `Python-urllib` UA** on the custom domain (a known-bot signature). `curl`, browsers, `python-requests`, and the framework's own `DEFAULT_UA` (`TheExhaust/0.1 …`) all get **200**, so the real fleet/restore code path is unaffected (framework `http_get` sets `DEFAULT_UA`). Minor friction only for naive consumers who fetch archives with Python's default UA and no header. **WORKPLAN candidate for the orchestrator (site phase / W-007):** decide whether to tune Bot Fight Mode / add a WAF allow-rule for the archive host so "anyone can rerun the receipts" holds literally, or just document "send a User-Agent." Not fixed here (out of W-001 scope; no covenant breach — access is open to any normal client).

**`ci/run_all.py` added** — runs the exact BUILD-PROTOCOL §5 block, prints per-step PASS/FAIL + a tail line, exits nonzero on any failure (surfacing the failing step's output to stderr). `ci.yml` switched from 8 inline steps to `python ci/run_all.py` (boto3 was already installed via `requirements.txt`). Suite green locally: **8/8 steps**. `BUDGET.json` updated with real figures (0.39 GB, $0/mo — far under R2's 10 GB free tier).

**Env note carried forward:** this worker ran in the same process as the W-000 session, so its shells could not see the persisted `setx` R2 creds; it sourced them from the W-000 scratch `r2-creds.env`. A genuinely fresh session (or the Task Scheduler jobs) will inherit the persisted user env vars. **Hand off: W-001 `done`; NEXT.md → W-002** (Actions cron fleet + scheduled complaints delta + cron-drift defenses).

---

## 2026-07-28 — W-002 · Actions cron fleet (6 collectors scheduled in R1 against R2) — `done`

The archive now runs itself in GitHub Actions, no operator box required. Built a reusable runner + 6 per-collector scheduled workflows, dispatched all 6, and verified green end-to-end against real R2. Commit `1e3b776` (fleet + ats fix); this hand-off in the follow-up commit.

**Workflows (SPEC-02 §1).** `.github/workflows/_collector.yml` — reusable `workflow_call` runner: standard runner, no LLM key, `permissions: contents: read`, exports the R2 secrets + all six `HC_*` (empty→inert) into `env:`, then `collectors.run <target>` or `collectors.ats_boards`. Six thin callers, each with `workflow_dispatch`, a per-collector `concurrency` group (`cancel-in-progress: false`), and an **odd-minute, staggered, over-scheduled** cron vs its SPEC-01 §2 cadence:

| workflow | cron (UTC) | target cadence | over-schedule |
|---|---|---|---|
| collect-ats-boards | `13 1,9,17 * * *` | daily (most perishable) | 3×/day |
| collect-cms-deficiencies | `17 4 * * 1,4` | weekly | 2×/week |
| collect-cpsc-recalls | `23 5 * * 2,5` | weekly | 2×/week |
| collect-nhtsa-recalls | `29 6 * * 1,4` | weekly | 2×/week |
| collect-nhtsa-complaints | `37 7 * * 3` | monthly (367 MB) | ~weekly (no over-schedule — file is huge) |
| collect-fdic-failures | `43 8 * * 6` | quarterly | weekly (tiny file) |

**Dispatched all 6 — every run GREEN, zero datacenter-IP 403s** (the W-002 headline risk did not materialize; every source served 200 to Azure runners). Per-collector Actions results:

| workflow | run | action (Actions) | R2 evidence |
|---|---|---|---|
| cms-deficiencies | 30358531252 | `unchanged` `d70b67207315` | dedupe vs baseline |
| cpsc-recalls | 30358533413 | `unchanged` `41878609dcab` | dedupe vs baseline |
| fdic-failures | 30358537877 | `unchanged` `24e6a3e54493` | dedupe vs baseline |
| nhtsa-recalls | 30358535940 | **`stored`** `efab48ed2da2` + **heartbeat `pinged`** | `raw/nhtsa-recalls/2026/07/28/1220-efab48ed2da2.zip` + manifest ✔ listed in R2 |
| nhtsa-complaints | 30358540340 | **`stored`** `73acbdca6b6f` (367 MB in ~63 s) | new 51-field vintage in R2 with manifest |
| ats-boards | 30358529393 | **`stored`** stripe `fc3dcca31138`, 2 boards `unchanged` | `raw/ats-boards/greenhouse/stripe/2026/07/28/1220-fc3dcca31138.json.zst` ✔ listed in R2 |

So **R2 write-from-Actions is proven concretely** (3 collectors stored; objects verified present in R2 via boto3 list from the operator box — not "should work"), **dedupe is proven** (3 collectors + 2 ats boards returned identical-hash `unchanged`), and the **`HC_NHTSA_RECALLS` heartbeat pinged healthchecks end-to-end from Actions**. The 3 `stored` collectors' sources genuinely drifted since the W-001 06:52 baseline (different hashes), so these are correct new vintages, not duplicates. **Second-firing dedupe** shown explicitly: re-dispatched `collect-cms-deficiencies` (run 30358888544) → again `unchanged` `d70b67207315`.

**ats-boards brought up to the R1 job contract (SPEC-02 §1).** `run_fleet` now pings the `ats-boards` heartbeat (`HC_ATS_BOARDS`, via a new `_heartbeat` helper mirroring the framework's — OK ping on a clean run, `/fail` ping on any quarantine, never raises) and `__main__` **exits nonzero on any quarantine** (previously it always exited 0 and never pinged — a scheduled quarantine would have gone green and silent, violating "a silently-stopped collector is an alarm"). Regression test `test_ats_fleet_heartbeat_and_alarm` added (records the OK vs `/fail` ping and the quarantine count). Suite green **8/8** (framework 7, engines now 5).

**KNOWN GAP — collector state is not committed back (HIGH-priority WORKPLAN candidate, filed below).** The R1 jobs run `contents: read` and do **not** commit `ops/state/HEALTH.json`, so a collector whose source has drifted from the *committed* baseline will **re-store the same content on each subsequent firing until a session commits state** (the checkout always starts from the stale baseline). SPEC-02 §1 explicitly anticipates the fix — *"a repo-activity keepalive is unnecessary while collectors commit state"* — i.e. collectors are supposed to commit their state. Not implemented here because it is a real architectural decision (shared `HEALTH.json` is read by `opscore/report.py` + `weekly.py`, so the choice is: per-collector state files + report-reader refactor, vs. a serialized rebase-retry commit on the shared file, vs. the SPEC-02 §2 weekly R2 session owning state commits) that the orchestrator should scope, not a worker improvise mid-item. **Near-term impact is bounded and non-destructive:** the seed board universe is tiny (3), cadences are weekly/quarterly, complaints fires once-weekly (no over-schedule), and duplicate objects are self-identifying (same `<hash>` suffix, different `HHMM`) so a later compaction pass can remove them — but for large files (complaints, 367 MB) recurring duplicates would eventually threaten R2's 10 GB free tier, so this should land before heavy over-scheduling or universe expansion. Filed as a WORKPLAN candidate; the fleet stays enabled meanwhile (over-collection is the covenant's stated preference over missed captures).

**Hand off: W-002 `done`; NEXT.md → W-003** (alarms + weekly session live). The state-commit-back candidate is flagged for the orchestrator to sequence (natural fit at/with W-003, since the weekly R2 session is one candidate owner of state commits).

---

## 2026-07-28 — W-002b · Collector state-commit-back (per-collector state files) — `done`

Closed the W-002 dedupe-persistence gap. Orchestrator promoted this ahead of W-003 and **locked option (a)** (per-collector state files); built exactly that — no re-litigation. Commits `d1b6178` (impl) + `6931ca4` (permissions fix) + the Actions-authored state commit `d2cdbf7`; hand-off in the follow-up commit.

**What changed.** State is now `ops/state/health/<collector>.json`, one file per collector, so each Actions job commits **only its own file** → the shared-`HEALTH.json` write race is gone *by construction*. `collectors/run.py` and `ats_boards.py` write the per-collector path in R1 (verify mode unchanged); `framework._save_health` + `ats_boards.run_fleet` `makedirs` the dir. Readers merge: `opscore/report.merged_health()` unions `ops/state/health/*.json` (authoritative) with legacy `HEALTH.json` (fallback for any collector not yet split); `report.py` + `weekly.py` consume it, and the weekly driver **re-materializes** the merged legacy `HEALTH.json` (keeps SPEC-02's letter + human readability). Migrated the existing 6 collectors into per-collector files. `_collector.yml`: `contents: write` + `fetch-depth: 0` + a **state-commit step** — skips on `unchanged` (baseline already committed → no timestamp-churn commits), else commits `state(<c>): <action> <hash12> [skip ci]` and pushes with `git pull --rebase --autostash` retry ≤2 then loud-fail. Added `keepalive.yml` (monthly empty `[skip ci]` commit) for the 60-day cron-disable backstop. Tests: `merged_health` reader-merge incl. legacy fallback + max-generated (opscore 18→ now 19 with this... actually +1 = 19), per-collector-write `makedirs` (framework 8→9).

**Caught + fixed a startup_failure (evidence of "should work is not done").** First dispatch of the new workflow hit `startup_failure` ("workflow file issue"). Root cause diagnosed, not guessed: the repo's **default `GITHUB_TOKEN` permission is `read`** (`actions/permissions/workflow` → `default_workflow_permissions: read`), and a **reusable** workflow's `permissions:` can't exceed the caller's grant — the callers had no `permissions:` block (→ read), so the reusable's `contents: write` request exceeded bounds and failed at startup. Fix: declared `permissions: contents: write` on all six caller workflows (a workflow-file change — **no repo-setting change**, so no security-setting escalation needed). Re-dispatched → green.

**Acceptance — all met, proven live (the proof W-002 structurally couldn't produce):**
- Suite green **8/8** (`python ci/run_all.py`).
- **One real Actions firing commits its state file:** `collect-nhtsa-recalls` firing 1 stored `efab48ed2da2` and the job pushed `d2cdbf7 state(nhtsa-recalls): stored efab48ed2da2 [skip ci]` to `main` (baseline advanced `8cc4c53733d7`→`efab48ed2da2`); persist step logged `state pushed (try 1)`.
- **Next firing dedupes against the freshly committed baseline:** firing 2 → `action: unchanged` (`efab48ed2da2`), persist step logged `unchanged — baseline already committed` (no store, **no duplicate**).
- **`[skip ci]` honored:** `gh run list --commit d2cdbf7` → empty; the state commit triggered zero workflows.
- **Duplicate accounting confirms the fix:** R2 `raw/nhtsa-recalls/2026/07/28/` holds `0552-8cc4c537` (W-001), `1220-efab48ed` (W-002), `1404-efab48ed` (W-002b firing-1 transitional dup — same hash, stale migrated baseline) — and **firing 2 added none**. So the predicted *one* transitional duplicate per drifted collector, then clean forever; the dup is self-identifying (shared `efab48ed` hash) for a later compaction pass.

**Not stress-tested (noted, safe by construction):** the concurrent-push race path (two collectors committing at the same instant) — firing 1 pushed on try 1, no race occurred. The rebase-retry is standard git and conflict-free by construction (distinct per-collector files → clean replay); the loud-fail-after-2-retries is the backstop. Natural schedule overlap or a future all-at-once dispatch will exercise it live.

**Hand off: W-002b `done`; NEXT.md → W-003** (alarms + weekly session). Note for W-003: the weekly driver now re-materializes `HEALTH.json` from the per-collector files — that write is part of what the weekly session commits.

---

## 2026-07-28 — W-003 · Alarms + weekly session live — `partial` (code+session done; drill/scheduler blocked on operator infra)

The watching layer stops being inert on the code side. Everything within a worker's power is built, tested, and proven; the two pieces that need infrastructure only the operator can mint (a healthchecks.io API token; a Task Scheduler job + its unattended-permission posture) are **mechanized to one-command operator errands** and filed as precise Vikunja blockers — not left as prose.

**Ground truth re-verified first (not assumed):** `gh` has `repo`+`workflow` scopes (can set Actions secrets); Actions secrets `NTFY_ALARM/GATE/PULSE` + `HC_NHTSA_RECALLS` + all `R2_*` present; **no** healthchecks API token anywhere (User env + no local file) → check-creation is genuinely operator-gated; `NTFY_*` **not** in User env → the weekly-session local-env step was really undone; `_collector.yml` already wires all six `HC_<COLLECTOR>` env vars; framework pings on `stored` **and** `unchanged` (drift withholds) — so grace keys off firing cadence, not target cadence.

**Item 6 — futility-clause auto-gate (DONE + tested).** `opscore/weekly.py` gained `maybe_file_futility_gate(root, today, bus)` wired into `run_weekly` (new step 5, after the sweep). On/after the pre-registered date (`_futility_date` reads the CALENDAR.md futility line, falls back to the `date(2027,12,31)` constant — so an operator override that re-arms the clock lands in one place) it files exactly one **mandatory** project-kill gate carrying the pre-registered bar (≥2 published retrocasts AND ≥1 external citation — scored honestly by `_futility_score`, which defaults 0/0-unmet pre-launch and has a `SCORECARD.json` hook for later), the archive-mode default, and the written-override-with-a-new-kill-date requirement. Idempotent by design: skipped while one is pending or after a **real** terminal decision; but an ignored one that expired-no-action (empty DECISION, swept to `decided/`) **re-files** next week — inaction may neither silently kill nor silently continue the project. `default_on_expiry` stays `no-action` (the SPEC-04 §3 invariant — nothing ever executes by expiry — is never weakened; archive-mode is a posture the operator enacts, not a gate side-effect). Tests (+4): date parse/fallback, fires-on-and-after-date + idempotent, re-files-on-expiry-but-stops-after-decision, and end-to-end through `run_weekly` (gate ntfy fired; before-date files nothing).

**Item 2 — ntfy topics into local env (DONE).** `NTFY_ALARM/GATE/PULSE` persisted to **User** env = `theexhaust-75Z` (verified read-back); Actions secrets confirmed already present. So a *freshly launched* weekly session (Task Scheduler) inherits them and `opscore.alarms` sends for real.

**Item 5 — one real weekly report, pulsed to the phone (DONE).** Ran `python -m opscore.weekly` live (ntfy topics set inline so the already-running process could send). Output: compiled `ops/reports/2026/W31.md` (6/6 collectors green, $0 storage, 0 decisions), re-materialized `ops/state/HEALTH.json` from the per-collector files, no spurious gates, no futility (correct — before 2027-12-31), and **pulsed**. Independently confirmed the ntfy delivery path returns **`200 OK`** from the operator box (`Invoke-WebRequest` to `ntfy.sh/theexhaust-75Z`) — the mechanical proof; the operator confirms the audible phone receipt (two notifications: the W31 pulse + a labeled "W-003 verify" test). `ALARMS.jsonl` ledger created (persistent — committed).

**Item 1 — healthchecks provisioning (MECHANIZED; execution operator-blocked → Vikunja #212).** No API token exists and NEXT.md forbids hand-creating silently, so instead of a manual dashboard dance I built the token-driven mechanization: `opscore/healthchecks.py` derives one cron-check spec per `collect-*.yml` straight from its cron — **grace = 1.5 × the max gap between consecutive firings** (SPEC-03 §1 "cadence × over-scheduling"; tolerates one drifted/skipped firing, catches a true stop), `channels:"*"` so one ntfy integration covers all, `unique:["name"]` idempotent. CLI `ops/setup/healthchecks_setup.py` prints the plan on a dry run and, with `--apply` + `HEALTHCHECKS_API_KEY`, creates/updates the 6 checks and sets each `HC_<COLLECTOR>` Actions secret via `gh`. Dry-run verified — computed graces: ats-boards 12 h, cms/cpsc/nhtsa-recalls 144 h (6 d), fdic/nhtsa-complaints 252 h (10.5 d). The weekly-session + site-publish checks in the §1 budget are deliberately **not** created (their runners don't exist yet — a check for a non-running job just false-alarms). Tests (+2): the cron→gap→grace math (incl. a day-of-month cron failing loud) and the specs matching the live workflows. **Blocker #212** collapses the operator's job to: mint a token, add the ntfy integration, run one command.

**Item 3 — kill-one-collector drill (DOCUMENTED; blocked on #212).** `ops/playbooks/kill-drill.md`, built around healthchecks' `/fail` endpoint as the **primary** path: it proves the whole chain (check down → ntfy → phone) in ~1 min **without disabling any collector**, so no real collection window is missed (archival-first covenant). The slow grace-window drill (disable a schedule, wait, re-enable + backfill) is documented as the optional periodic test. Can't execute until the checks + ntfy integration exist (#212) — folded into that blocker.

**Item 4 — schedule the weekly R2 session (SCRIPTED; operator action → Vikunja #213).** `ops/setup/schedule-weekly-session.ps1` registers an "Exhaust Weekly Ops" Task Scheduler job (Mondays 09:00) that runs `claude -p` on `ops/playbooks/weekly-ops.md`. Left **inert by default** — two decisions are the operator's, surfaced as comments: the unattended-permission posture (allowlist vs `acceptEdits` vs `--dangerously-skip-permissions` — a security choice) and ensuring the scheduled `claude` runs under the **subscription**, not metered API (spend covenant). Not self-registered: registering a scheduled unattended agent is persistent config + a security decision, squarely operator territory.

**Also (SPEC-03 §1 forward-wiring):** `run_weekly` now pings a `HC_WEEKLY` dead-man heartbeat on clean completion — **inert until `HC_WEEKLY` is set** (which waits on the weekly-session check existing, so it can't false-alarm), so item 4's completion activates it with no further code. Test asserts it's inert without the env var.

**Suite green 8/8** (`python ci/run_all.py`; opscore 19→25). Covenant guard clean (the new `opscore/healthchecks.py` + `ops/setup/` touch no do-not-collect entities and no R1 LLM key).

**Observation flagged, not silently fixed — the orphan clock reads "2 weeks to autonomous freeze."** `ops/state/ACK` says `last-active: 2026-07-11`, and operator liveness is measured by ACK updates + gate DECISIONs (SPEC-06), **not** code commits — so despite the operator being very active, the clock is ticking toward a 2026-08-08 autonomous freeze. I did **not** forge the ACK (faking the operator's liveness signal would defeat the orphan protocol). Pre-launch this is a near-no-op (nothing published/named to freeze), but the operator should `echo "last-active: 2026-07-28" > ops/state/ACK` (or decide any gate) to reset it. WORKPLAN candidate: consider having a worker/orchestrator session touch ACK, or teach the orphan clock to also count buildlog/commit activity.

**Vikunja hygiene note for the operator:** the board still shows the completed BUILD-00 errands **#9–13** plus two stale duplicate sets **#39–43** and **#84–88** (all done in W-000, never closed — the agent lacks done-permission). Close them: `foreach ($id in 9,10,11,12,13,39,40,41,42,43,84,85,86,87,88) { vtask done $id }`. New W-003 blockers filed: **#212** (healthchecks provisioning), **#213** (weekly Task Scheduler).

**Files:** `opscore/weekly.py` (futility wiring + weekly heartbeat), `opscore/healthchecks.py` (new), `ops/setup/healthchecks_setup.py` (new), `ops/setup/schedule-weekly-session.ps1` (new), `ops/playbooks/kill-drill.md` (new), `opscore/tests/test_opscore.py` (+7 tests), `ops/state/HEALTH.json` (re-materialized), `ops/reports/2026/W31.md` (new), `ops/state/ALARMS.jsonl` (new).

**Hand off: W-003 `partial`** — the code + live weekly session are done and green; the SPEC-03 §6 **drill acceptance is pending operator #212** (checks + ntfy integration), and the weekly Task Scheduler job is pending operator #213. Both are operator-completable without a worker session (run two scripts + a 1-min `/fail` drill). **NEXT.md → W-004** (C2 WARN tranche 1) — independent of the W-003 residual; the orchestrator may instead hold to close W-003 after #212. Futility wiring, local env, and the live pulse are fully accepted-worthy now.

---

## 2026-07-28 — W-004 · C2 WARN Watch, tranche 1 (10 states) — `done`

The WARN Watch corpus begins. Ten states' layoff-notice sources archive to R2 as one fleet with a single shared heartbeat — the perishable ground truth behind the Shadow Layoffs observational flagship.

**Design (mirrors the ats-boards fleet).** `collectors/warn.py` is a **data-driven fleet** over `collectors/seed_warn.json` (per-state: `format` + `data_url` or `landing_url`+`link_regex`), one health node `warn` with per-state detail, one shared `HC_WARN` heartbeat (OK only if zero quarantines / `/fail` otherwise), per-state content-hash dedupe. **Store-raw-always** semantics (the W-004 steer): the raw payload is the deliverable and is stored on every changed fetch; parsing is **best-effort manifest metadata**, never a gate — a parse miss records `parse_ok`/`parsed_rows` and moves on. Quarantine is reserved for **fetch** failure (transport error / non-200 / block page) → alarm + heartbeat withheld + nonzero exit (SPEC-02 §1 job contract). Parsing is **stdlib-only** (no new R1 deps, honoring `requirements.txt` "keep minimal and portable"): CSV/JSON exactly, XLSX via a zipfile `<row>` counter, HTML via an `html.parser` `<td>`-row counter; XLS/PDF/unknown store raw with the count withheld. A `landing_url`+`link_regex` resolver handles yearly/monthly-rotating filenames (mirrors `cms_deficiencies.resolve_csv_url`); a `{year}` token in a `data_url` is substituted with the current UTC year (FL's per-year page rolls over automatically).

**Every source re-verified live with the collector's own `http_get` (DEFAULT_UA, HTTP 200) on 2026-07-28** — not the research assistant's fetcher, and not from memory (standing order). A background research pass proposed candidates + covenant-checked them; I re-verified each and rejected the walled ones. **10 states shipped:** CA (xlsx), NY (retired HTML table — see below), TX (Socrata CSV), WA (HTML/WebForms), IL (xlsx via landing-resolve → newest monthly), NJ (xlsx, one sheet/year), PA (HTML), FL (HTML, `?year={year}`), MD (HTML), WI (HTML).

**Proven live to real R2 (not "should work"):**
- **First firing: all 10 stored** — parsed-row counts CA 41, NY 69, TX **2 368** (full multi-year via `$limit`), WA 17, IL 408, NJ 241, PA 0, FL 101, MD 82, WI 0. (`PA`/`WI` parse to 0 — their notices are grouped `<div>`s / a per-notice link-list, not a `<td>` table — but the full raw HTML is archived; that is the deliverable, per the steer.)
- **Dedupe proven — second firing: 6 `unchanged`** (CA, TX, IL, NJ, PA, FL — identical hash, no new object) **+ 4 re-stored** (NY, WA, MD, WI). The four HTML pages carry per-request-volatile markup (ASP.NET ViewState / session tokens / timestamps), so they never dedupe and re-store each firing (~174 KB/firing × 2/day ≈ **127 MB/yr — trivial vs the 10 GB free tier**). Filed as a WORKPLAN candidate: a content-normalization pre-hash (strip ViewState/tokens/timestamps) would restore dedupe for these four; deliberately not built now (fragile per-source normalization; the archive tolerates over-collection).
- **Acceptance round-trip PASS (SPEC-01 §6):** pulled a stored TX snapshot **back from R2 through the custom domain** `archive.theexhaust.org` (`Server: cloudflare`, never r2.dev — egress covenant), zstd-decompressed, **sha256 matched its manifest**, and showed a real notice: `2022-01-28 · Amentum · Bowie county · North East Texas WDA · 178 affected · New Boston`.

**Three tranche-1 states deferred (walled/sourceless — gated, not evaded).** Per the catch (JS-walled → STOP that state, gate, continue): **OH** = ODJFS CMS serves a 404 shell to every non-browser fetch (curl/UA/WebFetch) → needs a headless render; **GA** = no public list exists (tcsg.edu/warn is an employer-submission form; the legacy GDOL list is defunct through 2013) → needs an open-records request; **NY current-data** = a Tableau Public dashboard with no clean file export (the **retired** NY HTML table IS archived — frozen ~early 2025, but preserving a page marked retired is real archival value). OH/GA were swapped for **MD + WI** (clean high-volume sources) to keep 10 states live; the three are documented in one `source` gate `warn-tranche1-walled-sources` (options: defer / build a covenant-reviewed headless adapter / file a GA records request; safe default = defer, the 10 keep collecting).

**Actions wiring.** `collect-warn.yml` (caller of the reusable `_collector.yml`, `entry: warn`, over-scheduled 2×/day at `29 4,16`, `contents: write` for the W-002b state commit); `_collector.yml` gained the `warn` branch (collect + persist-state `name=warn`) and `HC_WARN` in `env:`. `opscore/healthchecks.py` needed **no change** — the fleet-workflow design means `collect-warn.yml` yields exactly one logical `warn` check (secret `HC_WARN`, grace 18 h from the 12 h firing gap), so the operator's #212 provisioning now covers **7 checks**. The `HC_WARN` heartbeat is inert until #212 sets the secret (consistent with the other collectors pre-provisioning).

**Tests + suite.** `collectors/tests/test_warn.py` (+8: format handlers incl. a synthetic xlsx, resolver direct+landing, `{year}` substitution, store/parse/dedupe, xlsx-stored-uncompressed, quarantine on fetch-fail + non-200, fleet aggregation + `--only`, and **seed integrity** — ≥10 states, the required 5 present, no aggregator domains). `ci/run_all.py` + BUILD-PROTOCOL §5 gained the `collectors warn` step; the opscore healthchecks test now asserts 7 collectors incl. `warn`. **Suite green 9/9.** Covenant guard clean (warn.py + seed reference only primary state `.gov` sources; none on the do-not-collect register; no R1 LLM key).

**Proven in Actions (post-hand-off, operator authorized the push + dispatch).** After pushing, dispatched `collect-warn.yml` → run [30380851260](https://github.com/mlawsonking/theexhaust/actions/runs/30380851260) **green in 40 s**. `Collect (warn)`: **5 stored + 5 `unchanged`** (TX/IL/NJ/PA/FL dedupe'd against the committed `warn.json` baseline; CA/NY/WA/MD/WI stored — CA's source genuinely changed 41→53 rows between the local and Actions firings), 0 quarantined — real R2 writes from a standard runner. `Persist collector state (W-002b)`: committed `state(warn): stored [skip ci]` and pushed on try 1 → `73b17dd`. So the new reusable-workflow `warn` branch AND the W-002b state-commit-back machinery both work for the fleet in Actions (not just locally). (Annotation: Node 20 deprecation warning on checkout/setup-python — affects all workflows, a fleet-wide maintenance item, not a failure.)

**Files:** `collectors/warn.py` (new), `collectors/seed_warn.json` (new), `collectors/tests/test_warn.py` (new), `.github/workflows/collect-warn.yml` (new), `.github/workflows/_collector.yml` (warn branch + HC_WARN), `ci/run_all.py` + `ops/BUILD-PROTOCOL.md` (suite step), `opscore/tests/test_opscore.py` (7-collector assert), `ops/state/health/warn.json` (new, first firing), `ops/state/QUEUE/pending/GATE-20260728-warn-tranche1-walled-sources.md` (new).

**Hand off: W-004 `done`** (10 states archiving to R2, real notice round-tripped, suite 9/9). **NEXT.md → W-005** (fleet-green + BUILD-01 acceptance) — its adversarial-review scope now also covers `collectors/warn.py` + the WARN fleet/seed + `collect-warn.yml`; its fleet-green window must include the warn Actions firings. WORKPLAN candidate: content-normalization pre-hash for the 4 volatile-HTML WARN sources (restore dedupe). Pending operator: push (then optionally dispatch `collect-warn.yml` to prove the Actions path early); #212 now provisions 7 checks incl. `HC_WARN`.

---

## 2026-07-28 — W-005 · Fleet-green + BUILD-01 acceptance evidence — `partial` (4 of 5 SPEC-01 §6 criteria closed; criterion 1 is time-bound to 2026-08-04)

Ran the SPEC-01 §6 checklist against the live fleet. **Four criteria are closed with evidence; the fifth (7 consecutive green days) cannot be satisfied by any collector yet because the archive clock started 2026-07-28** — it is pending time, not failing. Two real defects surfaced and were fixed.

### 1. Seven-consecutive-green-days — **NOT YET (day 1 of 7 for the whole fleet)**

Every enabled collector's clock starts **2026-07-28**: W-001 wrote the first real vintages at 05:52 UTC, the Actions fleet first fired at 12:20 UTC, WARN at 16:59 UTC. So the earliest date any collector can show a 7-day window is **2026-08-04**. Per the NEXT.md catch, that leaves BUILD-01 open **on this criterion only** — for all 7 collectors, not a subset.

Day-1 state, all three evidence channels (heartbeats are **inert** until operator #212, so Actions history + manifests + committed state are the evidence of record — this is stated rather than glossed):

| Collector | Actions runs 07-28 | Result | Committed state | Manifest in R2 |
|---|---|---|---|---|
| cms-deficiencies | 2 dispatch | success | `stored`, streak 0 | ✅ 07-28 |
| cpsc-recalls | 1 dispatch | success | `stored`, streak 0 | ✅ 07-28 |
| nhtsa-recalls | 4 dispatch | 3 success + **1 `startup_failure` 13:59** | `stored`, streak 0 | ✅ 07-28 |
| nhtsa-complaints | 1 dispatch | success | `stored`, streak 0 | ✅ 07-28 |
| fdic-failures | 1 dispatch | success | `stored`, streak 0 | ✅ 07-28 |
| ats-boards | 3 (1 **schedule**) | success | `stored` | ✅ 07-28 (after the fix below) |
| warn | 1 dispatch | success | `stored`, 0 quarantined | ✅ 07-28 (10 state manifests) |

Zero quarantines, zero pauses, zero drift across the fleet. The one blemish is honest and stays on the record: **`nhtsa-recalls` run [30366156694](https://github.com/mlawsonking/theexhaust/actions/runs/30366156694) `startup_failure` at 13:59** — the W-002b callers-permission bug, fixed five minutes later; a clean window for that collector therefore starts 2026-07-29, not 07-28.

**First scheduled (not dispatched) firing observed:** `collect-ats-boards` cron `13 1,9,17` fired at **18:41 UTC against a 17:13 slot — 88 minutes of drift**. Exactly the unbounded-cron-drift the doctrine predicts, and precisely why over-scheduling + an external heartbeat are mandatory rather than optional.

**`ops/fleet_green.py` (new)** makes the 2026-08-04 re-check mechanical instead of a re-derivation: it gathers Actions conclusions (`gh`), R2 manifest days (boto3), and committed state, then scores each collector. The scoring rule lives in `opscore/fleetgreen.py` so it is unit-tested, not buried in a CLI. Green = every firing in the window succeeded, ≥1 did, and committed state shows neither quarantine nor pause — cadences run daily..weekly, so a green *window* can never mean "a run every day". Current output: **6/7 GREEN, `nhtsa-recalls` FAILED-RUN**, exit 1.

### 2. Injected-drift drill — **PASS (end-to-end, not the unit test)**

`ops/playbooks/drift_drill.py` (new, re-runnable) exercises the REAL `cms_deficiencies.build()` collector — real name, real `CsvSchema`, real `Collector.run`, real on-disk state file, real weekly gate/alarm chain — against a throwaway `LocalFSBackend` root. Per the W-005 catch, **live R2 is never touched** (no creds read, nothing written in the repo). Injected drift = CMS renaming one required column (`Scope Severity Code` → `Scope/Severity Code`), the realistic failure. Every assertion passed:

- firings 1–3 → `quarantined`, `alarm: True`, **heartbeat withheld**, each drifted vintage preserved under `quarantine/cms-deficiencies/2026/07/28/` — and **`raw/` stayed completely empty** (no pollution);
- firing 3 → `drift_streak: 3`, `paused: True`, `needs_gate: schema-drift-3x` (SPEC-03 §2);
- the same drifted payload recurring → `quarantined-dup`, **`alarm: False`** (anti-storm, SPEC-03 §4), no new object;
- `weekly.file_collector_gates` filed exactly one `source` gate `collector-cms-deficiencies-schema-drift-3x`, undecided on arrival, emitted at `high` priority on the alarm topic; a second pass filed nothing (no gate spam);
- recovery: a schema-clean vintage `stored`, `drift_streak` → 0, `paused` cleared ("collector keeps running", SPEC-03 §2).

(WARN "drift" is a different path — fetch-failure quarantine, already covered by its own tests. The CsvSchema drill is the SPEC-01 §6 one.)

### 3. Covenant review vs SPEC-01 §4 — **PASS, with one dated must-fix before C3 expansion**

Verified against the code, not the docstrings.

| §4 rule | cms-def | cpsc | nhtsa ×2 | fdic | ats-boards | warn (10) | Evidence |
|---|---|---|---|---|---|---|---|
| 1. Honest UA + contact | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Exactly one UA in every collector path: `framework.DEFAULT_UA` = `TheExhaust/0.1 (+https://theexhaust.org; archival public-interest collector; contact: ops@theexhaust.org)`. No per-collector header override exists anywhere (`grep 'headers='` → framework only). |
| 1. Rate-limited / sequential per host | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | One request per host per firing; fleets iterate sequentially. **No `time.sleep` exists in the repo** — politeness is currently structural (1 host = 1 request), which holds at 3 boards and 10 states but **not** at the 3–5k-board universe, where thousands of sequential requests would hit 4 ATS hosts with no delay. **Must land before the C3 expansion gate** (candidate below), not now. |
| 2. No circumvention | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | No IP rotation, no CAPTCHA handling, no browser-UA spoofing, no auth, no ToS acceptance anywhere. Demonstrated by what W-004 *refused*: OH (404s non-browser fetches) and NY-current (Tableau) were **gated, not spoofed** (`GATE-20260728-warn-tranche1-walled-sources`). |
| 3. robots.txt at onboarding | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | Official bulk APIs (CMS/CPSC/NHTSA/FDIC) follow published limits. All 10 WARN seeds carry a per-state `robots_note` verified 2026-07-28. **ats-boards asserts a "one-time robots/master-ToS check" in its docstring but no record of it exists** — the check must be *logged* before universe expansion (candidate below). |
| 4. Dedupe before store | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `last_hash` compare precedes every store; proven live in Actions on every collector (W-002/W-002b/W-004) and re-proven today. |
| 5. 403 ladder | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Nothing escalates autonomously — compliant by construction. Zero datacenter-IP 403s observed to date. The W-001 finding (Cloudflare Bot Fight Mode 403s a *bare* `Python-urllib` UA; `DEFAULT_UA` unaffected) remains a W-007 candidate. |
| 6. Do-not-collect register | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | `ci/covenant_guard.py` OK — 11 sources enforced over `collectors/`, `engines/`, `resolver/`; no R1 LLM key in any workflow. |

**No covenant violation found**, so nothing fails the build on §4. The two ⚠️ are *scale* obligations that come due with the C3 universe-expansion gate, and are recorded as WORKPLAN candidates rather than silently deferred.

### 4. C7 Kroger confirmed dark — **CONFIRMED**

`grep -i kroger` over `collectors/`, `engines/`, `resolver/`, `opscore/`, `ci/`, `.github/`, `sitegen/`, `retrocast/` → **zero hits**. No collector, no endpoint, no seed entry; `opscore.fleetgreen.FLEET` has no kroger row and a test asserts it stays out. **Correction to the phrasing in the W-005 order:** the covenant guard does *not* enforce Kroger's darkness — Kroger is not on the do-not-collect register (it is gate-blocked pending the human ToS read, not banned), so the guard has nothing to match. Darkness is currently enforced by absence + this check. Mechanizing it (a guard assertion that no `kroger*` collector exists until the gate file clears) is a WORKPLAN candidate, deliberately not built inside this item's scope.

### 5. Storage projection — **PASS, ~$0.00/mo now, under the $5 bar for ~16 years**

Full `list_objects_v2` sweep of `exhaust-archive` (measured, not estimated): **0.7889 GB across 49 objects**, versus R2's 10 GB free tier → **$0.00/mo**. Written to `BUDGET.json` through `opscore.budget.Budget` (so the projection is computed by the governor, not hand-typed); `storage_alarm()` False.

Growth is modelled from **observed** change rates × the live cron, not guesses: `nhtsa-complaints` **19.1 GB/yr (91% of all growth)** — its 368 MB flat file changed twice in 6.5 h on day 1, so every weekly firing stores and dedupe can never help; `nhtsa-recalls` 1.54; `cpsc` 0.17; `cms` 0.05; `ats-boards` 0.10; `warn` 0.03 (measured 43.4 KB/firing for the 4 volatile-HTML states — **the inherited "~127 MB/yr" estimate was high; the measured figure is ~32 MB/yr**); `fdic` ~0. **Total ≈ 21.0 GB/yr** → free tier exhausted ~Dec 2026, **$0.18/mo at year 1, $1.44 at year 5, $3.02 at year 10; the $5 bar arrives at 343 GB ≈ year 16.** Re-project triggers recorded in `BUDGET.json`: C3 universe expansion (~100 GB/yr — would move the bar to ~year 3), WARN tranche 2, any new collector.

### Defects found and fixed

1. **`ats-boards` wrote no per-day manifest — a live SPEC-01 §3 violation.** `raw/ats-boards/**` held snapshots and *zero* `manifest.json`; `archive_board` never wrote one (the framework `Collector` and `warn` both do). A day's board snapshots therefore had no checkable index — and criterion 1 explicitly leans on manifests. Fixed with `_update_manifest()` mirroring the other two (+ `engines.ats.SCHEMA_VERSION` for the manifest's schema-version field). **Proven live, not asserted:** dispatched [run 30393584449](https://github.com/mlawsonking/theexhaust/actions/runs/30393584449) → green, and `raw/ats-boards/greenhouse/stripe/2026/07/28/manifest.json` now exists in R2 carrying `git_ref: 8eac50950499` (the commit that fixed it), `schema_version: posting-v1`, 533 postings, full sha256.
2. **`warn` manifests carried no `git_ref`** (same §3 clause) — fixed. Both fleets now resolve the ref **once per fleet run** rather than once per board/state (one subprocess instead of thousands at the 3–5k-board universe); a test asserts the single resolution.
3. **Day-1 backfill.** The six `ats-boards` objects stored *before* the fix were reconstructed into their manifests from the stored objects themselves — sha256 recomputed over the decompressed bytes, postings via `ats.normalize`, `stored_at` from R2 `LastModified` — and each entry is marked `backfilled` so provenance stays honest. Nothing invented; raw objects untouched.

**Fleet-wide integrity check (a by-product worth keeping):** every manifest in R2 was re-read and each recorded sha256 compared against the hash embedded in its own object key — **18 manifests, 34 file entries, 34 match, 0 mismatch**, and the entry count exactly equals the number of raw snapshot objects. Combined with W-001's custom-domain restore drill, the archive is self-consistent end to end.

**Tests + suite.** +2 regression tests for the manifest defects (`engines` 6, `warn` 9) and +1 for the fleet-green scoring rule (`opscore` 25→26). **Suite green 9/9.** Covenant guard clean.

**Files:** `collectors/ats_boards.py`, `collectors/warn.py`, `engines/ats.py`, `engines/tests/test_engines.py`, `collectors/tests/test_warn.py`, `opscore/fleetgreen.py` (new), `opscore/tests/test_opscore.py`, `ops/fleet_green.py` (new), `ops/playbooks/drift_drill.py` (new), `ops/state/BUDGET.json`. Commit `8eac509` (fix+drill+budget) + this hand-off commit.

**Hand off: W-005 `partial`.** SPEC-01 §6 criteria **2–5 closed with evidence**; criterion **1 is a dated residual — re-run `python ops/fleet_green.py` on or after 2026-08-04** (expect all 7 GREEN; exit 0 = criterion satisfied). Recommendation to the orchestrator: **run the adversarial review now** over its widened scope (all collectors since the last pass + the workflow YAMLs + the W-002b state machinery + the WARN fleet/seed + today's manifest changes), and mark **BUILD-01 accepted on 2026-08-04 conditional on that one command coming back clean** — nothing else is outstanding, and holding the review for a calendar wait buys nothing. Workers don't self-accept (constitutional).

**WORKPLAN candidates filed (not detours):** (a) explicit inter-request rate-limit/jitter in both fleet loops — **must land before the C3 universe-expansion gate**; (b) log the ats-boards robots/master-ToS check that the docstring asserts — same deadline; (c) mechanize C7 darkness in the covenant guard; (d) the inherited volatile-HTML normalization pre-hash for WARN; (e) fleet-wide Node-20 deprecation on `actions/checkout@v4` + `setup-python@v5`.

---

## 2026-07-28 — W-005b · Pre-launch placeholder page — `done`

The first public surface. The operator approved (live, 2026-07-28, recorded in the constitution log) a **no-numbers placeholder** on `theexhaust.org` ahead of the W-007 launch: near-zero legal surface, and a live landing for the FIJ application (due Sep 14). The full site stays held for the retrocast launch story.

**Build mode.** `python -m sitegen.build --placeholder` emits exactly one `index.html` to `site/dist/`. Content, strictly per the order: the identity line + the one-sentence lede; **"Status: pre-launch. Nothing is published here yet — no numbers, no estimates, no claims"**; the factual operational line *"The archive has been collecting since July 2026"* (with the one-sentence why — perishable records disappear, so collection precedes analysis); and the method-before-results card linking the **public repo** and the **frozen NHTSA pre-registration**, inviting the reader to *check the git history yourself: the commit that freezes a method is timestamped ahead of the commit that reports how it scored*. Plus one covenant line the page itself makes true: *no trackers, no analytics, no cookies*. It reuses the site's CSS spine (theme-aware, stdlib-only, self-contained) but **not** the nav — the other four pages don't exist in this mode, so a shared nav would have shipped four dead links. Footer carries operator identity (constitution covenant 5) and the `ops@theexhaust.org` contact, which is already public in the collector User-Agent.

**Full mode is byte-identical, proven not asserted:** built the full site to a temp dir and hashed all five pages against the pre-change build — **5 compared, 0 differing**.

**A real publish hazard caught in passing.** `site/dist/` is gitignored and *did* hold a full local build. A placeholder deploy that simply wrote `index.html` into that directory would have left `track-record.html`, `retrocasts.html`, `methodology.html`, `transparency.html` sitting there — i.e. quietly publishing the held, unlaunched site from a directory-based deploy. Placeholder mode now **removes the four full-site pages from the output dir before writing**, and a test proves the directory ends up containing exactly `index.html`.

**Tests (sitegen 2 → 5),** two of them deliberately adversarial rather than confirmatory:
- *required lines* — identity, tagline, pre-launch status, the archive line, repo URL, `PRE-REGISTRATION-v1.md`, the git-ordering claim, operator name, CSS spine, and **no link to any of the four unlaunched pages**;
- *publishes nothing measured* — after stripping tags/entities and excluding ISO dates, bare years and version tags, **no digit may remain in the prose**; and none of `%`, `PR-AUC`, `precision`, `median lead`, `scorecard.json`, `<table`, `PASS`/`FAIL`, `GB` may appear. (The first draft of this test failed on `civilization&#x27;s` being read as the number 27 — the check now unescapes entities first.)
- *no trackers, ever* — no `<script>`, `<img>`, `<iframe>`, `<link>`, `@import`, gtag/Google Analytics/plausible/fbq; and **every external URL on the page must start with our own repo URL**. If that test ever has to be relaxed, that is a gate, not a fix.

**Verified live, not assumed:** both published links return **HTTP 200** (`.../theexhaust` and `.../blob/main/retrocast/nhtsa-recalls/PRE-REGISTRATION-v1.md`), and the built page was rendered and read back rather than only asserted over. Suite **9/9**.

**Deploy config for ⚑ #217 (operator).** Cloudflare Pages → Git integration, repo `mlawsonking/theexhaust`, production branch `main`, **build command `python3 -m sitegen.build --placeholder`**, **output directory `site/dist`**, root directory = repo root, custom domains `theexhaust.org` + `www`. `sitegen` is stdlib-only — no install step, no `requirements.txt` to resolve, so the build cannot fail on dependencies; set `PYTHON_VERSION=3.13` if the image defaults lower. **Fallback per the catch:** if the Pages image can't run Python, deploy from Actions with `wrangler pages deploy site/dist`, which needs a `CLOUDFLARE_API_TOKEN` repo secret (Pages:Edit) — an operator credential, not one a session invents. #217 annotated with both paths.

**Correction to the order:** NEXT.md and the WORKPLAN cited errand **#214** for the Pages hookup; the actual open task is **#217** ("Cloudflare Pages hookup for the placeholder"). #214 is not on the board. Annotated #217 and corrected both files rather than filing a near-duplicate.

**Files:** `sitegen/build.py` (placeholder mode + `REPO_URL` + `FULL_PAGES` + `--placeholder` CLI), `sitegen/tests/test_site.py` (+3).

**Hand off (W-005b): `done`.** `NEXT.md` stripped of the W-005b section as instructed — **W-006 (NHTSA retrocast) is now the standing order**, its read-list verified present. Remaining for the operator: ⚑ #217 Pages hookup (the page itself is built and committed-by-build; `site/dist/` stays gitignored by design).

---

## 2026-07-28 — W-005c · BUILD-01 adversarial-review fixes — `done` (19/19 dispositioned)

The constitutional acceptance gate. The BUILD-01 review returned **19 confirmed findings (4 HIGH / 8 MEDIUM / 7 LOW)**; BUILD-01 cannot be accepted until each has a disposition. **All 19 are dispositioned: 17 fixed with regression tests, 2 deferred/accepted with reasons recorded in `docs/05-SCOPE-LEDGER.md` §5b** (not buried in prose — each comes due at a trigger). Hardening only; no new capabilities.

### Disposition table

| # | Sev | Finding | Disposition |
|---|---|---|---|
| F01 | HIGH | Quarantine outcomes never reached committed state (both fleets said `unchanged`/`stored`, so `_collector.yml` skipped the commit) | **FIXED** — `last_action` reports `quarantined`; `last_success` refreshes only on a clean run, else `last_run`. Test: mixed-outcome fleet run asserts the `/fail` heartbeat leg (previously zero coverage) **and** that the committed node says `quarantined` with no `last_success` |
| F02 | HIGH | One dead board killed the whole ats fleet (unwrapped fetch + `http_get` raising) | **FIXED** — per-board try/except mirroring warn. Test: 3-board seed, board 2 raises `URLError` → boards 1 and 3 still store, health written, `quarantined==1` |
| F03 | HIGH | `assert n >= 1` made a legitimately empty board a parse failure (alarm 3×/day forever; vanished-postings snapshot never archived) | **FIXED** — empty-but-parseable = valid store, `postings=0`; genuine parse failures quarantine **once** then anti-storm dedupe. Test covers all three paths |
| F04 | HIGH | Covenant guard scanned only `*.py`, but W-004 moved every source URL into the seed JSONs | **FIXED** — scans `*.py` + `*.json`. Test plants a banned domain in a temp seed and asserts the guard fails |
| F05 | MED | No 3-strike pause/gate wiring in either fleet; per-unit records live where the gate sweep never looks | **FIXED** — per-unit `fail_streak` → `paused` at 3, surfaced as a node-level `needs_gate`. Test drives 3 failures, asserts the pause, the skip, and that `weekly.file_collector_gates` files exactly one gate |
| F06 | MED | `storage.put` / corrupt-manifest exceptions aborted the remaining units | **FIXED** — per-unit try/except inside both `run_fleet`s; `read_manifest()` treats unparseable as absent in all three implementations. Tests: flaky backend (other state still collected), corrupt manifest replaced not fatal |
| F07 | MED | SPEC-03 §2 auto-pause was recorded but never enforced; a clean payload silently self-un-paused | **FIXED** — `Collector.run` returns `paused` **without fetching**; only an operator decision clears it. Test asserts zero fetches while paused and that a clean payload does not un-pause |
| F08 | MED | A re-armed futility clause could never fire; `_futility_date` took the first date on the first matching line | **FIXED** — gate slug carries the armed date; date parse takes `max()` of all valid dates on all futility lines. Tests: full re-arm cycle (2027 override → 2029 fires), stray earlier mention, malformed re-arm |
| F09 | MED | `fleet_green` read a corrupt state file as `{}` → vacuous **GREEN** on the acceptance gate | **FIXED** — `committed_state` moved into `opscore.fleetgreen`; unreadable (or missing record) → `STATE-UNREADABLE`, never green. Synthetic 7-day fixture test |
| F10 | MED | An in-flight run counted as a failed day → false **FAILED-RUN** on the acceptance gate | **FIXED** — `run_rows()` drops non-terminal runs; `score()` ignores them defensively. Same fixture test |
| F11 | MED | Robots verified against hosts the collector never fetches (WA, IL) | **FIXED** — re-probed with the collector's own `http_get`: `www.illinoisworknet.com/robots.txt` → **404** (nothing disallowed); `fortress.wa.gov/robots.txt` → **ConnectionResetError on two polite attempts — genuinely unverifiable**. Both `robots_note`s rewritten to name the fetched host; WA's records the failure **and the sanction basis** (endpoint returns 200 to our honest UA, no auth/ToS/CAPTCHA, 2×/day) rather than asserting a compliance we could not check |
| F12 | MED | Volume-anomaly detector entirely absent from the warn fleet | **FIXED** — per-state `rows_history`/`rows_median`, `volume_band` in the manifest, extreme tier alarms + nonzero exit; always-zero states (PA/WI link lists) exempt rather than permanently red. Test drives an 800→3 collapse |
| F13 | LOW | Non-200 forensics branch unreachable (urlopen raises, body discarded) | **FIXED** — `http_get` returns non-2xx `(code, headers, body)`. Tests at both levels: framework returns the body; warn stores the 403 block page to `quarantine/` with `raw/` untouched |
| F14 | LOW | A truncated state file crashed every later firing | **FIXED** — `load_state()` tolerates corruption in all three loaders. Test: truncated file → collection proceeds, state rebuilt |
| F15 | LOW | An empty fleet pinged the dead-man **green** and exited 0 | **FIXED** — empty → `/fail` + nonzero exit, both fleets. Tests assert the success URL is never pinged |
| F16 | LOW | SmartRecruiters `?limit=100` with no pagination → silently truncated "full board" vintages | **PARTIAL FIX + DEFERRED** — a payload whose `totalFound` exceeds what it returned is now **refused and quarantined loudly** (an immutable truncated vintage can never be re-fetched), and a test **blocks SR entries from the seed** until pagination lands. Full offset pagination deferred to the **C3 universe-expansion gate** — ledger §5b |
| F17 | LOW | SPEC-01 §4.1 rate-limit/jitter (a MUST) entirely unimplemented | **FIXED** — injectable `polite_pause()` called between fleet iterations, no-op in tests. Test asserts N−1 pauses and none before the first request |
| F18 | LOW | warn manifests omitted SPEC-01 §3's schema-version | **FIXED** — `PARSER_VERSION = "warn-parse-v1"` on the manifest and every entry |
| F19 | LOW | Missing W-004 regressions; two-writer manifest race unpinned | **FIXED (a,b) + ACCEPTED (race)** — store-raw-always and same-day manifest-append tests added. The race is **accepted with reasons** (ledger §5b): Actions is the only scheduled writer, the loss is an index entry never data, and the index is provably reconstructible (W-005 backfilled six entries from the stored objects) |

**One correction to the review, on evidence:** F19a's suggested fixture assumed a garbage body declared `csv` fails to parse. It does not — `csv.reader` tolerates any bytes and returns `(0, True)`. The test therefore exercises the genuine parse-miss path with a format whose parser really can fail (`xlsx`), and separately asserts the csv-garbage case still **stores** (the constitutional store-raw-always steer), with a collapse-to-zero caught by F12's volume detector rather than by refusing to archive. Noted in the test docstring so the next reader doesn't "fix" it back.

**A bug found while fixing F05, outside the 19.** `gates.new_gate` drops the slug straight into a filename with no validation. My first `needs_gate` value contained a colon — on Windows that writes an **NTFS alternate data stream**: no error, file created, and `load_pending` can never see it. A gate the operator is owed would simply vanish, silently, on the one interface the autonomy system depends on. Both call sites now emit sanitized slugs (board keys contain `/` too), and `new_gate` **raises** on an unsafe slug, with a test.

**Proven live after the fixes (not "should work"):**
- `collect-warn` [run 30398988686](https://github.com/mlawsonking/theexhaust/actions/runs/30398988686) **green** — 10 states, 5 stored / 5 dedupe'd, `quarantined: 0`, `paused: []`, `volume_extreme: []`, per-state `volume_band` recorded on every store; state committed back (`ec98b68`, push succeeded on retry 2 — the rebase-retry doing its job under genuine concurrency with the board fleet).
- `collect-ats-boards` [run 30398990995](https://github.com/mlawsonking/theexhaust/actions/runs/30398990995) **green** — 3 boards, 2 stored, `quarantined: 0`, `empty: false`, stripe at 533 postings; state committed (`9db37a0`).
- `ci` green on the fixes commit; the injected-drift drill re-run **PASS** against the new contract (it now also proves the pause is enforced and that only an operator decision resumes collection).

**Suite: 9/9, tests 26 → 61** (framework 8→13, warn 9→18, opscore 26→30, engines +5, covenant guard +1).

**Files:** `collectors/framework.py` (http_get non-2xx, `polite_pause`, `load_state`, `read_manifest`, pause enforcement), `collectors/warn.py`, `collectors/ats_boards.py`, `collectors/seed_warn.json` (F11 robots corrections), `engines/ats.py` (`truncation`), `opscore/weekly.py` (futility), `opscore/gates.py` (slug safety), `opscore/fleetgreen.py` (+`committed_state`/`run_rows`), `ops/fleet_green.py`, `ops/playbooks/drift_drill.py`, `ci/covenant_guard.py`, `docs/05-SCOPE-LEDGER.md` (§5b), + 5 test modules. Commit `e29c326`.

**Hand off: W-005c `done`.** BUILD-01's review blocker is cleared — every finding fixed or dismissed-with-reasons, as the constitutional rule requires. **BUILD-01 acceptance remains the orchestrator's**, now gated only on the dated check: `python ops/fleet_green.py` on/after **2026-08-04** (⚑ #215). Note for that run: the fixes touched collector state semantics, so the 7-day window's evidence is *stronger* than before (a quarantine now actually reaches `main`), but `nhtsa-recalls` still carries its 2026-07-28 `startup_failure`, so its clean window starts 07-29. `NEXT.md` stripped of W-005c — **W-006 (NHTSA retrocast) stands.**

---

## 2026-07-29 — W-006 · NHTSA Shadow Recalls retrocast v1 — `done` · **the retrocast FAILED its pre-registered bars, and that is the deliverable**

**BUILD-03's first exercise. The flagship index does not publish.** Three of four frozen §7 bars missed on the held-out window; the fourth passed for a reason that does not count. Per the registration and the standing doctrine, no bar was moved and no model was re-tuned — the failure is published with an autopsy, a hostile-review record, and reproduction instructions.

### The scorecard (held-out 2021–2025, `results/v1/scorecard.json`)

| bar (registration §7) | required | measured | |
|---|---|---|---|
| PR-AUC vs volume-only | ≥ +0.05 absolute | **0.0280** vs **0.0331** | ✗ loses to counting complaints |
| precision at the operating point | ≥ 0.30 | **0.0190** (CI 0.0188–0.0192) | ✗ off by 16× |
| event-recall | ≥ 0.50 | **0.4221** | ✗ — and 0.4221 is the ceiling |
| median lead | ≥ 60 days | 168 d | ✓ **degenerately** — half the leads sit exactly at the 175-day window edge |

Scale: 1,206,959 complaints and 216,449 recall rows in window → **5,928,725 scored cell-weeks** over 113,761 cells, 21,093 distinct (cell, week) recall events, 7,806 in the evaluation window. ~5 min of desktop CPU per run, zero metered spend, no LLM anywhere in the signal.

### Cause of death — structural, not tunable

**57.8% of held-out recall campaigns occur in cells with no complaint at all in the preceding 26 weeks.** No model can flag an event it has no data for, so the 0.50 event-recall bar was unreachable *before a coefficient was fit* — and it is not a test-window fluke (train coverage 0.3983 vs test 0.4221). Second cause: at the maximum-likelihood fit, `rate_ratio` (−0.318) and `hazard_lang` (−0.150), the two features the registration leaned on hardest, carry **negative** weight. Self-normalizing each cell against its own history removed the only thing that predicts a recall — that it is a high-volume cell. Third: because 0.50 is unreachable on train too, the operating point collapses to "flag everything", which is why precision equals the base rate exactly and the lead-time bar "passes".

### Ordering, frozen first (SPEC-08 §2 / §7 criterion 1)

`e3d4d84` registration (2026-07-13) → `d28d8fa` **workbook freeze** (component crosswalk + 82-term hazard lexicon + interpretable rule, 2026-07-28, *before* the runner existed) → results code, **clean tree**. The run resolves the registration's commit itself, asserts it is an ancestor of HEAD, and **aborts** otherwise; the ancestry booleans are in the scorecard.

**The component-taxonomy catch fired and was frozen, not bent.** The two files do not share one vocabulary — 40 shared top levels, 13 complaints-only, 1 recalls-only, and four systems split across old/modern labels (complaints file 71,981 rows to `SERVICE BRAKES` and 7,844 to `SERVICE BRAKES, HYDRAULIC`; recalls do the reverse). Raw top-level joining would have silently broken the label join for whole systems. The crosswalk is in the workbook with the counts that force it.

### Hostile review — 6/6 zeroed, 5 findings (`HOSTILE-REVIEW-v1.md`)

Ruled out, with evidence rather than assertion, every way this could have **failed for the wrong reason**: leakage (closed windows + a planted future-complaint test + 0/200,000 label mismatches vs the harness), stale/revised vintage (one hash-pinned archived pair; the retrocast code imports no HTTP client), a flattering base rate (the scored universe runs *hotter* than the full grid — 1.90% vs 0.714% — so the precision bar was **easier**, and it still missed 16×), threshold archaeology (bars asserted equal to the registration in CI), and an under-trained model (**|grad| = 5.99e-08**, reproduced by an independent IRLS/Newton solve to 4 decimals in 9 iterations). Two findings changed what is published: the full-grid base rate is now computed and disclosed, and the matched-control column is declared **vacuous** in this run (0/7,806 controls unflagged — the collapsed threshold flags them too). One residual carried to v2: 95 of 3,295 leads (2.9%) are same-week-bucket crossings; a v2 needs a strictly-before-`t` window.

### Two corrections made before publication, both disclosed with pre-fix numbers

1. **Labels are events, not rows.** FLAT_RCL repeats each campaign across make/model/year and component sub-descriptions (74,636 rows → 21,093 distinct (cell, week) events); left as rows, event-level metrics silently weight the most-repeated cells. Registration §4 is a set test. **Pre-fix event-recall 0.3120 → post-fix 0.4221** — the fix moved the number *toward* the bar and it still fails, which is stated explicitly so it cannot read as bar-shopping.
2. **Provenance `dirty`** counted the untracked results directory the run was writing; tracked-only now.

### Machinery built or hardened

- `retrocast/nhtsa_recalls/{lexicon,features,run_v1}.py` — the freeze, the five-feature signal over closed windows with sliding sums, and the runner (hash-pinned vintages with abort-on-mismatch, train-only standardization + deterministic fit, both mandatory dumb baselines, the interpretable rule, receipts).
- **harness (SPEC-08):** `test_start` + train/test label windows implement registration §5d (horizon-spillover guard) with a backward-compatibility test proving the defaults are byte-identical; `operating_threshold_event` went O(N log N) with the brute-force version kept as `_naive` and a randomized equivalence test — **which caught a real divergence at target-recall 0**. Both landed *before* the first run.
- **sitegen:** landing the first scorecard flipped the Track Record page from "no scorecards yet" to a live PASS/FAIL table, and only the empty branch stated that the bars were pre-registered. Caught by the existing test; the populated branch now says it and states that failures stay published.
- `retrocast/requirements.txt` (numpy, retrocast-only — the collector fleet stays lean) installed by `ci.yml` so CI exercises the real fit path against its pure-Python mirror.

**Suite: 11/11, +21 tests** (nhtsa freeze 8, nhtsa v1 13). Commits `4a24a39` (freeze) → `d28d8fa` (runner) → `4c68b60`, `db81897`, `2f914c2` (corrections) → `421a9bb` (results).

### Hand off

**W-006 `done`.** SPEC-08 §7 acceptance is exercised end-to-end: registration demonstrably predates results, a planted leaked feature is caught by the checklist procedure (test), the dumb-baseline comparison is in the report, `scorecard.json` validates and the site renders from it, and the dead-registration log is no longer empty. **The ⚑ operator launch gate was NOT reached** — a failed retrocast opens no named tier, so no LLC/insurance decision is triggered. What *is* owed to the operator is filed: gate `GATE-20260729-nhtsa-v1-dead-next-move` + ⚑ **#219** — v2 pre-registration vs moving to the second retrocast, and whether The Exhaust's first public number should be its own failure. `NEXT.md` → **W-007** (BUILD-04 launch surfaces), which now inherits a real question rather than an assumed launch.

**Provenance note (2026-07-29, after push).** The hand-off rebased onto a fleet state commit the Actions runner had pushed meanwhile (`f7dd483 state(ats-boards)`), which rewrote every local W-006 hash. Because the scorecard's whole job is a checkable ordering, the run was re-executed on the rebased history and every citation refreshed to the pushed hashes: registration `e3d4d84` (2026-07-13, untouched — it predates this work) → workbook freeze `d28d8fa` → results code `2f914c2`, clean tree, ancestry re-asserted by the run. **Lesson for future workers: cite commit hashes only from history that has been pushed** — a worker rebase silently invalidates them, and a scorecard pointing at a commit nobody can `git show` is exactly the unverifiable claim this project exists to not make.

---

## 2026-07-29 — W-007 · BUILD-04 launch surfaces — `partial` (surfaces built + proven end-to-end; deploy is ⚑ #217, publish-decision is ⚑ #219)

**The archive became a set of public surfaces.** Everything here is aggregate/observational and receipts-first, so none of it depended on the failed retrocast. Two things are deliberately NOT done, because neither is a worker's call: the Cloudflare Pages deploy (credentials absent — ⚑ **#217**) and the decision to publish the full site at all (⚑ **#219**). The build is proven locally against the live R2 archive instead, and the deploy workflow is written so that it stays inert until both gates clear.

### What was built

- **`artifacts/extract.py`** — archived payload → structured WARN notices, stdlib-only, never fetching. Readers for Socrata CSV, `.xlsx` (its own minimal XML reader: shared strings, inline strings, column-letter alignment so a sparse row keeps its header alignment) and HTML tables (a nested-table stack, and `<br>` treated as real structure). Field mapping is on the **source's own header text**, most-specific-hint-first, one column claimed once.
- **`artifacts/templates.py`** — the SPEC-04 §1 "approved templates" made literal. Five sentence shapes; `render()` raises `UnapprovedTemplate` on anything else, so a new claim shape is a reviewed code change, never something a job improvises.
- **`artifacts/compile.py`** — the compiler. Walks the archive by **deterministic manifest date-keys** (so it needs nothing from the storage backend but `get`, and works identically against LocalFS in tests and R2 in production), extracts, diffs consecutive vintages, and emits `site/data/*.json` + one receipts bundle per number.
- **`sitegen`** — WARN Watch + 10 per-state pages, Postings + per-board pages, 14 receipt pages, RSS 2.0 + JSON Feed 1.1, stale-data banners wired to HEALTH, and methodology sections `#warn-watch` / `#posting-diff` that every receipt actually links.
- **`.github/workflows/site.yml`** — suite → compile → build → upload artifact → (gated) deploy. **No cron, on purpose:** a scheduled full-site publish would decide ⚑ #219 by default. `mode` defaults to `placeholder` (the page the operator already approved in W-005b); `full` must be chosen by hand. Absent Pages credentials the deploy step fails loudly naming #217 and the built site is attached to the run instead.

### Fail-closed, proven both ways

`resolver.receipts.has_valid_bundle` is the gate, in two independent places: `compile._publish` refuses to write an artifact whose bundle does not validate, and `sitegen.build.require_receipt` refuses to render one. The site build checks **every** artifact before writing **any** page, so a refused build cannot leave half a site behind — and since a deploy only replaces the live site on success, the failure mode is "yesterday's site stays up", not "a number publishes without evidence". Verified against the real archive by stripping a bundle's `inputs` and by deleting a bundle outright; both raise `UnreceiptedNumber` and write nothing (`test_an_unreceipted_number_refuses_to_render`).

### Acceptance: a WARN notice source → archive → page → feed, with receipts

Traced end-to-end on real data, not a fixture — **PD Systems, Monterey County, 81 workers, filed 2026-07-27**, appearing between two CA vintages archived 44 minutes apart (well inside one collector cycle):

| Step | Evidence |
|---|---|
| source | `edd.ca.gov/.../warn_report1.xlsx` (the state's own file) |
| archive | `raw/warn/CA/2026/07/28/1700-c9709b4ca2ce.xlsx`, sha256 `c9709b4c…c80a78`; prior vintage `1616-408de91a3928.xlsx` |
| artifact | "CA published 12 new WARN notices covering 510 workers between 2026-07-28 and 2026-07-28" |
| page | `warn/CA.html` — the notice, plus the archive key and hash it came from |
| feed | present in `feed.xml` and `feed.json`, each carrying the receipts URL |
| receipt | `receipts/warn-watch/CA-new-…html` renders **both** input hashes, `code_ref`, index version, and a live methodology link |

**Coverage against the live archive:** 8 of 10 WARN states extract into individual notices (CA 53, NY 69, TX 2,367, WA 15, IL 16, NJ 2,343, FL 100, MD 82); PA and WI publish link lists rather than tables and are labelled *"archived, not yet machine-readable"* with their snapshot and hash shown — we publish no count we cannot derive. 14 artifacts, 14 receipt bundles, 36 pages, 364 KB.

### Real defects caught and fixed while building (each with a test)

1. **A source reshaping its table would have published as mass new layoffs.** `notice_id` pins every field, so a renamed column changes every id at once and an unchanged list reads as entirely new filings. Added `extract.compare_key` (employer + source date + headcount) for the *diff*, keeping the full-field id for receipts — plus a circuit breaker: if >50% of a list differs from the previous vintage (prior list ≥10), the change figure is **withheld** and the page states that the source changed shape. `test_a_reshaped_source_does_not_publish_as_mass_new_filings`.
2. **The cross-state "most recent" list was 100% New Jersey, showing future dates.** NJ publishes no filing date, and ranking on its (deliberately future) effective dates put notices that have not happened yet at the top of a list headed "most recent". Now ranked on notice date only; undated notices stay on their state page and the count of them is disclosed.
3. **Collapsing indistinguishable rows undercounted layoffs.** NY publishes only (company, region, two dates), so two genuine notices from one employer were deduped into one. Occurrence-disambiguated ids: NY went 61 → 69, matching its source exactly.
4. **A company's legal name was being truncated.** Treating the HTML source's own line wrapping as structure turned "Taft Broadcasting, LLC" into "Taft Broadcasting," — a wrong legal name on a public page. Only tags may create a line break now; source wrapping is collapsed first.
5. **The covenant guard did not scan the publishing side.** It covered `collectors/engines/resolver` only, so a banned source *cited* by `artifacts` or `sitegen` would have passed CI green — the W-005c/F04 lesson repeating one layer downstream. Both directories are scanned now, with a regression test.
6. **An overclaim on our own home page.** The lede said every number is "validated by running history backwards", which is false of the two observational surfaces now live. The page now separates *observational* from *signature* numbers explicitly and says nothing of the second kind is published yet; a test asserts the distinction survives and that no page drifts into forward-looking language.

Also disclosed rather than hidden: rows naming no employer are counted (`unnamed_rows`) and shown as a note on the state page — one in TX, one in IL — because a notice with no employer cannot be published as a named fact but the gap must not be buried. Excel serial dates are anchored in tests against three independently-known serials (44197/45292/46023).

### Verified, not assumed

- Extraction was written against **real archived bytes pulled from R2**, not from the spec — which is how the WA nested table, the FL `</br>`, the CA index-then-summary-then-detail sheet order, and the NJ sheet-per-year layout were found at all. Taking the densest sheet would have published NJ's **2020** notices as current.
- Full suite **12/12 green** (`ci/run_all.py`, new `artifacts` step; tests 61 → 87). Placeholder mode re-verified: after a full 36-file build, `--placeholder` leaves exactly `index.html` and removes the `warn/`, `postings/` and `receipts/` trees.

### Deliberately not done

- **Cloudflare Pages deploy** — no `CLOUDFLARE_API_TOKEN`/`ACCOUNT_ID`; that is ⚑ **#217**, referenced not re-filed. No alternate host was improvised (GitHub Pages and Vercel Hobby bar commercial use — covenant 6).
- **Full-site publication** — ⚑ **#219** owns whether the first public number is our own failure. The Track Record page's FAIL table was **not** softened, moved, or hidden; the home page states plainly that the first retrocast did not clear its bars. Final launch framing follows the gate.
- **Bluesky** — stays dark; no handle exists yet, and no posting code was written.
- `site/data/` is gitignored (re-derivable from the archive on every build); `site/receipts/` is committed as the public evidence record.

### Hand off

**W-007 `partial`.** Every severable surface is built, tested and proven against live archived data; the two residuals are operator gates by design. The BUILD-04 bar of two unattended weeks is tracked by the weekly reports, not by a session. `NEXT.md` → **W-008** (Hospital/Care retrocast, BUILD-05), which is severable from both open gates.

---

## 2026-07-29 — W-007b · `cms-pbj` collector — the missing half of SPEC-01 C1 — `done`

**BUILD-01's first-priority collector was half-delivered.** SPEC-01 §2 C1 is `cms-pbj` **+** `cms-deficiencies`; only the second existed. Consequences: the roster was incomplete, and W-008's trigger ("≥2 PBJ vintages archived") could never fire because nothing produced PBJ vintages. Both are now closed.

### Re-verified live before depending on it — and research §5 pointed at the wrong catalog

The standing order earned its keep. The raw PBJ files are **not** in `data.cms.gov/provider-data`, the catalog `cms-deficiencies` uses — that one publishes staffing *ratings* (`Provider Information`, `State US Averages`) but no PBJ file. The raw releases live in the **main CMS DCAT catalog**:

| | |
|---|---|
| catalog | `https://data.cms.gov/data.json` |
| dataset | `Payroll Based Journal Daily Nurse Staffing`, `7e0d53ba-8f02-4c66-98a5-14a1c997c50d` |
| cadence | `accrualPeriodicity: R/P3M` (quarterly); `temporal: 2017-01-01/2026-03-31` |
| inventory | **37 CSV releases, 2017Q1 … 2026Q1**, one per quarter, every one still downloadable |
| shape | 33 columns; **`PROVNUM` is the CCN** that joins to `cms-deficiencies`; daily rows per facility |
| licence | `usa.gov/government-works` (public domain), no auth, no ToS gate, no CAPTCHA |

Had this been built from the spec rather than the live source, it would have been pointed at a catalog that does not carry the data.

### Why it is a fleet, not a single-file `Collector`

The NEXT.md catch fired: unlike the deficiencies CSV (one file CMS overwrites in place), PBJ publishes **a separate file per quarter and retains every one**. So quarters are archived as distinct units under `raw/cms-pbj/<QUARTER>/<Y>/<M>/<D>/`, each with its own manifest entry, and are **never concatenated** — the retrocast needs the release boundary intact. This moved registration from `collectors/run.py` (whose contract is one payload per collector) to the `_collector.yml` `entry: pbj` branch, matching the `warn` / `ats-boards` precedent. Filename convention changed three times across the archive (`CY2026Q1`, `cy_2020q4`, `PBJ_Nurse_2019_Q1_aayb`, and some releases named only by an opaque id), so quarter identity resolves from the URL where possible and otherwise from the calendar quarter of the distribution's title date — verified to agree on **37/37 releases with zero duplicates**.

### Politeness: a 234 MB quarterly file must not move on every probe

Change is detected from the catalog's per-release URL (CMS embeds a per-release UUID, so a republish yields a new path) cross-checked against a HEAD `Last-Modified`. Measured against the live source: **49 s to store, 2.3 s to dedupe.**

**The defect my own test caught, and it was the one that mattered.** The cheap check treated *absence* of a `Last-Modified` as "unchanged" and skipped the download. SPEC-01 §2 C1 says in terms that **CMS overwrites revisions**, so that would have silently lost the exact event this collector exists to catch — an in-place revision at a stable URL. The skip now requires **positive evidence of sameness** (same URL **and** a matching non-empty `Last-Modified`); no signal means fetch and let the content hash decide. `test_absent_change_signal_forces_a_fetch_rather_than_assuming_unchanged` pins it. This is the fail-closed instinct applied to collection: silence is not evidence.

### Verified against live R2 and live Actions — not asserted

| Vintage | Rows | Raw | Stored | Checks |
|---|---|---|---|---|
| 2026Q1 | 1,303,830 | 234,273,667 B | 30.4 MB | sha256 == manifest · schema re-validated **from the bytes R2 returned** · byte-identical over `archive.theexhaust.org` (`Server: cloudflare`, never `r2.dev`) |
| 2025Q4 | 1,321,304 | 237,124,313 B | 30.7 MB | stored **by Actions**, sha256 == manifest, schema valid, manifest `quarter` correct |

- **Dedupe proven against the committed baseline** locally *and* in Actions (run `30491811625`: `{'quarter': '2026Q1', 'action': 'unchanged', 'reason': 'same url and last-modified'}`, and the workflow correctly skipped the state commit).
- **Store + state-commit-back proven in Actions** (run `30491868069` → `state pushed (try 1)` → `90c39f8 state(cms-pbj): stored [skip ci]` on `main`). The first dispatch only exercised the read path, so a second was run against a different quarter to exercise the write path rather than claim it.
- Compression measured at **7.7x** across both vintages (0.47 GB raw → 61.1 MB stored).

### The full-history backfill is opt-in, and measured

`--all` archives every published release; the default archives one. **Measured 2026-07-29: 37 releases ≈ 8.7 GB raw → ~1.1 GB stored**, against a 0.79 GB archive and R2's 10 GB free tier — affordable, but not something to do ambiently. History is stable and re-fetchable; the *current* release is the perishable thing, and the floor doctrine bans ambient backfills. State exposes the gap explicitly (`published_releases: 37`, `release_count`), so a retrocast cannot quietly assume history it does not have. This is W-008's first step, with the numbers in `NEXT.md`.

### Two roster consequences, both deliberate and both flagged

1. **`fleetgreen.FLEET` now has 8 collectors.** ⚑ #215's acceptance check covers `cms-pbj` too. This was a real choice: leaving it out would have protected the 2026-08-04 date at the cost of a collector nobody is watching, which is backwards. `score()` judges an unbroken window rather than a run per day, so a quarterly source probed 2×/week is green on a dedupe firing — and its first Actions runs are already green, so **the 2026-08-04 date is not pushed**.
2. **healthchecks auto-derives an 8th check, `HC_CMS_PBJ`** (the setup script reads `collect-*.yml`, so no code change). ⚑ #212 now provisions **8**. The pinned-roster test in `test_opscore` caught the change, exactly as designed — not re-filed as a task, #212 already covers provisioning.

Also hardened the shared runner: **every fleet `entry` must map to its state filename**, and an unmapped entry now fails loudly instead of writing `ops/state/health/.json` and silently never committing state back — the W-002b failure the watchers cannot see through.

**Suite 13/13, +14 tests.** Commit `8429257`; Actions state commit `90c39f8`.

### Hand off

**W-007b `done`.** W-008's trigger is now literally satisfied — two PBJ vintages are archived — but two quarters is not a retrocast, so `NEXT.md` sends W-008 to run the `--all` backfill first, with the measured cost and the pre-registration-before-results ordering restated. Candidate noted, not worked: the shared state-commit message renders a blank hash for fleet collectors (`state(cms-pbj): stored  [skip ci]`), because fleets keep hashes per unit rather than at the node — cosmetic, pre-existing, and shared with `warn`/`ats-boards`.

---

## W-008 — Hospital/Care Distress retrocast (BUILD-05) · `done` 2026-07-30 · **the retrocast FAILED its pre-registered bars, and the failure is the deliverable**

The second retrocast ran, and like the first it did not clear its gate. It is published with an
autopsy. Commits `d6b78c3` (registration freeze) → `6edf064` (runner + backfill) → `66d1815`
(hostile-review fix) → `ecb1de7` (results + report). Suite **15/15, +30 tests**.

### The verdict

Held out 2025-03-24 … 2025-09-22: **369,750 scored cell-weeks, 4,643 harm-citation events,
14,314 facilities.**

| bar (registration §7) | required | measured | |
|---|---|---|---|
| PR-AUC vs the better dumb baseline | ≥ +0.05 | **0.1771 vs 0.2526** | ✗ |
| precision at the operating point | ≥ 0.35 | **0.1794** (base rate 0.1357) | ✗ |
| event-recall | ≥ 0.50 | **0.4605** (ceiling 0.9468) | ✗ |
| median lead, and not degenerate | ≥ 60 d | **154 d**, 43.3% at the edge | ✓ |

**Cause of death: a facility's own citation history ranks better than any staffing measure.** The
pre-registered hard baseline — prior harm citations per observed year, i.e. "troubled homes stay
troubled" — scores PR-AUC 0.2526 against the nine-feature signature's 0.1771. Two qualifications
are published alongside it, because the bald statement overstates the baseline: it wins on
**ranking only** (its own precision is 0.1357, *exactly* the base rate — it flags nearly
everything), so neither model reaches a usable operating point; and the signature beats plain
staffing level by just **+0.0045** (0.1726 → 0.1771). The instability and deterioration terms the
whole registration was built around — weekend drop, day-to-day variability, days below the CMS
3.48 HPRD minimum — fit to coefficients of −0.003, +0.001 and +0.005. **No bar moved, no re-tune.**

**This failed differently from NHTSA v1, and that distinction is the finding.** NHTSA died
structurally: 57.8% of its events were unreachable before a coefficient was fit. Here nothing was
unreachable — 94.7% of held-out events had a scored pre-window, the operating point *transferred*
(train event-recall 0.5000 exactly, test 0.4605), calibration is monotone across all ten deciles,
matched controls are valid (55.0% of 523,787 did not cross), and every meaningful coefficient
points the direction the literature predicts (`hprd_total` −0.342 strongest, `contract_frac`
+0.119). The model works. It is simply beaten by a one-column baseline.

### Establishing what ground truth actually exists — the step that decided the design

The work order said to check the archive before designing anything around it. Doing so changed the
whole study window. CMS's Health Citations file spans survey dates 2017-03-23 → 2026-05-20, but
that is **not** nine years of history: CMS retains ~**three inspection cycles per facility**, so the
file is censored at both ends and **the left censoring is not random — a frequently-surveyed
facility has a *shorter* observed history, and frequently-surveyed facilities are the troubled
ones.** Pre-2023 the file holds ~1 cited survey per facility per year across a minority of
facilities; from 2023, 1.7–2.3. Scoring pre-2024 labels would have under-labelled precisely the
facilities the index is about and **manufactured a failure that had nothing to do with staffing.**
Window fixed at 2024-01-01 … 2026-03-31 (92.4% facility coverage at the start; the last month is
2% reported and was dropped with the one before it), plus a per-facility 182-day observation
requirement. That is what caps the study at 40 train / 27 test weeks.

### The leak control with no NHTSA analogue

Complaints publish daily; PBJ does not. Quarter *Q* is usable only from **Q_end + 135 days** —
without it the run would assume knowledge ~3 months before it was public and every lead-time number
would be fiction. **Verified, not asserted:** CMS embeds the publication month in each download URL,
the run checks all 16 archived releases against it and **aborts** if the rule would permit an early
read. All 16 pass. Realised consequence: over the 2,424 held-out cell-weeks sharing a week with a
harm survey, the staffing quarter had ended a minimum of **139 days** earlier — which is what turns
the harness's "5 leads ≤ 0" flag from a worry into a week-bucket artefact, answered with arithmetic.

### The hostile review found a real defect in the shared credibility engine

**6/6 zeroed, 5 findings.** The one that matters: SPEC-08 §7 criterion 2 requires a planted leak to
be caught, and **it was not**. Planting the cell label itself gives precision 1.0000 against a 13.6%
base rate, and `leakage_scan` returned an empty list — a binary oracle's PR-AUC is low (two-point
curve), and a horizon-based label makes an oracle *lead* the event rather than coincide with it, so
neither existing rule fired. Both rules are about the score's *shape*; precision against the base
rate is not, so it survives either plant. Now a fourth rule, with both plant shapes under regression
test. NHTSA v1's flags are unchanged (precision 0.0190) — the guard only got stricter. Two existing
fixtures started failing and **correctly**: both built "honest" signals that were perfect oracles.
They now carry realistic false positives *inside the held-out split* (the first attempt put them in
train, where they cannot move test precision). Weakening the guard to keep old fixtures green would
have been the wrong repair.

Also disclosed: base rate both ways, and the exclusions cut **against** us (scored 0.135651 vs full
grid 0.136587) — the opposite direction from NHTSA v1, stated either way because which way it cuts
is not the publisher's to choose after the fact. Under-training ruled out (refit to gradient norm
2.19e-16 changes nothing to four decimals; independent IRLS agrees). **The pre-committed lead-time
degeneracy rule did NOT fire** (43.3% at the edge, under the 50% bar) — which is the only reason it
is credible rather than a device for forcing a fail.

### The PBJ backfill, and the two consequences it caused

`--all` moved all 37 published releases. **24 stored + 2 already current; 11 QUARANTINED on schema
drift** — 2017Q1–Q4, 2018Q4, 2019Q1–Q4, 2020Q2–Q3 use lowercase headers (`provnum`, `mdscensus`)
plus three genuinely different names (`hrs_rn_donadmin`, `hrs_lpn_admin`, `hrs_na_trn`). **Not a
clean cutover**: 2018Q1–Q3 and 2020Q1 are TitleCase and stored fine, so CMS re-published some
quarters and not others. The collector behaved exactly as designed — quarantine + alarm, `raw/`
clean, bytes archived under `quarantine/cms-pbj/` (351 MB, hashed), nothing lost. Not fixed: scope
is law, and the retrocast reads 2022Q2+. Archive now 1.9 GB against R2's 10 GB free tier.

1. **⚑ #215 was put at risk and then restored, provably.** The backfill left node-level
   `last_action: "quarantined"`, which is the exact field `ops/fleet_green.py` reads. A dispatched
   Actions run recomputed `unchanged` but **did not persist it**: `_collector.yml` skips the state
   commit on a dedupe, so a stale quarantine flag can only be cleared by a run that *stores*
   something — and PBJ stores quarterly, so it would have sat on the acceptance check until
   ~2026-09-30. Cleared by running the collector in its **normal `--quarters 1` scope** and
   committing the true result, not by hand-editing state. `fleet_green` now reports **cms-pbj
   GREEN, 7/8**; the remaining blemish is the pre-existing `nhtsa-recalls` 07-28 failure, which ages
   out of the window before 08-04. **This is the mirror of W-005c/F02** — there a *failure* could
   not reach committed state; here a *recovery* cannot. Filed as a candidate, not fixed:
   `_collector.yml` is shared by all 8 collectors.
2. **`release_count` no longer warns.** It reads 37 of 37 published, but 11 of those are in
   quarantine rather than `raw/`. W-007b built that counter pair precisely so a retrocast could not
   assume history it does not have, and after this backfill only the per-quarter records carry the
   warning. Candidate filed.

### Three defects found by running it, none by reading it

Each would have quietly moved a published number: the **test label window reached one week past the
furthest any cell horizon can reach** (~0.7% of held-out events booked as misses no threshold could
catch — fixed before the first successful run, so no published number ever carried it);
**facility-quarters reporting a census with zero weekday nursing hours** make `weekend_gap`
undefined rather than zero (drop-and-count, as the workbook prescribes for an inadmissible quarter);
and **one trailing short row per release** (skipped and counted, 3 total, so a real width change
surfaces as a number rather than silence).

### Site

Both scorecards render as FAIL rows and both pre-registrations list. Two accuracy fixes on surfaces
this change touches, neither a ⚑ #219 framing decision: the home page said *"the first retrocast"*
when there are now two, and PR-AUC was publishing with **17 significant figures** (raw value stays
in `scorecard.json`; regression test added). The FAIL rows were not softened, moved, or hidden.

### Hand off

**W-008 `done`.** Not worked, by design: the **county-level care-fragility aggregate page** from
gameplan §6 BUILD-05. W-008's stated acceptance is the retrocast, and publishing a "care-fragility
index" off a retrocast that failed its bars would be exactly the overclaim the gate exists to
prevent; the observational county-staffing surface is severable and is a WORKPLAN candidate.
**⚑ This item was worked out of order, and the cause is a process gap worth closing.** The
orchestrator re-pointed `ops/state/NEXT.md` to **W-007c ONLY** in commit `d986118` on 2026-07-30.
This session read `NEXT.md` at start-up **without fetching first**, so its checkout still held the
W-007b hand-off ordering W-008, and it executed W-008. There was no queue conflict — the queue was
correct and the worker was stale. W-008 is delivered, green and severable, and **W-007c remains
outstanding and is now `NEXT.md`'s only item.** One incidental consequence: review finding **G10**
warned that the `--all` backfill W-008 needs is non-resumable and should be fixed first; the
backfill ran to completion, so the risk did not materialise, but it ran unprotected. **Recommended
for BUILD-PROTOCOL §2: `git fetch && git pull --rebase` as a required first step, before reading the
work order.** A stale work order is indistinguishable from a correct one from inside the session.
Also unchanged from W-006: the independent hostile-review confirmation that the orchestrator made a
publish precondition applies here too — this review was written in-session.

## 2026-07-30 — W-007c · BUILD-04 adversarial-review fixes — `done` (21/21 dispositioned)

The BUILD-04 publish-path review + the independent SPEC-08 §5 hostile confirmation of the NHTSA v1
failure returned **21 confirmed findings (1 CRITICAL / 3 HIGH / 10 MEDIUM / 7 LOW)**, and BUILD-04
cannot be accepted until each has a disposition. **All 21 are dispositioned and all 21 are fixed**,
every one with a regression test or a committed artifact correction. Hardening and transparency
only: **no bar moved, no metric changed, no retrocast was re-run**, and nothing was deployed.

The shape of the finding set is worth stating plainly, because it is the same shape twice. The
publish path was fail-closed on the thing it was designed to guard (a number with no receipts
bundle) and fail-**open** on every way the layer *underneath* that check could break: a corrupt
`artifacts.json` was read as "no artifacts", a corrupt `scorecard.json` as "no scorecard", a
damaged health file as "no health state". Each of those silently converted a broken input into a
clean-looking page. The through-line of this session's fixes is a single rule — **absent is a
state, broken is a refusal** — now expressed as a `RefusedBuild` exception family that aborts the
build rather than publishing around the damage.

### Disposition table

| # | Sev | Finding | Disposition |
|---|---|---|---|
| G01 | **CRITICAL** | Receipts gate keyed entirely off `artifacts.json`; `_load` swallowed parse errors, so a missing/corrupt derived file rendered every notice table and diff count with **zero receipts on disk**, build green | **FIXED** — `_load` is strict (absent → default, exists-but-unparseable → `DerivedLayerError`), plus `_check_derived_layer`: the three `site/data` files must be present together, carry the same `(generated, code_ref)` stamp, and every non-zero derived count must have its artifact in the receipt-checked set. Tests: the reviewer's two repros (delete `artifacts.json` + `receipts/`; merge-conflict junk), a stamp mismatch, and a state whose count has no artifact |
| G02 | HIGH | `require_receipt` checked only that a bundle existed and was internally complete — never that the rendered claim matched it, so a number inflated 10× rendered directly above the un-inflated bundle table | **FIXED** — `require_receipt` loads the bundle and asserts `number`/`unit`/`as_of`/`index_version` agree, and that an integer claim's own number appears in the sentence being published. `compile_all` now writes the three JSONs to temp files and `os.replace`s them after every publish, so the torn state is far harder to reach in the first place. 4 assertions, one per contradiction |
| G03 | HIGH | `run_fleet` pinged the healthcheck **success** on runs whose only results were `paused` or `quarantined-dup` — the collector reported alive while collecting nothing, forever | **FIXED** — a run that stored nothing and carries a pause or a dup **withholds** the ping (`withheld(paused)` / `withheld(drift)`, the framework `Collector`'s own precedent), so the check's grace window fires. Test drives both states against a dead HC URL and asserts the ping was never attempted |
| G04 | HIGH | `_scorecards` did `except Exception: pass`, so a truncated `scorecard.json` erased a published **FAIL** from the Track Record with a green build — while the home page kept saying the failure is published there | **FIXED** — a scorecard that exists and does not parse raises `CorruptScorecard` and aborts the build. Tests: truncated card refuses; the real repo build asserts both FAIL rows, their PR-AUCs, and both evidence links |
| G05 | MED | The anti-storm dup branch never incremented `fail_streak`, so "3 drifts → auto-pause + gate" could **never** fire for this collector's own threat model (CMS overwrites in place ⇒ a persistent drift presents identical bytes forever) | **FIXED** — the dup branch calls `_quarantine(rec, "quarantined-dup")`: counted, still no re-store and no re-alarm. Test: 3 identical drifted probes ⇒ `fail_streak==3`, `paused`, exactly one gate, exactly one quarantined object |
| G06 | MED | `fleetgreen.score()` saw only node-level `paused`; cms-pbj pauses at the **quarter** level and publishes only `paused_quarters`, so a paused quarter went invisible once any later run committed a different `last_action` — the ⚑ #215 criterion could close leniently | **FIXED**, and fixed for the whole fleet rather than just cms-pbj: `paused_units()` reads `paused` **and** `paused_quarters`/`paused_states`/`paused_boards`, and `fleet_green.py` prints which unit is paused. Test covers all three fleets, both directions. Deliberately **not** done: setting a node-level `paused` from `run_fleet`, because `Collector.run()` reads that same key to refuse to fetch, and a paused quarter must not halt the other 36 |
| G07 | MED | The scorecard render path had no validation gate: the "pre-registered and frozen in public" banner was asserted with zero machine verification, and a `pass` of `"false"` (a string) would render a green **PASS** | **FIXED** — `_validate_scorecard` refuses a card missing required keys, with `provenance.dirty`, with `registration_is_ancestor_of_code: false`, with a non-bool `pass`, whose `pass` contradicts `pass_detail`, or whose index has no discovered pre-registration. `pass_detail` reduction knows `lead_degenerate` is a **negated** key (hospital-care appends it after `pass` is computed), so a legitimately passing card is not called inconsistent. Tripwire test loads both committed cards against the frozen `lexicon.BARS`/`spec.BARS` and their vintage pins. Both current cards pass every check — purely additive |
| G08 | MED | Third-party board URLs went into `href` with `html.escape` only, which does not neutralise `javascript:`/`data:` | **FIXED** — `_safe_href`/`_safe_link`: an anchor only for `http(s)`, otherwise plain text (and, for a source URL, an honest "link withheld" note showing the raw value). Applied at all three sites. Test archives a `javascript:` payload end-to-end and asserts the title still renders and the scheme reaches no attribute |
| G09 | MED | Two distributions claiming one quarter resolved **first-wins** into a `duplicates` key no caller read, and the URL-derived quarter was never cross-checked against the title-derived one | **FIXED** — `resolve_releases(anomalies=[])` records `duplicate-quarter` and `quarter-disagreement`; a disagreement **skips** the release rather than mis-filing it (PBJ history is retained and re-fetchable, so a deferred release is delayed, never lost, whereas wrong bytes under a real quarter's key corrupt the release boundary BUILD-05 reads). `run_fleet` surfaces `ambiguous_quarters` in committed state and exits nonzero. Test covers both kinds plus the state/exit path |
| G10 | MED | Health was dumped once after the whole fleet loop, and `KeyboardInterrupt` is not an `Exception` — a killed `--all` persisted **nothing**, so the rerun re-downloaded every release and re-stored byte-identical snapshots | **FIXED** — atomic `persist()` after **every** release, plus a `BaseException` handler that persists and re-raises (recording `last_interrupt`). Second belt: when local state has no baseline, today's **manifest** is the authority — matching bytes read as `unchanged` instead of creating a spurious second vintage. Test kills a 5-release backfill at 3, asserts the rerun re-fetches exactly 2, then deletes the ledger outright and asserts 0 stores and no duplicate manifest hash |
| G11 | MED | `BUDGET.json`'s own `re_project_trigger` ("any collector added to the roster") fired at W-007b and was not executed — the ledger omitted the newest and second-largest storage line | **FIXED** with a real measured sweep, not an estimate: new `ops/storage_sweep.py` (read-only `list_objects_v2`, `--write` updates the ledger) so the trigger is executable in one command instead of by hand. Archive measured **2.1766 GB / 160 objects**; `raw/cms-pbj` 809.5 MB is now the second line, `quarantine/cms-pbj` 350.9 MB the third. Growth re-based to 21.15 GB/yr; free tier ~2026-12; the $5/mo bar still ~16 years. Fired triggers are now recorded as **closed** in `triggers_executed` |
| G12 | MED | Track Record rows carried no link to any evidence, never surfaced `leakage_flags` or failing `pass_detail`, and printed raw floats | **FIXED** — every row links its `results/<version>/` directory and its `REPORT.md`, and a caveat row under it names the bars missed and every leakage flag. (Float formatting was already fixed by W-008's `_num`.) Verified on the real build: 2 FAIL rows, 2 scorecard links, 2 autopsy links, both leakage flags rendered |
| G13 | MED | The headline autopsy claim ("57.8% … no complaint at all in the preceding 26 weeks") misdescribed its own computation on three axes and would not reproduce as worded | **FIXED (wording; the number is unchanged)** — restated in `REPORT.md` §3.1, the `HOSTILE-REVIEW-v1.md` Verdict and `DEAD-REGISTRATIONS.md` as *joined (cell, week) events, window ending at **and including** the report week, a **floor** not a point estimate*, with all three biases named and the strictly-leading figure (59.0%, = 3,295 − 95 non-positive leads) given. Each edit carries the pre-fix wording inline. `run_v1.py` now emits `test_events_with_strict_pre_window_activity` so a future run states it without arithmetic |
| G14 | MED | The hostile-review preamble claimed "results were already written and committed before this review began", but git shows the review, the report and `results/v1/*` all first landed in `421a9bb` | **FIXED (preamble; no finding or disposition changes)** — restated to the strength the record supports: the ordering is a session-internal claim git **cannot** corroborate, and what history *does* show is that `git diff 421a9bb e182fcc -- results/v1/scorecard.json` touches only `generated` and four provenance fields — every metric, bar, `pass_detail`, comparator and diagnostic byte-identical. Practice going forward: commit results **before** starting the hostile-review pass |
| G15 | LOW | `health_banner` swallowed everything and `merged_health` silently skipped unreadable health files, so a corrupt state file produced **no** stale banner — the disclosure chain failed open exactly when state was damaged | **FIXED** — `merged_health` returns an `unreadable` map instead of dropping; `health_banner` renders "**Freshness cannot be verified**" for a damaged file while absent state still (correctly) renders nothing. Tests both sides |
| G16 | LOW | `_rfc822` fell back to `datetime.now()` — the docstring called it "a small lie" — and `json_feed` emitted `T00:00:00Z` for a blank `as_of`; the empty feed was never validated | **FIXED** — an item with no parseable vintage raises `UndatedArtifact`; `now()` survives **only** as the channel `lastBuildDate` with zero artifacts, where it is a true build-time fact. Test parses `rss([])` and `json.loads(json_feed([]))` and asserts both refuse an undated artifact |
| G17 | LOW | "*N* states archived" counted seeded states with no snapshot at all, contradicting the page's own per-row "no snapshot in window" cells | **FIXED** — counts states with vintages and names the seeded-but-unsnapshotted remainder separately. Test adds a seeded state and pins both numbers |
| G18 | LOW | `workflow_dispatch` inputs interpolated raw into the run shell (`python -m collectors.cms_pbj ${{ inputs.args }}`) in a job holding `R2_SECRET_ACCESS_KEY` and a `contents:write` token | **FIXED** — `entry`/`target`/`args` reach the shell only as env vars (`$PBJ_ARGS` still word-splits, which is wanted, but cannot inject syntax), in **both** steps; the state-filename branch additionally rejects any name outside `[a-z0-9-]` before it is used as a path. **Proven in Actions, not just parsed**: `_collector.yml` is shared by all 8 collectors and a green local suite cannot exercise a workflow, so `collect-fdic-failures` (the smallest, most idempotent caller) was dispatched at `3a2ca59` — [run 30535200158](https://github.com/mlawsonking/theexhaust/actions/runs/30535200158), success, with **Collect (run fdic-failures)** and **Persist collector state (W-002b)** both green through the new indirection |
| G19 | LOW | The cited "workbook freeze" `d28d8fa` is the **runner** commit; the true freeze is `4a24a39`, and the hand-off rebase rewrote committer dates so the scorecard and the report disagree by a day | **FIXED (citation; ordering unaffected)** — `REPORT.md` cites `4a24a39` (authored 2026-07-28 23:10 −0500) and explains inline both why `scorecard.json` says `d28d8fa` (`provenance()` computes `git log -1 -- <frozen module>`, i.e. **last touched**, and the runner commit added 8 lines to `lexicon.py`) and why the dates differ (rebase rewrites committer, not author, timestamps). `provenance()` now records author dates and the module's **first** commit alongside the last-touched one |
| G20 | LOW | Two load-bearing figures rest on computations in no published artifact: train coverage 0.3983 and the independent IRLS/Newton solve | **FIXED (half in the pipeline, half as disclosure)** — `run_v1.py` now emits `train_events_with_any_pre_window_activity` and `train_event_recall_ceiling`, symmetric with the test side, so a future run publishes the coverage figure. The v1 scorecard is **not** being regenerated to add it: re-running to produce a nicer artifact is precisely what a pre-registration forbids. Both figures are marked in `REPORT.md` §3.1/§4, `HOSTILE-REVIEW-v1.md` §5 and `DEAD-REGISTRATIONS.md` as session-side checks not emitted by the pipeline; `train_grad_norm` **is** published and is the reproducible half of the under-training claim |
| G21 | LOW | The paused branch of `health_banner` ("Partial coverage") had zero test coverage | **FIXED** — fresh `last_success` + `paused_states: ["WA"]` ⇒ the banner appears on `warn.html` and on the state pages, asserted through a real rebuild |
| — | (dismissed by the review) | The "vacuous assert" at `collectors/tests/test_cms_pbj.py:236` | **Dismissal upheld** — the `os.walk` on the following lines does catch a manifest written for a drifted release, so the claimed coverage hole is unreachable. The dead `or True` line is deleted as the trivial cleanup the synthesis recommended |

### Evidence

Full suite **15/15 green**; tests **+18** (sitegen 13 → 26, cms-pbj 14 → 18, opscore 30 → 31).

Refusals demonstrated end-to-end against a **copy of live repo state**, not a synthetic fixture —
baseline builds 37 pages with 2 FAIL rows, 2 scorecard links and 2 autopsy links, then:

```
(1) truncated nhtsa scorecard.json        REFUSED [CorruptScorecard]   site left behind: nothing
(2) artifacts.json + receipts/ deleted    REFUSED [DerivedLayerError]  site left behind: nothing
(3) merge-conflict junk in artifacts.json REFUSED [DerivedLayerError]  site left behind: nothing
(4) warn-watch/WA-level claims 150 vs 15  REFUSED [UnreceiptedNumber]  site left behind: nothing
```

The one change a local suite **cannot** verify — `_collector.yml`, shared by all 8 collectors — was
proven by a real dispatched run rather than left at "should work": `collect-fdic-failures` at
`3a2ca59`, [run 30535200158](https://github.com/mlawsonking/theexhaust/actions/runs/30535200158),
every step green including both rewritten shell steps. CI on the pushed head is green.

⚑ **#215 acceptance evidence is unchanged and still on track**: `python ops/fleet_green.py` reports
**7/8 GREEN** and exits 1, with `nhtsa-recalls` the sole laggard on its long-fixed **2026-07-28**
`startup_failure`, which ages out of the window before **2026-08-04**. `cms-pbj` reads GREEN; no
collector carries a paused unit, so G06 is additive against current state rather than a re-verdict.

### Candidates raised (recorded here and in WORKPLAN; **not** worked — scope is law)

1. **Hospital/Care carries the identical G20 defect.** `hospital-care/HOSTILE-REVIEW-v1.md` §5 and
   `DEAD-REGISTRATIONS.md` both assert an independent Newton/IRLS solve that `hospital_care/run_v1.py`
   does not emit. This item's scope is the **NHTSA** artifact corrections, and the independent
   hostile confirmation of the Hospital/Care failure is explicitly owed and is the orchestrator's —
   so it is raised, not quietly fixed on a sibling artifact.
2. **A recovery still cannot reach committed state** (W-008's candidate, now load-bearing for G10):
   `_collector.yml` skips the state commit when `last_action == "unchanged"`, and G10's
   manifest-authority path deliberately reports `unchanged` on a rerun after a lost ledger — so the
   recovered baseline lands on disk in the runner and not in `main`. The mirror of W-005c/F02, and
   `_collector.yml` is shared by all 8 collectors.
3. **The gate slug names the wrong cause.** `_fleet_gate` emits `cms-pbj-fetch-3x-<Q>`, but after
   G05 a *drift* pause reaches it too, so an operator can be handed a filename saying "fetch"
   about a schema problem.
4. Unchanged from W-008: the **11 quarantined legacy-header PBJ releases** (recoverable from
   already-archived bytes), `release_count` no longer signalling the archive gap, and the severable
   county-level observational staffing surface.

### Hand off

**W-007c `done` — 21/21 dispositioned, suite green, nothing deployed.** The ⚑ #219 standing
decision was not pre-empted: `site.yml` still has no cron and still defaults to `placeholder`, and
**both** FAIL scorecards were not softened, moved, or hidden — they now carry *more* disclosure
(missed bars, leakage flags, evidence links) than before. Every NHTSA artifact correction publishes
with its pre-fix wording inline, and no result, bar, or metric moved anywhere in the repo.
BUILD-04 acceptance is the orchestrator's, as is the independent adversarial-review pass over these
fixes. Next worker: see `ops/state/NEXT.md`.
