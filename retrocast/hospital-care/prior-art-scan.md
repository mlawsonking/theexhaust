# Prior-art scan — Hospital/Care Distress (PBJ staffing → CMS harm deficiencies)

*Run 2026-07-29, before the v1 pre-registration was frozen. Logged per the constitution's
prior-art rule and [SPEC-08](../../ops/SPEC-08-retrocast-harness.md) §6. The rule exists because
J-14 ("poverty-timed pricing") was pre-registered as novel and turned out to be a published null
result someone had already run.*

## Verdict

**This join is not novel, and the registration does not claim it is.** The association between
nurse-staffing levels and nursing-home deficiency citations is one of the most heavily studied
relationships in long-term-care services research, and CMS itself already publishes star ratings
derived from *both* of these exact datasets. The index proceeds under the constitution's
**replicate-then-run** doctrine: reproduce a known-tractable relationship, then keep it running
forever with a public precision/recall scorecard, which is the part nobody maintains.

## What is established (and therefore must not be claimed as a discovery)

| Finding | Source |
|---|---|
| Higher total / RN / LPN / CNA hours-per-resident-day correlate with fewer and less severe deficiency citations; re-estimated on PBJ 2017–2019 across 11,261 homes | [JAMDA 2024, "The Relationship between Nursing Home Staffing and Health Outcomes Revisited"](https://www.jamda.com/article/S1525-8610(24)00503-6/fulltext) |
| Facilities cited with immediate-jeopardy deficiencies have, as a class, poor survey histories and low staffing | [Center for Medicare Advocacy — IJ deficiencies during the pandemic](https://medicareadvocacy.org/special-report-nursing-homes-cited-with-immediate-jeopardy-deficiencies-during-pandemic-poor-health-inspection-results-low-staffing-levels/) |
| Daily staffing is highly variable, weekend levels fall far below weekday, and 54% of facilities met expected staffing <20% of the time — i.e. **instability is a distinct construct from level** | [Geng, Stevenson & Grabowski, *Health Affairs* 2019](https://www.healthaffairs.org/doi/10.1377/hlthaff.2018.05322) |
| Staffing **instability** has already been proposed as an input to the Five-Star staffing composite | [*Health Affairs Scholar* 2024, "Incorporating staffing instability in the nursing home Five-Star Staffing Composite"](https://academic.oup.com/healthaffairsscholar/article/2/12/qxae159/7923974) |
| PBJ enables substantially more reliable staffing measurement than the prior self-reported snapshot | [Payroll-Based Staffing Measures for Nursing Homes (PMC6846848)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6846848/) |
| ~5% of deficiencies in the last survey cycle reach actual harm or immediate jeopardy; deficiency severity distributions are routinely published | [KFF — A Closer Look at Deficiencies in Nursing Homes](https://www.kff.org/medicaid/a-closer-look-at-deficiencies-in-nursing-homes/) |
| CMS's own use of staffing data for oversight has been formally reviewed | [HHS OIG OEI-04-22-00550 (June 2025)](https://www.aapc.com/codes/webroot/upload/general_pages_docs/document/OEI-04-22-00550.pdf) |

**Direct consequences for the registration, all binding:**

1. Because staffing *level* is already a published CMS star rating, **level alone is a dumb
   baseline, not a result.** §6 makes `hprd_total` alone one of the two baselines that must be
   beaten.
2. Because the literature is overwhelmingly **cross-sectional**, the only thing worth grading is
   whether the signature adds information **over the facility's own citation history** — so
   prior-harm rate is the second, harder baseline.
3. Because staffing instability is already a *proposed* rating input, finding that it predicts harm
   would confirm existing work, not extend it. The report must say so.

## What is *not* occupied

A sweep for prospective / early-warning / lead-time prediction of nursing-home harm or
immediate-jeopardy citations returned clinical patient-deterioration ML (CONCERN, medRxiv early-
warning models) and qualitative F-tag content analyses — **not** a facility-level staffing→harm
forecasting model with a published, falsifiable precision/recall and lead-time scorecard, and not
one running live. As with NHTSA, The Exhaust's contribution is **not methodological novelty**: it is
*live + public + pre-registered + scored in the open, including when it fails.*

## Method and limits of this scan

Four targeted searches (PBJ→deficiency prediction; staffing↔harm/IJ severity; prospective ML early
warning for IJ citations; the weekend/instability construct) across the open literature and
government reports, 2026-07-29. This is the constitution's *15-minute* sweep, not a systematic
review: it is sufficient to establish that the relationship is known and that the scorecard lane is
empty, and it would not reliably surface an unpublished or paywalled forecasting model. If one
surfaces later, it belongs in the report's limitations, not in a quiet edit here.
