# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the W-006 worker at hand-off, 2026-07-29. The orchestrator may re-point this before the next worker starts.*

## Not your job (no worker needed)

- **BUILD-01 acceptance** is the **orchestrator's**: ⚑ **#215** — run `python ops/fleet_green.py` on/after **2026-08-04**; exit 0 closes SPEC-01 §6 criterion 1 and BUILD-01 is marked accepted. One command, no session. (The W-005c fixes are in, so a quarantine now actually reaches committed state; `nhtsa-recalls` still carries its 2026-07-28 `startup_failure`, so its clean window starts 07-29.)
- **Operator residuals:** ⚑ **#212** healthchecks provisioning (mint an HC API token → `python ops/setup/healthchecks_setup.py --apply` → 1-min `/fail` drill; 7 checks incl. `HC_WARN`) · ⚑ **#213** weekly-session scheduler · ⚑ **#217** Cloudflare Pages hookup for the placeholder (exact settings + wrangler fallback are in the WORKPLAN W-005b entry).

---

## Standing decision the next item depends on — ⚑ #219, do not pre-empt it

**W-006 is `done` and the flagship retrocast FAILED its pre-registered bars** (2026-07-29, commit `421a9bb`). That is a published outcome, not a broken session: 3 of 4 frozen §7 bars missed on the held-out window and the 4th passed degenerately; the cause is structural — **57.8% of held-out recall campaigns occur in cells with no complaint at all in the preceding 26 weeks**, so the 0.50 event-recall bar was unreachable before a coefficient was fit. Hostile review 6/6 zeroed. Full record: `retrocast/nhtsa-recalls/REPORT.md`, `HOSTILE-REVIEW-v1.md`, `retrocast/DEAD-REGISTRATIONS.md`.

Two calls are the operator's, filed as gate `GATE-20260729-nhtsa-v1-dead-next-move` + ⚑ **#219**: (1) a v2 NHTSA pre-registration vs moving to the second retrocast (Hospital/Care Distress); (2) **whether The Exhaust's first public number should be its own failure.** Doctrine says publish failures — but whether that is also the *launch* is not a worker's call. **Do not decide either one, and do not build a v2 signal.** A v2 is a new pre-registration, frozen before results, or it is nothing.

---

## Item: W-007 — BUILD-04 launch surfaces

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** turn the archive into public surfaces — the artifact compiler, WARN Watch and posting-diff pages, feeds, stale-data banners, and the Pages deploy. Everything here is aggregate-only and receipts-first; nothing depends on a passing retrocast.

**Read (only these):** `sitegen/build.py`, `engines/posting_diff.py`, `resolver/receipts.py`, `ops/SPEC-04` (the autonomous/gated table), gameplan **§6 BUILD-04**.

**State you inherit (don't re-derive):**
- **The archive is live and self-running:** 7 collectors in Actions, state committed back per collector, 10 WARN states + 3 ATS boards, manifests carrying `git_ref`, 34/34 manifest hashes verified. Pages are built from **archived snapshots**, never live fetches.
- **`sitegen` is stdlib-only** and builds 5 pages (`python -m sitegen.build`), plus `--placeholder` mode which emits exactly one no-numbers page and deletes any stale `site/dist`. Placeholder mode renders **none** of the retrocast surfaces — that is why nothing has been published yet.
- **The Track Record page now renders a live PASS/FAIL table** from `retrocast/*/results/*/scorecard.json`, and the only scorecard in the repo is a **FAIL**. It already states that the bars were pre-registered and that failures stay published. If ⚑ #219 lands on "hold the site", that page is the thing being held.
- **Working Python:** `C:\ProgramData\miniconda3\python.exe`; full suite = `python ci/run_all.py` (11 steps, green).

**Do:**
1. **Artifact compiler** — cadence + anomaly artifacts from approved templates, **fail-closed through `receipts.has_valid_bundle`**: an unreceipted number must refuse to render, with a test that proves it refuses.
2. **WARN Watch page + per-state pages** from archived snapshots; **posting-diff pages** from the ATS fleet.
3. **RSS/JSON feeds**; **stale-data banners** wired to HEALTH (the government-continuity posture is a page-level obligation, not a footnote).
4. **Cloudflare Pages deploy** of `site/dist` — gated on ⚑ #217 existing; if it does not, build and verify locally and stop there rather than inventing a deploy path.
5. Bluesky posting stays **dark** until the ⚑ handle exists.

**Accept:** site builds green; a WARN notice flows source → archive → page → feed **with receipts** within one collector cycle; the fail-closed test passes; suite green. (The BUILD-04 bar of two unattended weeks is tracked by the weekly reports, not by a session.)

**Catches (decision tree, don't improvise):**
- **Any page tempted to show a number without a receipt bundle → it must refuse to render.** That is the fail-closed covenant, not a nice-to-have.
- **Tempted to soften or hide the FAIL scorecard on the Track Record page → STOP.** Publishing our own failure is the anti-ShadowStats tell and is constitutional. Presentation is W-007's business; deletion is nobody's.
- **No named-entity claims anywhere.** Observational facts with receipts (e.g. "this board removed N postings in three weeks, here are the diffs") are publishable day one; signature language is not, and there is no passing retrocast to unlock it.
- Deploy credentials or Pages settings missing → that is ⚑ #217, an operator errand — file/reference it, don't work around it.

**Hand off:** buildlog entry with evidence → mark W-007 in WORKPLAN → draft `NEXT.md` for W-008 → `python ci/run_all.py` green → commit → save memory → die.
