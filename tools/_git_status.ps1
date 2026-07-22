# ── Dynamic project root: tools/_git_status.ps1 → up one level ──────────
$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $toolsDir
Set-Location $projectRoot
git status > _git_out.txt
git log -1 --name-status >> _git_out.txt
git diff --name-only origin/main >> _git_out.txt
Get-Content _git_out.txt
