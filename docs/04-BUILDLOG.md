# 04-BUILDLOG — The Exhaust, Phase 4 implementation

*Opus, opened 2026-07-11. Predecessors: [`01-VISION`](01-VISION.md) · [`02-RESEARCH`](02-RESEARCH.md) · [`03-GAMEPLAN`](03-GAMEPLAN.md). Contracts: [`ops/SPEC-01…09`](../ops/).*

The multi-session build log (OnScript pattern). Standing orders (gameplan §0): **build exactly what the specs say · archival first · re-verify before you depend · the covenants are code review**. One BUILD item at a time, to acceptance, verified, committed, logged here.

---

## BUILD status

| Item | Scope | Status |
|---|---|---|
| **BUILD-00** | Foundations (repo, state layer, R2, healthchecks, ntfy, secrets) | **Opus scaffolding DONE; acceptance BLOCKED on operator errands ⚑ — tracked in Vikunja (board `observatory`, #9–#13)** |
| BUILD-01 | Archival fleet v1 (collectors → R2) | queued (blocked on BUILD-00 infra) |
| BUILD-02 | Ops core (state, alarms, gates, budget, gate-report, weekly session) | queued |
| BUILD-03 | Retrocast harness + NHTSA retrocast (⚑ LLC + insurance gate) | queued |
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
