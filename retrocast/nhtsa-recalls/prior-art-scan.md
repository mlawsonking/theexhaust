# NHTSA Shadow Recalls — prior-art scan (logged per SPEC-08 §6 / constitution)

**Scanned:** 2026-07-13 (web sweep) + research §2/§8/§12 + the Phase-2 deep pass (§13). **Verdict: replicate-then-run — the method is established (low novelty risk); the live-public falsifiable scorecard is unoccupied (the white space holds).**

## The method is NOT novel (this is the point — replicate a known-tractable result, then run it forever)
Complaint→recall forecasting from NHTSA data is an active, established area:
- **99P Labs / "Recall Recon"** — ML + RAG over NHTSA recall campaigns + consumer complaints for early-warning detection (analysis of 5,000+ campaigns, 30,000+ complaints).
- **AWS Industries** — ML to predict automotive part-recall risk from historical patterns.
- **Wipro Digital** — LSTM models learning defect/recall precursors.
- **Upstream Security (2025 report)** — estimates 70% of recalls since 2020 (≈90% of EV recalls) had detectable early signals; the detectable share rose 69% (2020) → 75% (2025).
- **Medical-device analog** — a published FDA medical-device recall ML model (PMC11908527) reporting high sensitivity/specificity at ~12-month lead — the conservative prior behind our lead-time expectations.

Implication for the pre-registration: the task is tractable, so the bars in §7 are set from these priors and deliberately conservative for the noisier vehicle-complaint setting. Failing them is publishable (autopsy), not a reason to move them.

## The live-public falsifiable scorecard is unoccupied (differentiated white space)
Every *live, public* NHTSA-recall tool is a **lookup / search dashboard** (after-the-fact), not a forward early-warning scorecard with published precision/recall + lead-time:
- NHTSA's own interactive recall dashboard, VIN lookup, and Search Safety Issues; `vehiclesafetyrecalls.com`, OBD/vehicle-lookup tools; `data.transportation.gov` recall datasets.
- The forecasting work above is **academic / vendor-internal** (AWS, Wipro, 99P Labs) or a **commercial security vendor's press estimate** (Upstream) — none publishes a free, falsifiable, receipts-attached precision/recall + lead-time scorecard that a hostile PhD can rerun.

The Exhaust's contribution is therefore **operational, not methodological**: live + public + a published retrocast scorecard + receipts + permanence — exactly the field-wide gap confirmed in research §8 and §13.4.

## Sources
- [99P Labs — Recall Recon (ML+RAG on NHTSA)](https://medium.com/99p-labs/recall-recon-a-machine-learning-and-rag-based-system-for-forecasting-automotive-safety-recalls-29f5d858385f)
- [AWS — Predicting automotive part-recall risk with ML](https://aws.amazon.com/blogs/industries/how-machine-learning-on-aws-can-help-customers-predict-the-risk-of-automotive-part-recalls/)
- [Wipro Digital — Reducing vehicle recalls with ML/AI](https://medium.com/@wiprodigital/reducing-vehicle-recalls-with-machine-learning-and-artificial-intelligence-9f9f22a70d61)
- [Upstream Security — 70% of recalls detectable earlier via connected-vehicle data](https://upstream.auto/press-releases/vehicle-recalls-detection-by-using-connected-vehicle-data/)
- [Medical-device recall ML (PMC11908527)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11908527/)
- [NHTSA interactive recall dashboard (lookup, not forecasting)](https://www.nhtsa.gov/press-releases/nhtsa-launches-interactive-searchable-recall-dashboard)
- [DOT recalls dataset (data.gov)](https://catalog.data.gov/dataset/recalls-data)

*Live re-confirmation is repeated at BUILD-03 pre-publication as part of the hostile-review overclaim scan.*
