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
