# WORKBOOK: Shadow Recalls (NHTSA)

*SPEC-07 workbook. Authored 2026-07-28 by the W-006 worker **before any result was computed** —
its purpose is to freeze the two things `PRE-REGISTRATION-v1.md` deliberately deferred to the
workbook: the **component grouping** (§2) and the **hazard lexicon** (§3, feature 5). The
executable half is [`retrocast/nhtsa_recalls/lexicon.py`](../../retrocast/nhtsa_recalls/lexicon.py)
(hyphenated directories are not importable, so the code sits in the underscore sibling package
while every registration-pinned path — the registration, `results/v1/`, `REPORT.md` — stays in
`retrocast/nhtsa-recalls/`);
this file is its human-readable rationale. Committed ahead of `results/v1/` — git ordering is the
receipt (SPEC-08 §2).*

```
slug: nhtsa-recalls    family: product-safety    engine: E3 + retrocast harness (SPEC-08)
verdict_ref: research §4.1 / §5 (NHTSA ODI flat files — GREEN, re-verified live 2026-07-13)
corpora: NHTSA ODI FLAT_CMPL (complaints, signal) + FLAT_RCL_POST_2010 (recalls, ground truth),
         both as ARCHIVED VINTAGES in R2 (collector C4), never live endpoints
official_number: NHTSA recall announcements (continuous; lag removed = complaint-signature ->
         official recall gap, published as a lead-time distribution)
tier: aggregate  (named watchlist = a separate future gate, after a published track record)
```

---

## Retrocast spec

Frozen in [`PRE-REGISTRATION-v1.md`](../../retrocast/nhtsa-recalls/PRE-REGISTRATION-v1.md)
(commit `e3d4d84`, 2026-07-13) — signal, labels, unit, splits, leak controls, dumb baselines and
the §7 publish bars. **This workbook does not restate or amend any of it.** It records only the
two frozen-in-workbook items plus the implementation choices the registration leaves open, all
made blind to outcomes.

### 1. Data of record (vintages used by v1)

| side | R2 key (via `archive.theexhaust.org`) | sha256 | rows |
|---|---|---|---|
| signal | `raw/nhtsa-complaints/2026/07/28/1220-73acbdca6b6f.zip` | `73acbdca6b6f…` | 2,229,384 |
| labels | `raw/nhtsa-recalls/2026/07/28/1220-efab48ed2da2.zip` | `efab48ed2da2…` | 243,126 |

Both hashes re-verified against their manifests at download time. Both were collected in the same
12:20 UTC cycle on 2026-07-28, so signal and labels are one coherent vintage pair.

**Field pinning** (registration §1 pins names "to the archived record-layout at C4 build";
positions confirmed against the archived files themselves, 1-indexed):

- Complaints (51 fields): 4 `MAKETXT`, 5 `MODELTXT`, 6 `YEARTXT`, 7 `CRASH`, 9 `FIRE`,
  10 `INJURED`, 11 `DEATHS`, 12 `COMPDESC`, 16 `DATEA`, 17 `LDATE`, 20 `CDESCR`.
- Recalls (29 fields): 3 `MAKETXT`, 4 `MODELTXT`, 5 `YEARTXT`, 7 `COMPNAME`, 16 `RCDATE`
  (report-received date = the event date, registration §1), 13 `ODATE` (owner-notification —
  **not** used; it post-dates the event).

**As-known-then date.** The registration says complaints enter the trailing window by *date
received*. The file carries two candidates: `DATEA` (date added to file) and `LDATE` (date
received by ODI). Measured on this vintage: identical on 2,016,520 rows, `DATEA` later on
194,986, `LDATE` later on 17,878. v1 uses **`max(DATEA, LDATE)`** — strictly the more
conservative of the two, so no complaint can enter a window earlier than either date admits.
This is a leak control, not a tuning knob.

### 2. Component grouping — FROZEN (registration §2)

Top level = the text before the first `:` in `COMPDESC` / `COMPNAME`, then canonicalized by the
crosswalk in `lexicon.py`.

