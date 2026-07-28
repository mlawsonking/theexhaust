# REVIEW-BUILD01 — confirmed adversarial-review findings (2026-07-28)

*Constitutional BUILD-01 acceptance review (4 reviewers → verified synthesis; workflow `wf_07f6cc4a-b15`).*
*19 confirmed (4 HIGH / 8 MEDIUM / 7 LOW), 1 dismissed (healthchecks grace sizing — documented stricter-direction design choice).*
*This file is the W-005c fix-worker's spec. Each finding: fix it, or record a dismissal/deferral WITH REASONS in the buildlog (constitutional rule). BUILD-01 acceptance is blocked until every finding has a disposition.*

**Synthesis summary:** Synthesized 31 findings from 4 reviewers into 19 confirmed (4 high, 8 medium, 7 low) after verifying every load-bearing claim against the code (warn.py, ats_boards.py, framework.py, _collector.yml, weekly.py, gates.py, fleet_green.py x2, covenant_guard.py, seed files, healthchecks.py, engines/ats.py). Dismissed 1: the healthchecks grace-sizing complaint (18h vs the spec's 36h example) — the module docstring documents it as a deliberate stricter-direction design (tolerate exactly one missed firing) and a second reviewer independently verified the arithmetic; at most it warrants a SPEC-03 §1 text amendment, not a code fix. One merged finding was corrected during synthesis: the claimed weekly futility-gate re-filing spam (R2) cannot occur because the terminal-decision check blocks re-filing — which is itself the confirmed bug (a re-armed kill date can never fire); the underlying date-parse fragility was folded into that finding. Top cluster to fix first (compounding): fleet last_action misrecording means quarantine state never persists to main (and fleetgreen's quarantine leg is dead for both fleets), while ats_boards' unwrapped fetch and empty-board assert make routine events (dead token, hiring freeze) either kill the whole fleet run or alarm 3x/day forever. Also constitutional: covenant_guard never scans the seed JSONs where all source URLs now live, and both fleet_green evidence bugs sit directly under the imminent 2026-08-04 BUILD-01 acceptance check (one false-green direction, one false-red).

## F01 · HIGH · `collectors/warn.py:205`
*Raised by: spec-compliance + correctness + test-adequacy (3 reviewers)*

**Defect:** Quarantine outcomes never reach committed state: both fleets set node last_action='stored' if stored else 'unchanged' and refresh last_success unconditionally (warn.py:205, ats_boards.py:96), so a quarantine-only run reads 'unchanged' and _collector.yml:67 skips the state commit; the quarantine/pause evidence the watchers need never persists.

**Failure scenario:** All warn states dedupe-unchanged except CA which 503s: run exits 2, but node last_action='unchanged' -> persist step prints 'unchanged — baseline already committed' and exits 0. Per-state quarantined-fetch record (last_error, quarantined count) never reaches main; weekly merged_health, report, and fleet_green's committed-state leg all show a healthy fleet for the whole outage. Corollary: opscore/fleetgreen.py:48's startswith('quarantined') check can NEVER trigger for either fleet, and a framework collector's paused=False reset riding an 'unchanged' dedupe also never persists. Verified: warn.py:205-207, ats_boards.py:96-97, _collector.yml:62-67.

**Fix:** In both run_fleet functions compute last_action = 'quarantined' if quarantined else ('stored' if stored else 'unchanged'), and refresh last_success only when quarantined==0 (record last_run otherwise). Add the missing mixed-outcome fleet test (one state 503, one stored -> assert /fail heartbeat suffix and committed node reflects quarantine) — the /fail path of warn._heartbeat currently has zero coverage.

## F02 · HIGH · `collectors/ats_boards.py:62`
*Raised by: spec-compliance + correctness + test-adequacy (3 reviewers)*

**Defect:** archive_board calls fetch_fn with no try/except; framework.http_get uses urllib.urlopen which raises HTTPError on any non-2xx, so one dead board (routine 404 when a seed company drops its ATS) crashes the whole fleet run: remaining boards uncollected, health file never written, no heartbeat — not even /fail.

