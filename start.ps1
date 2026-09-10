# IT-mentor review shell (API + Vite). Not the jury CLI.
# PowerShell:  .\start.ps1   or   .\start.bat
# Do not type: start          (that is Start-Process)
# Do not type: start.bat      (PowerShell will not run a .bat from cwd)
# Explorer: double-click start.bat. CMD: start.bat
# .bat is not blocked by ExecutionPolicy; prefer .\start.bat if this file is blocked.
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$python = Join-Path $PSScriptRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    Write-Host "backend\.venv not found. From AeroBIM\backend:"
    Write-Host "  py -3.12 -m venv .venv"
    Write-Host "  pip install -e `".[dev,raster]`""
    Write-Host "Not the jury CLI. customer_go false."
    exit 1
}
& $python -m aerobim.tools.run_it_mentor_stand @args
exit $LASTEXITCODE
