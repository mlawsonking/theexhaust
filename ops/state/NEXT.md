# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the orchestrator 2026-07-17.*

> **Prior attempt — 2026-07-27 (WORKER): BLOCKED, precise stop.** All five errands (#9–13) were unverifiable/incomplete — no GitHub repo `theexhaust` exists (so no remote, no push, `ci` never ran there), no R2 creds/bucket/domain, ntfy topic names + healthchecks URL not available to the session, no phone-receipt confirmation. Nothing was wired. **Re-run this same gatecheck** — do not advance to W-001 until it passes. Environment fact for the re-run: the working Python is `C:\ProgramData\miniconda3\python.exe` (Windows `python`/`py` on PATH are only the MS-Store shim); the `vtask` bus was unreachable (Tailscale endpoint timed out) — errands #9–13 are already on the Vikunja `observatory` board, do NOT re-file. Full evidence: buildlog 2026-07-27.

## Item: W-000 — BUILD-00 acceptance gatecheck

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** verify the five operator BUILD-00 errands (Vikunja `observatory` #9–13) are actually complete. Wire nothing beyond the checks. This item exists so the next session builds on real infrastructure, not assumptions.

**Read (only these):** `OBSERVATORY.md` (status block + covenants), `docs/03-GAMEPLAN.md` §6 BUILD-00 paragraph, `ops/SPEC-02` §1, `ops/state/WORKPLAN.md` (W-000/W-001).

**Checks (evidence into the buildlog for each):**
1. Git remote `theexhaust` exists, public, and `git push` succeeds; the `ci` Actions run on GitHub is green.
2. R2: Actions secrets present (names per SPEC-02 env contract: `R2_BUCKET`, `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`); a local boto3 list/put/get round-trip works with those creds (install boto3 if absent; add to requirements confirmed).
3. The bucket's **custom domain** serves a test object over HTTPS (never raw `r2.dev`).
4. ntfy: all three topics accept a test publish; note titles sent; the operator confirms phone receipt (if unconfirmed, say so plainly — do not mark passed).
5. healthchecks.io: project exists; one test check created + pinged.

**Pass →** mark W-000 `done` in WORKPLAN, draft NEXT.md for **W-001** (copy its WORKPLAN entry + anything you learned that the next session needs), buildlog entry, run the full suite (protocol §5), commit, save memory, die.

**Any check fails →** report EXACTLY which Vikunja task is incomplete and in what way (the missing secret name, the DNS state, the 403 body). Mark W-000 `blocked(<which>)`. Do NOT partially wire, do NOT work around, do NOT proceed to W-001. A precise stop is a successful session.
