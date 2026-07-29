# GATE: NHTSA retrocast v1 failed its bars — decide the next move (v2 vs next index) and whether the failure publishes
type: new-index
created: 2026-07-29  by: job:W-006-nhtsa-retrocast
expires: 2026-08-26
default_on_expiry: no-action
## What & why now
The flagship first retrocast is DEAD: 3 of 4 pre-registered bars failed on the held-out window and the fourth passed degenerately (REPORT.md, HOSTILE-REVIEW-v1.md 6/6 zeroed, autopsy in DEAD-REGISTRATIONS.md). The binding cause is structural, not fixable by tuning: 57.8% of held-out recall campaigns occur in cells with no complaint at all in the preceding 26 weeks, so the 0.50 event-recall bar was unreachable before a coefficient was fit. Two decisions follow, and neither is a worker s: (1) portfolio — a v2 pre-registration for NHTSA (new registration + mandatory disclosure of this attempt) or move to the second retrocast (research called Hospital/Care Distress the cleanest immediate one, hard CCN key); (2) launch surface — landing this scorecard flips the site Track Record page to a live PASS/FAIL table, so The Exhaust s first public number would be its own failure. Doctrine says publish failures; whether that is also the LAUNCH is an operator call. Nothing is deployed yet (Pages hookup #217 is open and placeholder mode renders none of this).
## Evidence
retrocast/nhtsa-recalls/REPORT.md; HOSTILE-REVIEW-v1.md; results/v1/scorecard.json (registration e3d4d84 2026-07-13 -> freeze d28d8fa -> results code, clean tree, ancestry asserted by the run); DEAD-REGISTRATIONS.md
## Options
A publish the failure as the launch story (doctrine-consistent: the scorecard is the moat, and a public autopsy is the anti-ShadowStats tell) + move to the Hospital/Care retrocast / B v2 NHTSA pre-registration first (coarser unit, longer horizon, or defect-narrative join — all untested), publish nothing until it clears / C publish the failure but hold the site until a second retrocast passes, so the first public page is not only a failure
DECISION: 
notes: 
