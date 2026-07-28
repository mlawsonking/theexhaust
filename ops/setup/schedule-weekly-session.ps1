# Schedule the weekly R2 ops session (SPEC-02 §2 / ops/playbooks/weekly-ops.md).  OPERATOR ACTION.
# W-003 item 4. Registers a Windows Task Scheduler job that runs the weekly gate-report session
# headless every Monday. Review the two DECISIONS below, adjust, then run this from an elevated
# PowerShell in the repo root. Verify afterward:  Get-ScheduledTask -TaskName 'Exhaust Weekly Ops'
#
# ── DECISION 1 — permission mode for an UNATTENDED claude session ────────────────────────────────
# The weekly session must, unattended, run `python -m opscore.weekly`, commit + push the report/state,
# and send ntfy. That needs tool permissions with nobody at the keyboard. Pick ONE and set $ClaudeArgs:
#   (a) settings allowlist (SAFEST): pre-approve exactly the tools it needs in
#       .claude/settings.json (Bash(git ...), Bash(python ...), the ntfy send) and run plain `claude -p`.
#   (b) --permission-mode acceptEdits  (edits auto-approved; bash still prompts unless allowlisted).
#   (c) --dangerously-skip-permissions (SIMPLEST, BROADEST — an unattended agent with no guardrails;
#       only if you accept that posture on this box). This is a security choice — YOU own it, not the
#       build session. Left unset below on purpose so the task won't run until you decide.
# ── DECISION 2 — subscription, not metered API ──────────────────────────────────────────────────
# The weekly session is subscription work (spend covenant #6: metered API is per-run gated, never
# ambient). Ensure the scheduled `claude` resolves to your subscription CLI. Check: (Get-Command claude).Source
# ─────────────────────────────────────────────────────────────────────────────────────────────────

$RepoRoot   = 'C:\Users\bobdo\projects\observatory'
$ClaudeExe  = (Get-Command claude -ErrorAction SilentlyContinue).Source   # or hard-code the full path
$ClaudeArgs = ''   # <-- DECISION 1: e.g. '--dangerously-skip-permissions'  (leave '' and the task is inert)

$Prompt = 'You are the weekly R2 ops session (SPEC-02 §2). Read OBSERVATORY.md to confirm phase, then ' +
          'follow ops/playbooks/weekly-ops.md exactly: run `python -m opscore.weekly`, triage alarms/quarantine, ' +
          'spot-verify one rotating pipeline, execute ONLY operator-decided approvals, commit `weekly ops`, and exit. ' +
          'Do nothing gate-shaped directly — file a gate. No metered API.'

if (-not $ClaudeExe) { Write-Error 'claude not on PATH — hard-code $ClaudeExe to the CLI full path.'; return }

# Runs pwsh -> cd repo -> claude -p "<prompt>"  (single unattended shot).
$inner  = "cd '$RepoRoot'; & '$ClaudeExe' $ClaudeArgs -p '$($Prompt -replace "'","''")'"
$Action = New-ScheduledTaskAction -Execute 'pwsh' -Argument "-NoProfile -NonInteractive -Command `"$inner`""
$Trigger  = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9:00am
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun   # catch up if the box was off
Register-ScheduledTask -TaskName 'Exhaust Weekly Ops' -Action $Action -Trigger $Trigger `
    -Settings $Settings -Description 'The Exhaust weekly R2 gate-report session (SPEC-02 §2).'

Write-Output "Registered 'Exhaust Weekly Ops' (Mondays 09:00). NTFY_* already persisted to User env (W-003)."
Write-Output "Once the SPEC-03 weekly-session healthcheck exists, set HC_WEEKLY in User env so the driver's"
Write-Output "dead-man heartbeat activates (opscore/weekly.py _ping_weekly_heartbeat)."