**Why a crosswalk exists at all** (the W-006 order's named catch — *"component-taxonomy mismatch
vs the layout doc → freeze the mapping in the workbook and note it; never bend the spec
silently"*): the two files do not share one vocabulary. Measured on these vintages, 40 top-level
values appear in both, 1 only in recalls, 13 only in complaints — and several pairs are the same
physical system under old (recall) vs modern (complaint) labels:

| system | complaints file | recalls file |
|---|---|---|
| brakes | `SERVICE BRAKES` 71,981 · `SERVICE BRAKES, HYDRAULIC` 7,844 | `SERVICE BRAKES, HYDRAULIC` 6,578 · `SERVICE BRAKES` 576 |
| engine | `ENGINE` 152,783 · `ENGINE AND ENGINE COOLING` 15,249 | `ENGINE AND ENGINE COOLING` 6,119 · `ENGINE` 693 |
| fuel/propulsion | `FUEL/PROPULSION SYSTEM` 55,484 · `FUEL SYSTEM, GASOLINE` 12,195 | `FUEL SYSTEM, GASOLINE` 11,441 · `FUEL/PROPULSION SYSTEM` 8 |
| visibility | `VISIBILITY/WIPER` 22,245 · `VISIBILITY` 8,667 | `VISIBILITY` 5,380 · `VISIBILITY/WIPER` 345 |

Joining raw top levels would have silently broken the label join for whole systems — a brake
complaint would essentially never match a brake recall. The crosswalk merges (a) that vocabulary
drift, (b) two spelling variants (`COMMUNICATIONS`, `ELECTRONIC STABILITY CONTROL`), (c) the
child-seat sub-component labels that exist only complaint-side, and (d) the residual
`OTHER`/`NONE`/blank labels into one `UNKNOWN OR OTHER` bucket. Systems that both vocabularies
use consistently are **kept separate** (parking brake, traction control, wheels vs tires,
equipment vs adaptive equipment, the three ADAS groups, power train vs engine, interior vs
exterior lighting). The mapping was authored from label semantics and corpus structure only —
no version of it was scored against outcomes.

### 3. Hazard lexicon — FROZEN (registration §3, feature 5)

82 terms in `lexicon.HAZARD_TERMS`, grouped by hazard family: fire/thermal, loss of motive
power, braking, steering/control, unintended acceleration, structural/wheels/tires, restraints,
crash-and-harm outcome language, electrical, rollaway/closures. Matching is a **word-boundary
n-gram match** on the upper-cased `CDESCR` narrative — so `MISFIRE` and `FIREWALL` do not count
as `FIRE`. Inflections are enumerated explicitly rather than stemmed: a frozen list is auditable
by a hostile reviewer, a stemmer is not. `hazard_lang` for a cell-week is the fraction of the
trailing complaints whose narrative matches ≥1 term. **No LLM anywhere in the signal** — the
constitution's spend covenant and the reproducibility doctrine both require the core signal to be
deterministic and rerunnable by a critic with no API key.

### 4. Implementation choices the registration leaves open (all made before results)

1. **`rate_ratio` denominator.** "Trailing-52-week baseline mean" is implemented as the cell's
   own trailing-52-week complaint count scaled to a 12-week window (`count52 × 12/52`), so the
   ratio is dimensionless and 1.0 means "this cell is running at its own recent normal". Because
   the 12-week window is inside the 52-week window, `n_trailing ≥ 1 ⇒ baseline > 0`; the ratio is
   never 0/0 on a scored cell-week.
2. **Scored universe.** Cell-weeks with `n_trailing = 0` are unscorable by construction (no
   complaints ⇒ no rate, no severity fraction, no hazard fraction) and can never cross any
   positive threshold. v1 therefore scores cell-weeks with `n_trailing ≥ 1`. The count of
   excluded cell-weeks and the base rate that would result from including them are **published in
   the report** — the base-rate honesty item of the hostile review is answered with the number,
   not with silence.
3. **Cell key normalization.** Make/model upper-cased and whitespace-collapsed; model-year kept
   as a 4-digit token, with missing/unknown collapsed to `9999` **on both sides**, so an
   unknown-year complaint can only match an unknown-year recall.
4. **No product-type filter.** The registration names no filter, so none is applied: vehicle,
   equipment, tire and child-seat records are all in, joined on the same keys on both sides.
5. **Horizon-spillover guard (registration §5d).** Cell-weeks whose 26-week horizon straddles the
   train/test boundary are dropped from scoring entirely, and an event is evaluated for
   event-recall/lead-time only where its full 26-week pre-window lies inside its own split's
   observation window. Events remain present for *labelling* in both splits — dropping them there
   would mislabel legitimate positives as negatives.
6. **Right-censoring.** The last scored week is 2025-12-31, whose horizon ends 2026-06-30 — inside
   the 2026-07-28 labels vintage, so no scored cell-week is short of label coverage. Recalls
   received in the last days before the vintage may not yet appear in the file; this affects only
   the final ~4 weeks of label coverage and is disclosed.

## Methodology v0

Signal: the five registration §3 features per (make, model, model-year, component-group) × week,
computed only from complaints received ≤ t; scored by a logistic regression fit on the train
window only, with the pre-registered interpretable threshold rule reported alongside. Entity
resolution: none required — the join is a hard make/model/year/component key inside one
government ecosystem (registration §0). Known biases stated in the report: complaint reporting is
voluntary and media-sensitive; recall *report-received* dates are administrative, not the moment
the defect became known; the component crosswalk is a judgement call and is published.

## Artifacts

Monthly category hazard-pressure chart; anomaly artifact at category z>3; piggyback artifact on
every NHTSA recall announcement ("signal history for this MMY", receipts linked). None ship until
the launch gate — v1's only artifact is the retrocast report and its scorecard.

## Alarms

Volume bands and staleness expectations are inherited from the C4 collector (SPEC-01/03). Index
alarms (divergence vs the official series, calibration-band breach) are wired at launch, reading
the calibration bands published by this retrocast (SPEC-08 §6, the Google-Flu-Trends clause).

## Weekly jobs

`complaints-delta compute` (<15 min) and `monthly index recompute + artifact batch` — specified
here, **not enabled**: they go live only through the launch gate.

## Covenant notes

Aggregate-only at launch; the naming-gate clock starts at retrocast publication, and a named tier
would additionally require the frozen editorial rubric plus written operator sign-off
(constitution covenant 2). Both corpora are official, free, bulk, and already archived — no
scraping, no ToS surface, nothing adjacent to the do-not-collect register. Framing is
measurement, never prediction: the claim class is "this cell accumulated complaints matching the
pre-recall signature of N/M historical campaigns at similarity Y", past tense, receipts attached.
