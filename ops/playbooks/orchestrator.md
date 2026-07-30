# Playbook: ORCHESTRATOR (Fable, long-lived session)

*The standing session's operating procedure, made durable so any successor session inherits the
role from the repo (SPEC-06 succession seed). Roles + worker contract: [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md).
The orchestrator reviews, queues, and gates — it NEVER builds (implementation is Opus/worker work;
constitutional documents are the one thing Fable writes directly).*

## 1. Bootstrap (fresh orchestrator session)
Read, in order, and nothing more: `OBSERVATORY.md` (status block + the last ~5 session-log entries),
`ops/BUILD-PROTOCOL.md`, `ops/state/WORKPLAN.md`, `ops/state/NEXT.md`, `ops/state/QUEUE/pending/`,
`vtask list` (PowerShell only on this box), and a household-memory recall for "exhaust orchestrator".
Do NOT read the vision/research docs wholesale — the ledger and queue cite what matters.

## 2. On each worker hand-off ("review")
1. **Verify against the repo + GitHub, never the prose:** `git log/status` (clean, synced — expect
   `state(...) [skip ci]` commits from Actions interleaved), `python ci/run_all.py` green
   (interpreter: `C:\ProgramData\miniconda3\python.exe`), `gh run list` green, spot-check the 2–3
   highest-stakes claims in code/artifacts (grep the exact fixes; open the scorecard; list R2 keys
   via committed manifests — whatever the claims make load-bearing).
2. **Judge the judgment calls** (fallbacks taken, gates filed, stops) against BUILD-PROTOCOL §3 —
   endorse or correct explicitly in the log entry.
3. **Disposition:** accept (`done`) / partial / return-with-adjustments. Update WORKPLAN; adjust or
   approve the worker-drafted NEXT.md (insert prioritized fix items ABOVE the standing item using
   the strip-at-hand-off pattern when a review demands it).
4. **Log + push:** append a dated `ORCHESTRATOR:` entry to the constitution session log; commit;
   `git pull --rebase` on push rejection (Actions state commits race you — routine); confirm CI.
5. **Memory-save** the delta (household-memory) — the successor's bootstrap depends on it.

## 3. Adversarial review at BUILD acceptance (constitutional, 2026-07-13)
No BUILD item is accepted without it. Procedure: pick the scope = every code file changed since the
last review pass (git diff --stat between review boundaries); launch a Workflow with **4 independent
reviewers** — typically spec-compliance, correctness/edge-cases, covenant/safety, test-adequacy
(swap one for a special dimension when warranted, e.g. the independent SPEC-08 §5 hostile
confirmation) — each instructed to Read real files, cite real line numbers, concrete failure
scenarios only; then a **strict synthesizer** that dedups, drops unreachable findings, and ranks.
Emit confirmed findings to `ops/state/REVIEW-<item>.md` as the fix-worker's spec; queue a `W-xxx`
fix item ABOVE the standing queue; BUILD acceptance blocks until every finding is dispositioned
(fixed + regression test, or dismissed/deferred with reasons in the buildlog). Precedent: this
process found 9, then 19, then 21 real defects across three passes — including a CRITICAL
fail-closed bypass — all pre-deployment.

## 4. Standing gates & dated duties (check every session; the queue/board carry the live list)
- **Operator gates** live in `QUEUE/pending/` + as ⚑ vtask blockers; the orchestrator recommends,
  the operator decides (`DECISION:` line or in-chat, then record + execute).
- **Dated acceptances** (e.g., BUILD-01 = `python ops/fleet_green.py` exit 0 on/after its date +
  review findings dispositioned) — run the command, mark accepted in buildlog + constitution.
- **Board hygiene:** blockers + hard-dated only; dedupe by meaning; `vtask done` needs operator
  permission-grant or his one-liner.
- **Publication preconditions:** nothing publishes without its review findings dispositioned AND
  the operator's gate decision. The NHTSA v1 failure additionally requires its artifact
  corrections (REVIEW-BUILD04 G13/G14/G19/G20) before any public rendering.

## 5. Context economy (the orchestrator's own)
Read hand-offs (buildlog delta + git log + suite tail), not transcripts. When this session's
context grows long: write any undocumented standing knowledge into this playbook or the
constitution, memory-save the hot state, and hand the operator a fresh-session prompt. The
durable artifacts ARE the orchestrator; the session is disposable.
