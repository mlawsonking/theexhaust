# WORKPLAN — the build-grind queue

*Maintained by the ORCHESTRATOR; consumed one item at a time by WORKER sessions via `NEXT.md` (see [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md)). Items are session-sized. Work strictly top-down unless NEXT.md says otherwise. Every item: scope → read-list → build → accept → catches/fallbacks. Status vocab: `queued | next | in-progress | done(commit) | partial | blocked(reason)`.*

*Ordering doctrine: deploy-and-verify before new construction (the archive clock is the scarcest resource); flagship retrocast before launch surfaces; launch surfaces before expansion. Gameplan §6 acceptance criteria govern; this plan slices them into sessions.*

---

## Phase A — light the machine (immediately after operator BUILD-00 errands)

### W-000 · BUILD-00 acceptance gatecheck — `done` (2026-07-27, in commit at hand-off)
**Scope:** verify the five operator errands actually completed; wire nothing yet.
**Read:** `docs/03-GAMEPLAN.md` §6 BUILD-00 only; `ops/SPEC-02` §1.
**Do:** check git remote exists + push works; `ci` Action ran green on GitHub; R2 credentials present as Actions secrets AND usable (list bucket via boto3 locally with env creds); custom domain on the bucket serves an object; ntfy topics reachable (send a test to each; operator confirms phone receipt out-of-band); healthchecks project exists.
**Accept:** all five confirmed in the buildlog with evidence, or a precise per-item failure report.
**Catch:** any missing piece → report EXACTLY which Vikunja task (#9–13) is incomplete and in what way; STOP. Do not partially wire.
**Result (2026-07-27, precise stop):** **all five failed/unverifiable — none complete.** #9 repo: no git remote, `gh` confirms `theexhaust` does not exist on GitHub → no push, `ci` never ran there. #10 R2 bucket+custom domain: no creds, no bucket, untestable. #13 Actions secrets: unset locally + unverifiable (no repo). #12 ntfy: topic names not available to the session, no phone confirmation → not passed. #11 healthchecks: no ping URL/evidence. Suite re-run green (0 failures). NOTHING wired. Evidence in buildlog 2026-07-27. **`NEXT.md` stays W-000** — re-run this gatecheck once the operator reports #9–13 done; do NOT advance to W-001 until it passes.

### W-001 · R2 backend live + restore drill — `next`
**Scope:** the fleet writes to real R2; prove restore.
**Read:** `collectors/framework.py`, `collectors/run.py`, `ops/SPEC-01` §3/§6.
**Do:** `pip install boto3` (and add to CI install); run each of the 6 verified collectors once against R2 (`--verify` off, env creds); restore drill per SPEC-01 §6 (pull yesterday's snapshot via the custom domain, revalidate schema, match manifest hash); update `BUDGET.json` storage figures; add `ci/run_all.py` (runs the §5 suite, exits nonzero on any failure) and switch CI to it.
**Accept:** 6 collectors stored-or-unchanged against R2; restore drill passes; suite green.
**Catches:** R2 auth fails → re-check secret names (SPEC-02 env contract) before touching code; a collector fails live → its per-collector quarantine/pause semantics are the fallback, never edit-and-hope; datacenter-403 → the SPEC-01 §4.5 ladder (log the switch if operator-box fallback used).

### W-002 · Actions cron fleet + the 367 MB complaints pull — `queued`
**Scope:** collectors run scheduled in R1 with cron-drift defenses; first full `nhtsa-complaints` vintage archived.
**Read:** `ops/SPEC-02` §1, `.github/workflows/ci.yml` as pattern, `collectors/nhtsa.py`.
**Do:** one workflow per collector (or grouped ≤3 where cadence matches): odd-minute schedules, 2–4× over-scheduling, `workflow_dispatch`, per-collector concurrency groups, heartbeat env wiring; a dedicated workflow runs `nhtsa-complaints` full pull (chunk under 6-hr cap; it's one file — fine); confirm dedupe logs on the second firing.
**Accept:** every enabled collector has ≥1 green scheduled run in Actions; complaints vintage (51-field, ~500k+ rows) in R2 with manifest; heartbeats pinged (visible in healthchecks).
**Catches:** complaints download flaky in Actions → retry once, else run from operator box at identical politeness and note it; cron doesn't fire (drift) → `workflow_dispatch` manually this session, the heartbeat grace windows are the systemic answer; row count wildly off layout → ZipTabSchema quarantines it — file the gate, don't "fix" the schema to make it pass.

### W-003 · Alarms + weekly session live — `queued`
**Scope:** the watching layer stops being inert.
**Read:** `opscore/alarms.py`, `opscore/weekly.py`, `ops/SPEC-03`, `ops/playbooks/weekly-ops.md`.
**Do:** healthchecks checks created per SPEC-03 §1 budget (≤18 collector/logical, grace = cadence × over-schedule); ntfy topics into local env + Actions secrets; kill-one-collector drill (SPEC-03 §6: disable a firing, confirm healthchecks→ntfy alarm within grace); schedule the weekly R2 session (Windows Task Scheduler → `claude -p` per SPEC-02 §2); run `python -m opscore.weekly` once for real and confirm the pulse lands on the phone; wire the futility-clause auto-gate (2027-12-31 from `CALENDAR.md`) into the weekly driver + a test.
**Accept:** SPEC-03 §6 drill items pass; one real weekly report compiled + pulsed; futility wiring tested offline.
**Catches:** ntfy delivery fails → topics are the only auth, regenerate + update secrets (operator ping via Vikunja if his action needed); healthchecks free-tier limits hit → group per §1 budget, never drop outcome-based pings.

## Phase B — the ground truths at scale

### W-004 · C2 WARN, tranche 1 (top-10 states) — `queued`
**Scope:** the WARN Watch corpus begins; heterogeneous per-state adapters.
**Read:** `ops/SPEC-01` C2 row, `docs/02-RESEARCH.md` §3-① WARN paragraph ONLY, `collectors/cms_deficiencies.py` as adapter pattern.
**Do:** per-state collectors for CA, NY, TX, WA, IL + 5 more by volume; **primary state sources only** (aggregators are cross-checks, not sources — covenant); per-state schema contracts (PDF states → store raw + parse what's parseable; parsing completeness is per-state metadata, not a gate); shared `warn` logical heartbeat.
**Accept:** 10 states archiving on schedule; ≥1 real notice visible end-to-end in a stored snapshot; suite green.
**Catches:** a state portal blocks datacenter IPs → 403 ladder step (b) operator box, log it; a state is JS-walled or CAPTCHA'd → STOP that state, gate item, continue the other nine (never burn a session on one state); format drifts mid-tranche → quarantine semantics already handle it.

### W-005 · Fleet-green + BUILD-01 acceptance — `queued`
**Scope:** close BUILD-01 formally.
**Read:** `ops/SPEC-01` §6.
**Do:** verify 7 consecutive green days across enabled collectors (heartbeats + manifests); injected-drift drill; covenant review of every collector vs SPEC-01 §4; C7 Kroger confirmed dark; storage projection into `BUDGET.json` (< $5/mo bar).
**Accept:** SPEC-01 §6 checklist fully evidenced in the buildlog → orchestrator runs the **adversarial review** over all collectors added since the last pass → BUILD-01 marked accepted.
**Catch:** any collector <7 green days → BUILD-01 stays open for it; accept the rest, list the stragglers.

## Phase C — the first credibility artifact

### W-006 · NHTSA retrocast: run → hostile review → publish gate — `queued` ⚑
**Scope:** the flagship. Run the pre-registered retrocast against archived vintages; produce results v1.
**Read:** `retrocast/nhtsa-recalls/PRE-REGISTRATION-v1.md` (the law), `retrocast/harness.py`, `ops/SPEC-08` §3/§5.
**Do:** signal construction per the frozen spec §3 (deterministic; hazard lexicon frozen in the workbook first); run harness on archived complaints/recalls vintages (retrocast-of-record, never live endpoints); emit `results/v1/` + `scorecard.json` citing the registration commit; write `REPORT.md`; then a SEPARATE hostile-review session walks SPEC-08 §5 (leakage, vintage, base-rate, dumb-baseline, threshold archaeology, overclaim) to zero.
**Accept:** scorecard validates; registration commit demonstrably predates results; hostile checklist zeroed; **then the ⚑ operator launch gate** (TX LLC + insurance decision + sign-off — gets `vtask add` when reached).
**Catches:** **bars fail → that is a publishable outcome**: dead-registration autopsy + a v2 pre-registration if a fixable flaw is found (disclosure mandatory) — the clause exists for exactly this; compute too heavy for Actions → operator box (the 4080 is idle); component-taxonomy mismatch vs layout doc → freeze the mapping in the workbook, note it, never bend the spec silently.

### W-007 · BUILD-04 launch surfaces — `queued` ⚑
**Scope:** WARN Watch + posting-diff pages + feeds + artifact compiler + deploy.
**Read:** `sitegen/build.py`, `engines/posting_diff.py`, `resolver/receipts.py`, `ops/SPEC-04` autonomous table, gameplan §6 BUILD-04.
**Do:** artifact compiler (cadence + anomaly artifacts from approved templates, **fail-closed through `receipts.has_valid_bundle`** — an unreceipted number must refuse to render, with a test proving it); WARN Watch page + per-state pages from archived snapshots; posting-diff pages from the ATS fleet; RSS/JSON feeds; stale-data banners wired to HEALTH; Cloudflare Pages deploy of `site/dist`; Bluesky posting dark until ⚑ handle exists.
**Accept:** site live on Pages; a WARN notice flows source→archive→page→feed with receipts within one collector cycle; two weeks unattended is the BUILD-04 bar (tracked by the weekly reports, not by a session).
**Catches:** Pages build quirks → build in Actions, deploy artifact only; a page needs a number lacking a bundle → that's the fail-closed system WORKING — build the bundle path, never bypass.

## Phase D — scheduled expansions (pull forward only via SCOPE-LEDGER triggers)

### W-008 · Hospital/Care retrocast (BUILD-05) — `queued` — trigger: ≥2 PBJ vintages archived
### W-009 · Expansion collectors C6/C8/C10/C11 — `queued` — model-bills (Wayback-only for ALEC-Exposed), EDGAR 8-K (10 req/s + UA rule), mouseprint, EIA-861
### W-010 · Workbook compiler (BUILD-06) — `queued` — trigger: two indexes live
### W-011 · Leg-authorship + FOIA micro (BUILD-07) — `queued` — **calendar-armed: prep gate fires Nov 2026** (statehouse session Jan–Apr 2027; E2 ports from OnScript)
### W-012 · Grocery pilot + Say-Do pilot (BUILD-08/09) — `queued` — Q2 2027; Kroger **⚑ human ToS read is the hard gate**, fallback = alt retailer APIs or shrinkflation-only
### W-013 · Track Record v1 + bank aggregate + first 311 city (BUILD-10) — `queued` — Q3 2027

*Everything else ideated lives in [`docs/05-SCOPE-LEDGER.md`](../../docs/05-SCOPE-LEDGER.md) with explicit triggers — nothing enters this plan except through a trigger firing or an operator gate.*
