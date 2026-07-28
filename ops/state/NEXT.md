# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the W-005 worker at hand-off, 2026-07-28. The orchestrator may re-point this before the next worker starts.*

## Not your job (no worker needed)

- **BUILD-01 acceptance** is the **orchestrator's**: run the adversarial review (scope: every collector since the last pass + `_collector.yml` and all callers + `keepalive.yml` + the W-002b state machinery + the WARN fleet/seed + the W-005 manifest changes), then mark BUILD-01 accepted **on/after 2026-08-04 conditional on `python ops/fleet_green.py` exiting 0**. That command is the entire remaining evidence for SPEC-01 §6 criterion 1 — one command, no session.
- **Operator residuals:** ⚑ **#212** healthchecks provisioning (mint an HC API token → `python ops/setup/healthchecks_setup.py --apply` → 1-min `/fail` drill; provisions 7 checks incl. `HC_WARN`). ⚑ **#213** weekly-session scheduler (`ops/setup/schedule-weekly-session.ps1`). Until #212 lands, heartbeats are inert and fleet-green evidence comes from Actions runs + manifests + committed state (`ops/fleet_green.py` says so in its own output).

- **W-005b placeholder is `done`** (2026-07-28): `python -m sitegen.build --placeholder` is live in the repo and the page is built. The remaining step is the operator's ⚑ **#217** — Cloudflare Pages hookup (exact settings + the wrangler fallback are in the WORKPLAN W-005b entry and the buildlog). Nothing here for a worker.

---

## FIRST: Item W-005c — BUILD-01 review fixes (constitutional acceptance blocker)

**Execute W-005c ONLY this session.** At hand-off, **delete this W-005c section** so the W-006 order below becomes the standing order.