**Failure scenario:** A Greenhouse token 404s: HTTPError propagates through the run_fleet comprehension (line 93), the process dies with a traceback before the health json.dump and before _heartbeat. Every board sorted after the dead one loses its daily snapshot (the docstring's own 'every uncollected day loses the diff'), already-fetched boards' dedupe updates are lost, and the failure repeats every firing until an operator edits the seed. warn.archive_state (warn.py:150-156) contains exactly this case; ats_boards does not. No test feeds a raising fetch_fn, so the whole suite passes.

**Fix:** Wrap the fetch in try/except mirroring warn.archive_state: rec.update(last_run, last_action='quarantined-fetch', last_error=...) and return {'board': bkey, 'action': 'quarantined', 'alarm': True} so the fleet continues, health is written, and the existing quarantine count still drives /fail + exit 2. Land with a regression test (3-board seed, board 2 raises URLError -> boards 1 and 3 store, quarantined==1, health written, heartbeat /fail).

## F03 · HIGH · `collectors/ats_boards.py:71`
*Raised by: spec-compliance + correctness (2 reviewers)*

**Defect:** assert n >= 1 classifies a legitimately empty board (valid {"jobs": []}, zero open postings) as a parse failure: quarantined + alarm=True + exit 2 on every firing, forever, with no anti-storm dedupe, no drift streak, and no auto-pause — and the all-postings-vanished snapshot never lands in raw/.

**Failure scenario:** A seed company (layoffs.fyi alumni — hiring freezes are the norm) closes its last opening: Greenhouse returns valid empty jobs. The assert fires, the payload goes to quarantine/, and with 3x/day over-scheduling that is a /fail ping + red workflow three times a day indefinitely. The single most valuable event for the Posting-Diff engine — postings vanished — is treated as schema drift, the SPEC-03 §4 alarm budget (~0/week) is destroyed, and framework's last_quarantine_hash/drift_streak/pause semantics (framework.py:353-365) don't exist in the fleet path so nothing ever de-escalates.

**Fix:** Drop the n>=1 assert: an empty-but-parseable board is a valid store with postings=0 (keep the try/except for real normalize() exceptions). Add last_quarantine_hash-style anti-storm dedupe to the fleet quarantine path so a recurring identical bad payload alarms once.

## F04 · HIGH · `ci/covenant_guard.py:43`
*Raised by: covenant (1 reviewer, verified)*

**Defect:** Do-not-collect enforcement scans only *.py (cdir.rglob('*.py')), but W-004 moved every source URL into collectors/seed_warn.json and seed_boards.json — a banned-source data_url added to a seed passes CI green. do_not_collect.txt's claim 'Enforced by ci/covenant_guard.py' is now false for the files where sources actually live.

**Failure scenario:** A future session adds an aggregator 'cross-check' data_url (e.g. a layoffs.fyi or indeed.com URL) to seed_warn.json: covenant guard and ci/run_all.py pass, the change merges, and collect-warn.yml fetches a register-banned source from production twice daily with zero CI signal. The hardcoded 4-name substring check in test_warn.py does not read the register and covers only the WARN seed.

**Fix:** In check_collectors() scan JSON alongside Python: for p in list(cdir.rglob('*.py')) + list(cdir.rglob('*.json')). Add a regression test that plants a banned domain in a temp seed .json under collectors/ and asserts the guard fails.

## F05 · MEDIUM · `collectors/warn.py:154`
*Raised by: spec-compliance (1 reviewer, mechanism verified)*

**Defect:** Neither fleet has SPEC-03 §2's 3-consecutive-failures -> auto-pause + gate wiring for fetch quarantines: no fail_streak, per-state paused, or needs_gate is ever set, and weekly.file_collector_gates (weekly.py:136-140) reads needs_gate only on top-level collector records — which the fleets never write — so a permanently broken source alarms 2x/day forever and can never surface as a gate item.

**Failure scenario:** A state rotates its yearly filename (the resolve_data_url docstring says states do exactly this) and the old data_url 404s: every firing records quarantined-fetch, pings /fail, exits 2 — 14 alarm events/week from one state, indefinitely. Nothing pauses the state, no gate is ever filed (per-state records live under node['states'] where the sweep never looks), and the alarm channel drowns while the other 9 states are actually fine.

**Fix:** Track per-state (and per-board) fail_streak in the quarantine paths; on streak>=3 set state-level paused (skipped by run_fleet until operator re-enable) and node-level needs_gate=f'warn-{state}-fetch-3x' so file_collector_gates files exactly one source gate and the heartbeat recovers once the broken state is paused.

## F06 · MEDIUM · `collectors/warn.py:202`
*Raised by: correctness + test-adequacy (2 reviewers)*

**Defect:** archive_state's try/except covers only resolve+fetch; exceptions from storage.put (line 178) or _update_manifest's json.loads of a corrupt existing day-manifest (line 131) propagate out of the run_fleet comprehension, aborting the remaining states, skipping the health write and the heartbeat. Same shape in ats_boards.py:44-54 and framework.py:308-309.

**Failure scenario:** A transient R2 500 on storage.put for the first state in seed order, or a truncated raw/warn/CA/.../manifest.json from an interrupted earlier run, raises mid-comprehension: the other 9 states are not collected this firing and already-stored states lose their dedupe update (duplicate re-stores next run). In the corrupt-manifest case, every subsequent firing that day re-stores the raw then crashes at the same manifest — a self-sustaining partial outage costing the perishable corpus up to a full day.

**Fix:** Wrap the per-state/per-board unit of work in try/except inside run_fleet (record last_action='error', alarm=True, continue), and in all three _update_manifest implementations treat unparseable existing manifest content as absent (start fresh; the old object stays immutable in storage) instead of raising.

## F07 · MEDIUM · `collectors/framework.py:323`
*Raised by: spec-compliance (1 reviewer, verified)*

**Defect:** The SPEC-03 §2 auto-pause is recorded (paused=True, needs_gate at framework.py:364-365) but never enforced: Collector.run has no paused check, so a 'paused' collector keeps fetching, a varying drifted payload defeats the last_quarantine_hash anti-storm and re-quarantines + re-alarms every firing, and any clean/unchanged payload silently self-un-pauses (paused=False at lines 335 and 381) without an operator decision.

**Failure scenario:** CMS renames a column AND keeps shipping daily data updates: each drifted payload hashes differently, so after the 3rd drift sets paused=True the next firing still runs, misses the anti-storm branch, and emits alarm=True plus a new quarantine object every firing while nominally paused — the alarm budget the pause exists to protect keeps bleeding and quarantine/ grows per firing.

**Fix:** At the top of Collector.run (after _load_health), if rec.get('paused'): return {'action': 'paused', 'heartbeat': 'withheld(paused)'} without fetching. Clear paused only via the gate's operator re-enable, not automatically on a clean payload.

## F08 · MEDIUM · `opscore/weekly.py:86`
*Raised by: spec-compliance + correctness + test-adequacy (3 reviewers, merged)*

**Defect:** A re-armed futility clause can never fire: _futility_terminally_decided matches any decided gate with the constant 'futility-clause' slug forever (gates.is_decided includes approve-override), so after option B's approve-override + new CALENDAR.md kill date, the new date passing files nothing — the constitution's 'the clause is re-armed, never deleted' is silently defeated. Compounding: _futility_date (lines 39-47) takes the first date on the first line containing 'FUTILITY', so a stray earlier mention silently re-dates the review and a malformed re-arm date silently reverts to the 2027 constant.

**Failure scenario:** 2027-12-31 passes, operator records approve-override with a re-armed 2029 date in CALENDAR.md exactly as the gate's option B instructs. In 2029 the new date passes: maybe_file_futility_gate finds the 2028 approve-override gate in decided/ and returns None — silent continuation, the exact outcome the mandatory clause exists to forbid. Separately, an operator note line mentioning FUTILITY with a 2030 date above the real line moves the kill review to 2030 with no alarm.

**Fix:** Scope the terminal-decision check to the currently-armed date: include the armed date in the gate slug (f'{FUTILITY_SLUG}-{fdate.isoformat()}') for filing and both pending/decided lookups. Harden _futility_date with a strict anchor (e.g. 'FUTILITY: YYYY-MM-DD') or take max() of dates on the line, and pin both behaviors with tests (multiple FUTILITY lines; malformed/invalid re-arm date).

## F09 · MEDIUM · `ops/fleet_green.py:86`
*Raised by: test-adequacy (1 reviewer, verified)*

**Defect:** committed_state() swallows any exception and returns {} (bare except at line 86-87), which score() reads as quarantined=False/paused=False — a corrupt or shape-changed committed state file yields a vacuous GREEN and 'criterion 1 SATISFIED' exit 0. The entire evidence-gathering half of the BUILD-01 acceptance gate (gh_runs, r2_manifest_days, committed_state, main) has zero tests; only the pure score() is tested.

**Failure scenario:** ops/state/health/warn.json is truncated or carries merge-conflict markers while its committed record said paused=True: committed_state returns {}, score sees no quarantine/pause, and the acceptance report prints GREEN and SPEC-01 §6 criterion 1 SATISFIED — falsely closing the constitutional acceptance criterion in the lenient direction.

**Fix:** Make an unreadable state file a non-green verdict (e.g. STATE-UNREADABLE), never GREEN. Move committed_state and the run-row mapping into opscore/fleetgreen.py and add a synthetic 7-day fixture test covering a corrupt state file, a paused=True file, and main-level aggregation returning 1.

## F10 · MEDIUM · `ops/fleet_green.py:52`
*Raised by: correctness (1 reviewer, verified)*

**Defect:** gh_runs maps an empty conclusion (run still executing) to 'in_progress', and score() (opscore/fleetgreen.py:46) counts any conclusion not in ('success','skipped') as a FAILED day — a merely in-flight run marks the collector FAILED-RUN and the 7-day criterion falsely NOT satisfied (exit 1).

**Failure scenario:** Operator runs fleet_green.py --today 2026-08-04 shortly after any cron slot (7 collectors x up to 3 firings/day makes this the common case): the in-flight run lands in the window with conclusion 'in_progress', that day joins failed_days, green flips False, and the acceptance report reads FAILED for a perfectly green collector — corrupting BUILD-01 evidence in the strict direction.

**Fix:** Drop non-terminal runs from evidence: skip rows with a falsy conclusion in gh_runs (or exclude 'in_progress' from the failed set in score()). A run with no conclusion is not evidence either way. Cover in the same fixture test as the committed_state fix.

## F11 · MEDIUM · `collectors/seed_warn.json:29`
*Raised by: covenant (1 reviewer, verified against seed text)*

**Defect:** Robots verification is recorded against hosts the collector never touches for 2 of 10 states: WA fetches fortress.wa.gov (line 27) but its robots_note cites esd.wa.gov; IL fetches www.illinoisworknet.com (lines 34-35) but its robots_note (line 37) cites dceo.illinois.gov. robots.txt is per-host, so the SPEC-01 §4.3 onboarding check never covered the fetched hosts (reviewer probe: illinoisworknet robots is 404/nothing-disallowed; fortress.wa.gov reset the connection — genuinely unverified).

**Failure scenario:** fortress.wa.gov/robots.txt disallows /esd/ or everything: the fleet then scrapes a robots-disallowed path daily while the committed seed asserts compliance — a covenant violation with a falsified audit trail, and BUILD-01 acceptance evidence citing a verification that never covered the fetched host.

**Fix:** Re-run the onboarding robots check against fortress.wa.gov and www.illinoisworknet.com with the collector's own http_get and correct both robots_note fields to name the fetched host and what its robots.txt says. If fortress.wa.gov cannot be verified, record that plus the basis on which the fetch is sanctioned.

## F12 · MEDIUM · `collectors/warn.py:181`
*Raised by: spec-compliance (1 reviewer)*

**Defect:** The SPEC-01 §5 / SPEC-03 §2 volume-anomaly detector is entirely absent from the warn fleet: parsed_rows is computed but no per-state rows_history/trailing-median, no volume band in the manifest, no alarm at the extreme tier. W-004 relaxed schema-drift quarantining to parse-as-metadata; it did not waive the volume detector.

**Failure scenario:** CA's xlsx silently collapses from ~800 parsed rows to 3 (agency splits the workbook, or moves data to a sheet _count_xlsx_rows doesn't pick): parse_ok=True, the snapshot stores green with no flag and no alarm — for months, on the flagship state. Detectable only by manual manifest archaeology.

