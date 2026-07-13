# 04-BUILDLOG — The Exhaust, Phase 4 implementation

*Opus, opened 2026-07-11. Predecessors: [`01-VISION`](01-VISION.md) · [`02-RESEARCH`](02-RESEARCH.md) · [`03-GAMEPLAN`](03-GAMEPLAN.md). Contracts: [`ops/SPEC-01…09`](../ops/).*

The multi-session build log (OnScript pattern). Standing orders (gameplan §0): **build exactly what the specs say · archival first · re-verify before you depend · the covenants are code review**. One BUILD item at a time, to acceptance, verified, committed, logged here.

---

## BUILD status

| Item | Scope | Status |
|---|---|---|
| **BUILD-00** | Foundations (repo, state layer, R2, healthchecks, ntfy, secrets) | **Opus scaffolding DONE; acceptance BLOCKED on operator errands ⚑ — tracked in Vikunja (board `observatory`, #9–#13)** |
| BUILD-01 | Archival fleet v1 (collectors → R2) | **in progress** — C1 + C5 + **C4 nhtsa-recalls** + **C9 fdic-failures** live-verified (6 collectors, 3 schema types); nhtsa-complaints built + HEAD-verified (367 MB deferred to Actions); C6/C8/C10/C11 next; R2 deploy + fleet-green pending BUILD-00 |
| BUILD-02 | Ops core (state, alarms, gates, budget, gate-report, weekly session) | **built & tested** — gates + budget + orphan + report + **alarm/ntfy bus** + **weekly-ops driver** + playbooks (17 tests); live ntfy/heartbeat delivery inert until BUILD-00 topics exist |
| BUILD-03 | Retrocast harness + NHTSA retrocast (⚑ LLC + insurance gate) | **pre-registration FROZEN** + **harness code built & tested** (`retrocast/harness.py`; synthetic: dumb-baseline beaten, planted-leak caught, scorecard validates); NHTSA run pending C4 archive + LLC/insurance gate |
| BUILD-04 | Public launch (site, WARN Watch, posting-diffs, Bluesky) | queued |
| BUILD-05 | Hospital/Care retrocast | queued |
| BUILD-06 | Workbook compiler v1 | queued |
| BUILD-07 | Legislative Authorship + FOIA micro (Q1 2027, session-timed) | queued |
| BUILD-08 | Grocery forward pilot + shrinkflation retrocast (Q2 2027) | queued |
| BUILD-09 | Say-Do pilot (Q2 2027) | queued |
| BUILD-10 | Track Record page, bank aggregate, first 311 city, mortality groundwork (Q3 2027) | queued |

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
