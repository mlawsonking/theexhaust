# GATE: WARN tranche-1: onboarding approach for walled/sourceless states (OH, GA, NY current-data)
type: source
created: 2026-07-28  by: job:W-004-warn
expires: 2026-08-25
default_on_expiry: no-action
## What & why now
W-004 shipped 10 WARN states collecting to R2 (CA NY-historical TX WA IL NJ PA FL MD WI). Three tranche-1 sources have no clean primary fetch and were deferred (not evaded): OH = ODJFS CMS serves a 404 shell to every non-browser fetch (curl/UA/WebFetch) — needs a headless render; GA = no public list exists (tcsg.edu/warn is an employer submission form only; the legacy GDOL list is defunct through 2013) — needs an open-records request; NY current-data = a Tableau Public dashboard with no clean file export (the RETIRED NY HTML table IS archived, but is frozen ~early 2025). None is a covenant-safe autonomous fetch today. Decide the onboarding approach.
## Evidence

## Options
A defer all three to a later WARN tranche (10 states keep collecting; safe default) / B build a headless-render adapter for OH + NY-current — REQUIRES a covenant review (a headless browser must stay polite and non-evasive; no bot-detection defeat) / C file a GA public-records request (operator action)
DECISION: 
notes: 