**Fix:** When parse_ok is true, keep per-state rows_history[-8:] + rows_median (mirroring framework.py:376-379), write volume_band into the manifest entry, and alarm on the extreme tier — handling the legitimate always-0 states (PA/WI) whose median is 0. Alternatively, if the operator rules this waived by W-004, record that explicitly in the scope ledger; today the waiver exists nowhere.

## F13 · LOW · `collectors/warn.py:157`
*Raised by: correctness (1 reviewer, verified)*

**Defect:** The non-200 forensics branch (store block/notice page under quarantine/, record last_status) is unreachable in production: framework.http_get (framework.py:59) uses urlopen, which raises HTTPError for any non-2xx, so real 403/503s take the generic except at line 154 and the response body is discarded. Only the test fakes (tuple-returning fetches) exercise lines 157-162.

**Failure scenario:** A state serves a 403 datacenter-block page: rec gets only 'HTTPError: ...' text — the block-page body the 403-ladder (module docstring, SPEC-01 §4) needs for diagnosis is never stored. Tests pass while the documented forensics feature does not exist in production.

**Fix:** Catch urllib.error.HTTPError before the generic except and feed e.code / e.read() into the existing non-200 quarantine branch (or have http_get return (e.code, dict(e.headers), e.read()) for HTTP errors so status-based handling is real). Add a production-shaped test raising HTTPError with a body.

