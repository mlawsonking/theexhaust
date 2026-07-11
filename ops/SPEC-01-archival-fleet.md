# SPEC-01 — Archival fleet

*Contract for the collectors. Doctrine: collect before you can compute — every uncollected week is data lost forever. Built at BUILD-01, which outranks everything.*

## 1. Purpose

Continuously snapshot perishable public corpora into immutable object storage, schema-validated, deduplicated, alarmed. The archive is the retrocast-of-record (constitution: government-continuity posture) and the long-term primary-source asset.

## 2. Collector roster v1 (priority order)

| # | Collector | Source | Cadence target | Perishability | Notes |
|---|---|---|---|---|---|
| C1 | `cms-pbj` + `cms-deficiencies` | CMS PBJ staffing + Health Deficiencies (r5ix-sfxw) | on release (quarterly) + weekly probe | **CMS overwrites revisions** | keep every vintage |
| C2 | `warn-<state>` | 49 state WARN sources | daily, staggered | notices amended/removed | top-10 states by volume first (CA, NY, TX, WA, IL, …), rest phased in |
| C3 | `ats-boards` | Greenhouse/Lever/Ashby/SmartRecruiters full-board JSON, seed universe ~3–5k boards | daily full snapshot | postings vanish silently | seed = layoffs.fyi companies ∪ WARN appearers ∪ major-index lists; universe expansion is a gate item |
| C4 | `nhtsa-complaints` | NHTSA complaints API + FLAT_CMPL refresh | weekly delta + monthly flat file | additive but re-issued | flat file is retrocast-of-record |
| C5 | `cpsc-recalls` | CPSC RestWebServices JSON + CSV | weekly | recalls edited post-hoc | |
| C6 | `model-bills` | ALEC current library + SiX/ALICE pages | weekly | pages edited/removed | ALEC-Exposed historical via **Wayback only** (never defeat the Cloudflare challenge) |
| C7 | `kroger-basket` | Kroger Public Products API, pilot-metro stores | daily | prices are the product | **built dark; enable only after the human ToS read gate clears** |
| C8 | `edgar-8k` | EDGAR submissions stream (workforce/officer/auditor items) | daily | additive | descriptive User-Agent required (their rule) |
| C9 | `fdic-quarterlies` | FDIC BankFind/FFIEC bulk | quarterly | stable | aggregate-only downstream, per constitution |
| C10 | `mouseprint` | mouseprint.org posts | weekly | page rot | shrinkflation retrocast source |
| C11 | `eia-861` | EIA-861 SAIDI/SAIFI workbooks | annual | stable | utility ground truth |
| C12 | `legiscan-bulk` | LegiScan bulk datasets | weekly in-session | bills amended | registration key; never republish their compilation |

Adding a collector = a gate item (new-source onboarding, SPEC-04). Removing/pausing on failure is autonomous (safe direction).

## 3. Storage contract

- **Primary:** Cloudflare R2, bucket `exhaust-archive`, served via a **free custom domain** (never raw `r2.dev` — egress covenant). Layout: `raw/{collector}/{YYYY}/{MM}/{DD}/{HHmm}-{sha256_12}.{ext}.zst` + a per-day `manifest.json` (files, hashes, row counts, schema version, collector git ref).
- **Immutability:** raw objects are never overwritten or deleted. Corrections happen downstream; the archive keeps the wrong vintage too (that's what a vintage is).
- **Cold mirror:** monthly tarball per collector to GitHub Releases (≤2 GiB/asset, chunk if needed). **Banned:** Git LFS; hot-serving `raw.githubusercontent.com` (constitutional).
- **Quarantine:** schema-drifted snapshots go to `quarantine/{collector}/...` untouched, alarmed, never silently dropped — drifted data is still data.
- **Derived layer:** `derived/{engine}/...` is rebuildable from raw + code and carries no immutability guarantee.

## 4. Collection etiquette (covenant-enforcing, MUST)

1. Rate-limited and jittered per source; sequential per host; identify honestly (stable User-Agent with contact URL) where headers are customary.
2. **Never** circumvent technical access controls: no IP rotation to evade blocks, no CAPTCHA solving, no bot-detection evasion, no account creation, no ToS acceptance (constitution, scraping-hygiene covenant).
3. Respect robots.txt for scraped HTML paths; API/bulk endpoints follow their published limits.
4. Dedupe before store: skip if content hash matches the latest stored snapshot (also the cron-drift dedupe).
5. **The 403 ladder:** (a) source serves normally → Actions. (b) source generically 403s datacenter IPs but serves ordinary home connections → collector MAY run from the operator box (scheduled task) at **identical politeness** — this is being a normal client, not evasion; log the switch. (c) source blocks *this collector* specifically (UA/behavioral) or challenges (CAPTCHA/anti-bot) → **STOP**, quarantine note, gate item. Never escalate past (b) autonomously.
6. Do-not-collect register (constitution) is enforced in code: collectors for registered sources MUST NOT exist in the repo.

## 5. Per-collector obligations

Each collector MUST: declare a schema contract (fields, types, row-count band vs. trailing 8-week median); validate before store; write `HEALTH.json` on success; ping its heartbeat check (SPEC-03) on success only; quarantine + alarm on drift; be idempotent (re-run safe); finish < 45 min (chunk otherwise); carry a 3-line README (source, cadence, covenant notes, verified date from research §5 — re-verify on build).

## 6. Acceptance criteria (BUILD-01)

- All enabled collectors green 7 consecutive days (heartbeats + manifests).
- Restore drill: pull an arbitrary yesterday snapshot from R2 via the custom domain, revalidate schema, match manifest hash.
- Injected fake drift on one collector quarantines + alarms without polluting `raw/`.
- Covenant review of every collector against §4 passes; C7 (Kroger) confirmed dark pending its gate.
- Storage spend visible in `BUDGET.json`; projection < $5/mo at current cadence.
