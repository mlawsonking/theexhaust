# collectors — the archival fleet (SPEC-01)

Each collector continuously snapshots a perishable public corpus into immutable R2 object storage, schema-validated, deduplicated, alarmed. **Doctrine: collect before you can compute — every uncollected week is data lost forever.** Built at **BUILD-01** (outranks everything) against real R2.

## Per-collector contract (SPEC-01 §5), every collector MUST:
1. Declare a **schema contract** (fields, types, row-count band vs. trailing 8-week median) and validate before store.
2. Store to `raw/{collector}/{YYYY}/{MM}/{DD}/{HHmm}-{sha256_12}.{ext}.zst` + a per-day `manifest.json`; **never overwrite raw** (vintages are immutable).
3. **Dedupe by content hash** (also the cron-drift defense); skip if unchanged.
4. Write `ops/state/HEALTH.json` on success; ping its healthchecks heartbeat **on validated store only**.
5. Quarantine + alarm on schema drift (`quarantine/{collector}/…`), never silently drop.
6. Be idempotent; finish < 45 min (chunk otherwise); carry a 3-line README (source, cadence, covenant notes, `verified` date).

## Collection etiquette (covenant, MUST — SPEC-01 §4)
Rate-limited/jittered, sequential per host, honest stable User-Agent. **Never circumvent technical controls** (no IP rotation, CAPTCHA-solving, bot-detection evasion, account creation, or ToS acceptance). **The 403 ladder:** serves normally → Actions; generically datacenter-403s but serves home connections → operator box at identical politeness (log it); blocks/challenges *this* collector → **STOP + gate item**. Never escalate past the operator box autonomously.

## Do-not-collect enforcement
Collectors for the registered sources (OBSERVATORY.md register; `ci/do_not_collect.txt`) **must not exist** — `ci/covenant_guard.py` fails CI if one references a banned source. Revival = gate item + fresh operator sign-off.

## Roster v1 (priority order — SPEC-01 §2)
C1 `cms-pbj`+`cms-deficiencies` · C2 `warn-<state>` · C3 `ats-boards` · C4 `nhtsa-complaints` · C5 `cpsc-recalls` · C6 `model-bills` · **C7 `kroger-basket` (built dark; enable only after the human ToS-read gate)** · C8 `edgar-8k` · C9 `fdic-quarterlies` · C10 `mouseprint` · C11 `eia-861` · C12 `legiscan-bulk`.

*C1 sources re-verified live 2026-07-11 (CMS deficiencies `r5ix-sfxw`: 200, 418,479 rows, CCN key present).*
