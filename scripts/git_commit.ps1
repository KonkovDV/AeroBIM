# Single-author commit (no Co-authored-by trailers).
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts/git_commit.ps1 -Message "docs: update README"

param(
    [Parameter(Mandatory = $true)]
    [string]$Message
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$env:GIT_AUTHOR_NAME = "KonkovDV"
$env:GIT_COMMITTER_NAME = "KonkovDV"
$env:GIT_AUTHOR_EMAIL = "KonkovDV@users.noreply.github.com"
$env:GIT_COMMITTER_EMAIL = "KonkovDV@users.noreply.github.com"

if ($Message -match "(?i)Co-authored-by:") {
    throw "Message must not contain Co-authored-by trailers."
}

$msgFile = Join-Path $env:TEMP ("aerobim-gitmsg_{0}.txt" -f [guid]::NewGuid().ToString("N"))
try {
    [System.IO.File]::WriteAllText($msgFile, $Message.TrimEnd() + "`n", [System.Text.UTF8Encoding]::new($false))
    git add -A
    if ($LASTEXITCODE -ne 0) { throw "git add failed" }
    git commit --no-verify -F $msgFile
    if ($LASTEXITCODE -ne 0) { throw "git commit failed" }
    $body = git log -1 --format="%B"
    if ($body -match "(?i)Co-authored-by:") {
        throw "Commit still contains Co-authored-by; amend or disable Cursor Attribution."
    }
    Write-Host "OK: $(git log -1 --oneline)"
}
finally {
    Remove-Item -LiteralPath $msgFile -Force -ErrorAction SilentlyContinue
}
