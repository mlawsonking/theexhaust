# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the W-007 worker at hand-off, 2026-07-29. The orchestrator may re-point this before the next worker starts.*

## Not your job (no worker needed)

- **BUILD-01 acceptance** is the **orchestrator's**: ⚑ **#215** — run `python ops/fleet_green.py` on/after **2026-08-04**; exit 0 closes SPEC-01 §6 criterion 1. **Read the queue-change note below first** — W-007's hand-off found that SPEC-01 C1 is half-built, which is a scope question for that acceptance, not a green-days question.
- **Operator residuals:** ⚑ **#212** healthchecks provisioning (now **8** checks if W-007b lands — `HC_CMS_PBJ` joins the list) · ⚑ **#213** weekly-session scheduler · ⚑ **#217** Cloudflare Pages hookup · ⚑ **#219** the post-NHTSA-v1 move **and** whether the first public number is our own failure.

---

## Two standing decisions the queue depends on — do not pre-empt either

**1. ⚑ #219 — publication is not decided.** W-007 built the full launch surfaces and **deployed nothing**. `.github/workflows/site.yml` is `workflow_dispatch`-only with **no cron** (a scheduled full publish would decide #219 by default), defaults to the operator-approved `placeholder` mode, and its deploy step fails loudly naming ⚑ #217. Do not add a cron, do not flip the default to `full`, do not deploy. Do not soften, move, or hide the FAIL scorecard on the Track Record page — that is constitutional.

**2. Queue change for the orchestrator to ratify — `next` is now W-007b, not W-008.** SPEC-01 §2 **C1 is `cms-pbj` + `cms-deficiencies`**, and only the second was ever built (no registry entry, no R2 objects). So: BUILD-01's first-priority collector is half-delivered; **W-008's trigger "≥2 PBJ vintages archived" can never fire**; and PBJ is marked **"CMS overwrites revisions"**, making it perishable under collect-before-you-can-compute. W-008 is marked `blocked` in the WORKPLAN and this order points at the collector instead. If the orchestrator would rather re-point at something else, W-007b's entry carries the full reasoning.

---

## Item: W-007b — the `cms-pbj` collector (the missing half of SPEC-01 C1)

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** build the one collector SPEC-01 §2 C1 names and BUILD-01 never delivered, so the second retrocast has ground truth to stand on and no further CMS release is lost. This is on the **already-approved roster** — no new-source gate, no covenant question (same publisher and posture as `cms-deficiencies`, which has been archiving since 2026-07-28).

**Read (only these):** `collectors/cms_deficiencies.py` (closest sibling: Socrata URL resolve → `CsvSchema` → `Collector`), `collectors/run.py` (the registry), `ops/SPEC-01` §2 C1 + §3 + §5, `.github/workflows/collect-cms-deficiencies.yml` (copy the caller shape), `docs/02-RESEARCH.md` §5 row *"CMS PBJ staffing + Health Deficiencies"* — that row only.

**State you inherit (don't re-derive):**
- **The fleet pattern is settled and proven.** A collector = fetch → hash → dedupe → schema-validate → zstd → immutable `raw/` + per-day manifest (`git_ref` + schema version) → per-collector `ops/state/health/<name>.json` → heartbeat. The Actions caller commits its own state file back (W-002b); `permissions: contents: write` on the caller is required or the run is a `startup_failure`.
- **Working Python:** `C:\ProgramData\miniconda3\python.exe`; full suite = `python ci/run_all.py` (**12 steps**, green at hand-off; `artifacts` is the newest step).
- **R2 creds are live in this box's environment**, so a real vintage can be archived and verified without Actions.
- `HC_*` heartbeat secrets are inert until ⚑ #212 provisions them — that is expected, not a failure.

**Do:**
1. **Re-verify the PBJ source live before depending on it** (standing order; research last checked 2026-07-11). Confirm the dataset id, the file layout of a release, and that the **CCN key** and staffing-hours columns are present.
2. Build `collectors/cms_pbj.py` with a schema contract pinning the columns the retrocast needs (CCN + staffing hours + reporting quarter). Register it in `collectors/run.py`.
3. Add the scheduled caller (C1 cadence: on release, quarterly, **plus** a weekly probe — over-schedule and let dedupe absorb it, per the cron-drift doctrine) and wire `HC_CMS_PBJ` into `_collector.yml`.
4. **Archive one real vintage to R2 and verify it** — object present, manifest hash matches, schema validates. Then fire a second time and prove it dedupes `unchanged` against the committed baseline.
5. Tests alongside the code (the sibling's tests are the template).

**Accept:** one live vintage in R2 with a conforming manifest; second firing dedupes; schema validation proven against the **real** payload, not a fixture; suite green. Note the new `HC_CMS_PBJ` check for ⚑ #212 (8 total) in the buildlog — do **not** file a new task for it, #212 already covers provisioning.

**Catches (decision tree, don't improvise):**
- **Endpoint moved, dataset retired, or shape drifted from research §5 → STOP and file a gate.** Do not go shopping for a substitute dataset; a different source is new-source onboarding (⚑ gate), not a fix.
- Release is large or multi-file → reuse the read-cap/streaming pattern `nhtsa-complaints` already runs (368 MB works today), and **archive each file as its own manifest entry** — the retrocast needs the release boundary intact, so never concatenate.
- Anything behind a login, ToS click-through, or CAPTCHA → STOP. CMS open data is none of those; if what you find is, that is the finding.
- Tempted to also start the retrocast because the data is now there → **no.** Pre-registration comes first and is its own item (W-008).

**Hand off:** buildlog entry with evidence → mark W-007b in WORKPLAN → draft `NEXT.md` for W-008 (whose trigger can then actually fire) → `python ci/run_all.py` green → commit → save memory → die.