## F14 · LOW · `collectors/warn.py:197`
*Raised by: correctness (1 reviewer)*

**Defect:** run_fleet json.load's the committed per-collector state file with no error handling (same at ats_boards.py:88 and framework.py:284); a truncated warn.json — which the persist step will happily commit, since corrupt json makes its jq fall back to action='update' — makes every subsequent firing crash before collecting anything.

**Failure scenario:** Runner killed mid health-write -> truncated state file committed by the always() persist step -> every later firing raises JSONDecodeError at line 197 and the whole WARN archive stops until a human repairs a file whose only role is a recoverable dedupe/health cache.

**Fix:** Wrap the load in try/except -> fall back to {'collectors': {}} in all three loaders (worst case: one duplicate snapshot re-stored, which the immutable archive tolerates by design).

## F15 · LOW · `collectors/warn.py:212`
*Raised by: test-adequacy (1 reviewer, verified)*

**Defect:** An empty fleet (0 states after an --only typo, or a seed-shape drift past the CI seed test) pings the dead-man heartbeat SUCCESS and exits 0 — the exact silent-stop SPEC-03 §1 exists to alarm on. Same hole at ats_boards.py:103.

**Failure scenario:** Operator runs --only CAX (typo) from the sanctioned operator-box path with HC_WARN set: results=[], quarantined==0, healthcheck pinged green, exit 0 — healthchecks stays up while zero states were collected.

