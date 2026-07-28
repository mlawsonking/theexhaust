# NEXT — the current work order

*Read this, execute exactly this, hand off per [`ops/BUILD-PROTOCOL.md`](../BUILD-PROTOCOL.md) §2. Drafted by the W-000 worker at hand-off, 2026-07-27.*

## Item: W-001 — R2 backend live + restore drill

**You are a WORKER session. Model check:** Phase 4 implementation = Opus-class session. If you are not, STOP and say so.

**Mission:** the collector fleet writes to **real R2** (BUILD-00 is now green — repo/CI/R2/custom-domain/ntfy/healthchecks all verified 2026-07-27), and prove a snapshot can be restored from R2. Close the loop between "collector runs" and "durable, recoverable archive."

**Read (only these):** `collectors/framework.py`, `collectors/run.py`, `ops/SPEC-01` §3 (storage/manifest) + §6 (restore drill + acceptance).

**Environment — read before you run anything (learned in W-000):**
- Working Python interpreter is **`C:\ProgramData\miniconda3\python.exe`** — the Windows `python`/`py` on PATH are only the MS-Store shim and fail. **boto3 1.43.57 is already installed** there.
- `collectors/run.py::select_storage` auto-selects `R2Backend` when **`R2_BUCKET` + `R2_ENDPOINT`** are in the env (also needs `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`); else it falls back to `LocalFSBackend`. So a real-R2 run just needs those four env vars present in the process you launch.
- **Cred-propagation gotcha:** `setx` persists to the registry but only a *freshly launched* process sees it; a long-running agent's spawned shells do **not** inherit it. The four validated `R2_*` values from W-000 lived in that session's scratchpad `r2-creds.env`, which is **gone this session**. Options, in order: (a) if a fresh shell already has the four `R2_*` set (operator ran `setx` to persist them), just use them; (b) else ask the operator to confirm/redo the persist, or source a creds file into the env for the run. Never hardcode creds; never commit them.
- R2 endpoint in use: `https://112ede6f1cef9259e072f1300492dec3.r2.cloudflarestorage.com`; bucket `exhaust-archive`; public read via **`https://archive.theexhaust.org/<key>`** (custom domain — never `r2.dev`). A W-000 test object exists at `test/roundtrip.txt` (safe to leave or delete).

**Do (SPEC-01 §3/§6):**
1. `pip install boto3` into CI's install step (already local; add to `.github/workflows/ci.yml` install so R1 has it too).
2. Run each of the **6 verified collectors** once against R2 (`--verify` OFF so it uses `select_storage`, env creds present): `cms-deficiencies` (C1), `cpsc-recalls` (C5), `nhtsa-recalls` (C4), `fdic-failures` (C9), `ats-boards` (C3), + the sixth per `run.py` REGISTRY. Confirm each stores-or-dedupes with a manifest in R2.
3. **Restore drill (SPEC-01 §6):** pull a stored snapshot back — via the custom domain `https://archive.theexhaust.org/<key>` and/or boto3 `get` — revalidate its schema, and match the manifest content-hash. Prove byte-integrity round-trips.
4. Update `ops/state/BUDGET.json` storage figures with the actual bytes landed (keep the `< $5/mo` projection honest).
5. Add **`ci/run_all.py`** that runs the §5 suite verbatim and exits nonzero on any failure; switch `ci.yml` to call it (it becomes the one-liner the protocol references).

**Accept:** 6 collectors stored-or-unchanged against R2 (evidence: keys + manifest hashes in the buildlog); restore drill passes (hash match shown); `ci/run_all.py` green locally and wired into CI.

**Catches (pre-written — use the decision tree, don't improvise):**
- R2 auth fails → re-check the four secret **names** against the SPEC-02 env contract and that the env is actually populated in *this* process **before** touching any code.
- A collector fails live → its per-collector quarantine/pause semantics ARE the fallback; store-anomalous-and-flag, never edit-the-schema-to-pass.
- Datacenter-403 from a source → the SPEC-01 §4.5 ladder (operator-box fallback at identical politeness; log the switch). Bot-challenge/CAPTCHA → STOP + gate, never evade.

**Hand off:** buildlog entry with evidence → mark W-001 in WORKPLAN → draft NEXT.md for **W-002** (Actions cron fleet + the 367 MB complaints pull) → full §5 suite green → commit → save memory → die.
