# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the W-007b worker at hand-off, 2026-07-29. The orchestrator may re-point this before the next worker starts.*

## Not your job (no worker needed)

- **BUILD-01 acceptance** is the **orchestrator's**: ⚑ **#215** — run `python ops/fleet_green.py` on/after **2026-08-04**; exit 0 closes SPEC-01 §6 criterion 1. **It now scores 8 collectors, not 7** — W-007b added `cms-pbj` to `fleetgreen.FLEET`. Its first two Actions runs are already green, so the 2026-08-04 date is not pushed. C1 is now fully delivered, which also settles the scope question W-007 raised.
- **Operator residuals:** ⚑ **#212** healthchecks provisioning — now **8 checks** (`HC_CMS_PBJ` is auto-derived; no code change needed) · ⚑ **#213** weekly-session scheduler · ⚑ **#217** Cloudflare Pages hookup · ⚑ **#219** the post-NHTSA-v1 move **and** whether the first public number is our own failure.

---

## Standing decision — do not pre-empt it

**⚑ #219 — publication is not decided.** W-007 built the full launch surfaces and **deployed nothing**. `.github/workflows/site.yml` is `workflow_dispatch`-only with **no cron** (a scheduled full publish would decide #219 by default) and defaults to the operator-approved `placeholder` mode. Do not add a cron, flip the default to `full`, or deploy. Do not soften, move, or hide the FAIL scorecard on the Track Record page — that is constitutional.

---

## Item: W-008 — Hospital/Care Distress retrocast (BUILD-05)

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** the second retrocast. PBJ nurse staffing → subsequent CMS harm deficiencies, hard-keyed on the CCN. Research §5 calls it the cleanest in the portfolio: no semantic join, leak-free by construction, 418k dated ground-truth citations. **The trigger fired 2026-07-29** — `cms-pbj` exists and two vintages are archived.

**Read (only these):** `ops/SPEC-08` §3 + §5 + §7, `retrocast/harness.py`, `retrocast/nhtsa-recalls/PRE-REGISTRATION-v1.md` — as the *form* a registration takes, **not** its content, `collectors/cms_pbj.py` and `collectors/cms_deficiencies.py` (what the archive actually holds), gameplan **§6 BUILD-05**.

**State you inherit (don't re-derive):**
- **The harness is exercised end-to-end and its sharp edges are known.** W-006 ran the NHTSA retrocast to a published FAIL: closed windows, a spillover guard (`test_start` + label windows), an O(N log N) operating-threshold search, planted-leak tests. Read `retrocast/nhtsa-recalls/REPORT.md` + `HOSTILE-REVIEW-v1.md` only if you need a worked example of the standard.
- **The join key is real and needs no matching:** `PROVNUM` in PBJ == `CMS Certification Number (CCN)` in the deficiencies CSV. Both sides archived, both hash-pinned.
- **Working Python:** `C:\ProgramData\miniconda3\python.exe`; full suite = `python ci/run_all.py` (**13 steps**, green at hand-off). R2 creds live in this box's env. The 4080 is idle if the fit is heavy.
- **What is archived right now:** PBJ **2026Q1 + 2025Q4 only** (35 of 37 published releases are NOT yet backfilled — the state file says so explicitly via `published_releases` vs `release_count`). Deficiencies: one vintage per collection day since 2026-07-28, and **CMS overwrites that file in place**, so the archive holds only what we have collected since then.

**Do:**
1. **Backfill the PBJ history FIRST** — `python -m collectors.cms_pbj --all`, or dispatch `collect-cms-pbj.yml` with args `--all`. **Measured cost: ~8.7 GB raw → ~1.1 GB stored** (archive is 0.79 GB; R2 free tier 10 GB). Two quarters satisfy the letter of the trigger and cannot support a retrocast.
2. **Establish honestly what ground-truth history exists.** The deficiencies file is overwritten in place, so the *survey dates inside* the current vintage are the history — not a series of archived vintages. Check what the archived file actually spans before designing anything around it.
3. **Pre-register before computing anything.** Signal, labels, controls, splits and **pass/fail bars** frozen and committed in a workbook + `PRE-REGISTRATION-v1.md`, with the run asserting that the registration commit is an ancestor of HEAD and aborting otherwise. Cite hashes **only from pushed history** and verify with `git merge-base --is-ancestor <hash> origin/main` (BUILD-PROTOCOL §2.7 — `git cat-file -e` gives a false pass on a rebased hash).
4. Run on archived, hash-pinned vintages only. Emit `results/v1/` + `scorecard.json` + `REPORT.md`, including **both dumb baselines**.
5. A **separate** hostile-review pass walks SPEC-08 §5 (leakage, vintage, base rate, dumb baseline, threshold archaeology, overclaim) to zero.

**Accept:** same bar as BUILD-03 — the registration commit demonstrably predates the results, `scorecard.json` validates and the site renders from it, the hostile checklist is zeroed, dumb baselines are published.

**Catches (decision tree, don't improvise):**
- **Bars fail → publish the failure**, with an autopsy in `retrocast/DEAD-REGISTRATIONS.md`, exactly as W-006 did. That is a successful session. **Never move a bar or re-tune after seeing results.**
- **If the needed ground-truth history is not in the archive, say so and scope the retrocast to what is.** Never reconstruct history from a live endpoint — archived vintages are the retrocast-of-record, and a live refetch would silently smuggle in revisions.
- **CCN reuse and facility closure across years is a real join hazard** (a CCN can be retired or reassigned). Freeze the handling in the workbook with the counts that force it — the W-006 component-taxonomy precedent — never bend it silently.
- A staffing→harm signal invites causal language. **Never predict, only measure**: this is a computed comparison to history, past tense, with receipts. **No named facility publishes** — the county-level aggregate is the surface; the named-facility tier stays gated.
- Compute too heavy for Actions → the operator box.

**Hand off:** buildlog entry with evidence → mark W-008 in WORKPLAN → draft the next `NEXT.md` → `python ci/run_all.py` green → commit → save memory → die.
