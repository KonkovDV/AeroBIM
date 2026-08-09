# Run on the primary Windows workstation (signing key 24D8BC0C78AAABA6).
# Stages should already include N-43 / SECURITY / baseline policy / new pubkey.

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$gpg = "C:/Program Files/Git/usr/bin/gpg.exe"
$key = "24D8BC0C78AAABA6"
git config --local gpg.program $gpg
git config --local user.signingkey $key
git config --local commit.gpgsign true

$msg = @"
fix(gov): N-43 baseline lag policy + workstation signing key

Watch max_commits_behind until 17.08 via registry; add local author key 24D8BC0C78AAABA6 (B5690 secret is on another machine); document unregistered-key exit 2; draw DrawingRegionRef overlays.
"@

git commit -S$key -m $msg
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git log -1 --format="%H %G? %GS %s"
Write-Host "Next: upload governance/trusted_signing_keys/24D8BC0C78AAABA6.asc to https://github.com/settings/keys then git push origin HEAD"
