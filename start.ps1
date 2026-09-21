# Review shell (API + Vite). Not the jury CLI.
# PowerShell:  .\start.ps1   or   .\start.bat
# Do not type: start          (that is Start-Process)
# Do not type: start.bat      (PowerShell will not run a .bat from cwd)
# Explorer: double-click start.bat. CMD: start.bat
# .bat is not blocked by ExecutionPolicy; prefer .\start.bat if this file is blocked.
$ErrorActionPreference = "Stop"
Write-Host "AeroBIM review shell. Vite 127.0.0.1:5173  API 127.0.0.1:8080  (not Next.js)"
Set-Location -LiteralPath $PSScriptRoot
$python = Join-Path $PSScriptRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    Write-Host "backend\.venv not found. From AeroBIM\backend:"
    Write-Host "  py -3.12 -m venv .venv"
    Write-Host "  .venv\Scripts\python.exe -m pip install -e `".[dev,raster]`""
    Write-Host "Review shell needs Node 20+. Jury CLI does not. customer_go false."
    exit 1
}
& $python -m aerobim.tools.run_review_stand @args
exit $LASTEXITCODE