**Why:** the BUILD-01 adversarial review (constitutional gate) confirmed **19 findings — 4 HIGH / 8 MEDIUM / 7 LOW**. BUILD-01 cannot be accepted (target 2026-08-04) until every finding is fixed or dismissed-with-reasons in the buildlog. Two of them corrupt the acceptance evidence itself (`fleet_green` false-GREEN and false-RED), one defeats a constitutional mechanism (a re-armed futility clause can never fire), and one is a covenant-enforcement hole (the guard doesn't scan seed JSONs).

**Read (only these):** `ops/state/REVIEW-BUILD01.md` (**the spec — all 19 findings with scenarios + fixes**), then the files it names as you work them.

**Priority order (fix in this order; the clusters compound):**
1. **F01–F04 (HIGH):** quarantine-state persistence (both fleets + `_collector.yml` condition), ats-boards fetch containment, the empty-board false-quarantine (empty-but-parseable = valid store, postings=0), covenant guard scans `collectors/**/*.json`.
2. **F09–F10 (acceptance evidence):** `fleet_green` — unreadable state ⇒ non-green verdict (never vacuous GREEN); in-flight runs are not evidence (never false-RED). Add the synthetic 7-day fixture test.
3. **F08 (constitutional):** futility re-arm — slug carries the armed date; harden the CALENDAR date parse; pin with tests (multiple FUTILITY lines, malformed re-arm).
4. **F05–F07, F12–F15, F18–F19 (MEDIUM/LOW):** fleet 3-strike pause + `needs_gate` wiring, per-unit try/except + corrupt-manifest tolerance, framework pause enforcement (paused ⇒ no fetch; only an operator decision un-pauses), warn volume detector (or record the operator-waiver in the scope ledger), HTTPError forensics, corrupt-state-file tolerance, empty-fleet ⇒ never ping success, warn `schema_version`, the two missing W-004 regression tests.
5. **F11 (covenant audit):** re-run the robots checks against the two ACTUALLY-FETCHED hosts (`fortress.wa.gov`, `www.illinoisworknet.com`) with the collector's own `http_get`; correct both `robots_note` fields. If `fortress.wa.gov` cannot be verified, record that + the sanction basis — do not silently keep the wrong citation.
6. **F16–F17 (latent-at-scale):** fix now if quick (SR pagination; injectable `polite_pause`), else **defer-with-reasons** tied to the C3 universe-expansion gate in the buildlog + `docs/05-SCOPE-LEDGER.md` — the reviewer confirmed both are unreachable at the current 3-board seed.

**Every finding gets a disposition** (fixed + regression test, or dismissed/deferred with reasons in the buildlog). No new capabilities, no scope creep — this is hardening only.

**Accept:** all 19 dispositioned; the review's named regression tests exist and pass; suite green (`python ci/run_all.py`); a real Actions firing after the fixes still goes green end-to-end (dispatch one collector; confirm state-commit now persists a quarantine correctly if you can simulate one safely — the drift drill root, never live `raw/`).

**Hand off:** buildlog entry with a per-finding disposition table → mark W-005c `done` in WORKPLAN → strip this section from NEXT.md (W-006 stands) → commit → push → memory → die.

---

## Item: W-006 — NHTSA retrocast: run → hostile review → ⚑ launch gate

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** the flagship credibility artifact. Run the **pre-registered** NHTSA recalls retrocast against archived vintages, produce `results/v1/`, then walk the hostile-review checklist to zero. This is the first thing the project publishes a number from, so the pre-registration is law and the review is adversarial by design.

**Read (only these):** `retrocast/nhtsa-recalls/PRE-REGISTRATION-v1.md` (**the law — signal construction, thresholds, bars, all frozen**), `retrocast/harness.py`, `ops/SPEC-08` **§3 (harness contract) + §5 (hostile-review checklist)**.

**State you inherit (don't re-derive):**
- **The corpus is in R2 and is the retrocast-of-record** — never fetch live endpoints for this. `raw/nhtsa-complaints/2026/07/28/` holds two 368 MB `FLAT_CMPL.zip` vintages (51 tab-delimited fields, ~2.23 M rows); `raw/nhtsa-recalls/2026/07/28/` holds three `FLAT_RCL_POST_2010.zip` objects across two distinct hashes (29 fields, 243 k rows). Manifests carry the sha256 of every one; **34/34 manifest hashes verified against their object keys on 2026-07-28**.
- **Pull vintages through the custom domain** `archive.theexhaust.org` (egress covenant — never raw `r2.dev`); the W-001 restore drill proves that path (sha256 + schema match).
- **Working Python:** `C:\ProgramData\miniconda3\python.exe`; full suite = `python ci/run_all.py` (9 steps, currently green). R2 creds are in the operator-box User env.
- **Compute:** the operator box + its RTX 4080 is the sanctioned heavy-compute runner (Actions has a 6-hr job cap; a 368 MB × 2.2 M-row join belongs local). **No metered LLM anywhere in this** — signal construction is deterministic per the frozen spec.

**Do (SPEC-08 §3):**
1. **Freeze the hazard lexicon in the workbook first**, then construct the signal exactly as pre-registration §3 specifies — deterministic, no tuning against outcomes.
2. Run the harness over archived vintages only; emit `results/v1/` + `scorecard.json` **citing the registration commit** (the git ordering IS the proof the registration predates the results — verify it does).
3. Write `REPORT.md` (what was measured, precision/recall/calibration, the dumb baseline it must beat).
4. **Then a SEPARATE hostile-review pass** (SPEC-08 §5) to zero: leakage, vintage discipline, base rate, dumb baseline, threshold archaeology, overclaim.

**Accept:** scorecard validates; the registration commit demonstrably predates the results; hostile checklist zeroed; suite green. **Then the ⚑ operator launch gate** (TX LLC + insurance decision + sign-off) — file it with `vtask add` when reached, don't assume it.

**Catches (decision tree, don't improvise):**
- **Bars fail → that is a publishable outcome, not a failure of the session.** Write the dead-registration autopsy; a v2 pre-registration is allowed only with the disclosure the doctrine requires. Never retune the frozen spec to make a bar pass — that is threshold archaeology and the hostile review exists to catch it.
- Component-taxonomy mismatch vs the layout doc → freeze the mapping in the workbook and note it; never bend the spec silently.
- Compute too heavy for Actions → operator box (expected; note the switch).
- Anything that tempts a live fetch of NHTSA data → STOP; the archived vintages are the record (government-continuity posture).

**Hand off:** buildlog entry with evidence → mark W-006 in WORKPLAN → draft `NEXT.md` for **W-007** (BUILD-04 launch surfaces) → `python ci/run_all.py` green → commit → save memory → die.
