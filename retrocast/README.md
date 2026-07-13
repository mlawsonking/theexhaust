# retrocast/ — the credibility engine (SPEC-08)

Every index publishes only through this harness: a **pre-registration committed before any result**, run against the **retrocast-of-record** (archived flat-file vintages, never live endpoints), producing a full P/R curve + lead-time distribution + calibration + a per-case receipts table, graded against pre-registered bars.

The git history that a `PRE-REGISTRATION` commit **predates** its results commit is the field-wide differentiator (research §13.4) made mechanical and unforgeable.

| Path | What |
|---|---|
| `retrocast/<index>/PRE-REGISTRATION-v{n}.md` | the frozen spec — signal, labels (source+vintage+hash), controls, splits+leak controls, thresholds — committed **before** results |
| `retrocast/<index>/prior-art-scan.md` | the logged scholarly sweep (constitution / SPEC-08 §6) |
| `retrocast/<index>/results/v{n}/` | P/R curve, lead-time dist, calibration, per-case scored table (receipts), `scorecard.json` |
| `retrocast/<index>/REPORT.md` | the human-readable, hostile-review-proof report page |
| `retrocast/DEAD-REGISTRATIONS.md` | failed/abandoned retrocasts, published with autopsies (a killed index builds trust too) |

Doctrine: **never predict, only measure** · methodology change ⇒ new version ⇒ full backtest republication · a spec change *after seeing results* is a *new* pre-registration with the prior attempt disclosed here.