**Fix:** In both run_fleet functions treat an empty fleet as a failure: ping /fail (or skip the ping) and exit nonzero; add tests asserting an empty fleet never pings success.

## F16 · LOW · `engines/ats.py:26`
*Raised by: spec-compliance + correctness (2 reviewers; latent — no smartrecruiters board in the current 3-board seed)*

**Defect:** The SmartRecruiters endpoint hardcodes ?limit=100 with no pagination: any board with >100 postings archives a silently truncated 'full-board' snapshot with the manifest reporting postings=100 as if complete. Latent today, armed for the gated universe expansion — and a truncated vintage in the immutable archive can never be re-fetched.

**Failure scenario:** Universe expansion onboards a 150-posting SmartRecruiters company: every snapshot stores only the first page; posting_diff later reports phantom appear/vanish events from page-composition churn, with hash, parse, and validation all green.

**Fix:** Page the SR endpoint (offset/limit loop until totalFound reached, archiving the concatenated document), or at minimum quarantine loudly when totalFound exceeds the returned page — and block smartrecruiters seed entries at onboarding until pagination lands.

## F17 · LOW · `collectors/ats_boards.py:93`
*Raised by: spec-compliance + covenant (2 reviewers; latent at current seed size)*

**Defect:** SPEC-01 §4.1 is a MUST ('rate-limited and jittered per source; sequential per host') but no rate-limit/jitter code exists in either fleet loop; engines/ats.py:7 claims 'polite rate-limited polling' that is unimplemented. Bounded today (max 2 same-host requests: IL's landing resolve + data fetch), but C3 targets 3-5k boards concentrated on ~4 shared API hosts.

**Failure scenario:** At expansion, the fleet fires thousands of zero-delay sequential requests at boards-api.greenhouse.io 3x/day — the burst behavior that draws 429s/vendor blocks and escalates the 403 ladder on a self-inflicted wound; the BUILD-01 §6 covenant-review criterion cannot honestly pass for C3 with the politeness covenant unimplemented.

**Fix:** Add an injectable polite_pause(base, jitter) helper in framework.py, call it between fleet iterations (and between IL's landing resolve and data fetch), no-op in tests; size for the SPEC-01 §5 45-min bound before the universe grows.

## F18 · LOW · `collectors/warn.py:131`
*Raised by: spec-compliance (1 reviewer)*

**Defect:** warn per-day manifests omit SPEC-01 §3's required 'schema version' component entirely — files/hashes/parsed_rows/git_ref but no parser version — unlike ats-boards (schema_version='posting-v1') and framework (schema_required).

**Failure scenario:** The W-004 parse heuristics change (_RowTdCounter or _count_xlsx_rows behavior): parsed_rows across vintages become incomparable and nothing in the manifest says which parser produced each count — a retrocast consumer cannot distinguish a real volume shift from a parser change.

**Fix:** Add a module-level PARSER_VERSION ('warn-parse-v1') written as schema_version in _update_manifest, bumped on any parse-behavior change.

## F19 · LOW · `collectors/tests/test_warn.py:1`
*Raised by: test-adequacy (1 reviewer)*

**Defect:** Two W-004 invariants lack regression protection: (a) no end-to-end test that an unparseable payload still STORES raw with parse_ok=false/parsed_rows=null (the constitutional store-raw-always steer — all archive_state tests use parseable payloads); (b) warn's same-day manifest append has no test (ats-boards got exactly this regression test at W-005), and the two-writer manifest read-modify-write race (sanctioned operator-box run vs Actions firing on the same R2 bucket) is neither fixed nor pinned as accepted.

**Failure scenario:** A refactor that re-orders parse before store or re-promotes a parse miss to quarantine (the exact pre-W-004 behavior this design reversed) passes the entire suite; an overwrite bug in warn's manifest append — the same bug class the ats test was written for — ships silently, leaving stored raw objects absent from the SPEC-01 §3 audit index.

**Fix:** Add to test_warn.py: (a) archive_state with format 'csv' but b'%PDF garbage' body -> assert action=='stored', parse_ok False, raw object exists, manifest entry carries parse_ok=false; (b) a second changed same-day store -> assert both manifest entries survive (mirror engines/tests/test_engines.py:104-109). Record a decision (or fix) for the two-writer manifest race.
