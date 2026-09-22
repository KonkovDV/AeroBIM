# =============================================================================
# AeroBIM -- Universal Demo Setup Script (Windows PowerShell)
# =============================================================================
#
# Использование:
#   .\deploy\demo\setup-demo.ps1              # авто-выбор
#   .\deploy\demo\setup-demo.ps1 -Mode cli   # CLI жюри
#   .\deploy\demo\setup-demo.ps1 -Mode ui    # UI оболочка
#   .\deploy\demo\setup-demo.ps1 -Mode docker        # Docker API
#   .\deploy\demo\setup-demo.ps1 -Mode docker-full   # Docker API + Vite UI
#   .\deploy\demo\setup-demo.ps1 -Mode airgap        # Air-gap Docker
#
# Если ExecutionPolicy блокирует скрипт:
#   powershell -ExecutionPolicy Bypass -File .\deploy\demo\setup-demo.ps1
# =============================================================================
[CmdletBinding()]
param(
  [ValidateSet('auto','cli','ui','docker','docker-full','airgap')]
  [string]$Mode = 'auto'
)
$ErrorActionPreference = 'Stop'
$RepoRoot = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $RepoRoot

function Info  { param($m) Write-Host "[AeroBIM] $m" -ForegroundColor Cyan }
function Ok    { param($m) Write-Host "[  OK  ] $m" -ForegroundColor Green }
function Warn  { param($m) Write-Host "[ WARN ] $m" -ForegroundColor Yellow }
function Die   { param($m) Write-Host "[ FAIL ] $m" -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------------------
# Авто-выбор режима
# ---------------------------------------------------------------------------
if ($Mode -eq 'auto') {
  Info "Auto-detecting best demo mode..."
  if (Get-Command docker -ErrorAction SilentlyContinue) {
    try { docker info 2>$null | Out-Null; $Mode = 'docker'; Info "Docker found => Mode C (docker)" }
    catch { $Mode = '' }
  }
  if ($Mode -eq 'auto' -or $Mode -eq '') {
    if (Get-Command py -ErrorAction SilentlyContinue) {
      try {
        py -3.12 --version 2>$null | Out-Null
        if (Get-Command node -ErrorAction SilentlyContinue) {
          $Mode = 'ui'; Info "Python 3.12 + Node found => Mode B (ui)"
        } else {
          $Mode = 'cli'; Info "Python 3.12 found (no Node) => Mode A (cli)"
        }
      } catch { Die "No Docker, no py -3.12. Install Docker Desktop or CPython 3.12." }
    } else {
      Die "No Docker, no py launcher. Install Docker Desktop or CPython 3.12 from python.org."
    }
  }
}

# ---------------------------------------------------------------------------
# Режим A: CLI жюри
# ---------------------------------------------------------------------------
if ($Mode -eq 'cli') {
  Info "Mode A: CLI jury demo (Python 3.12 only)"
  & "$RepoRoot\run-jury.bat"
  exit $LASTEXITCODE
}

# ---------------------------------------------------------------------------
# Режим B: UI оболочка
# ---------------------------------------------------------------------------
if ($Mode -eq 'ui') {
  Info "Mode B: Review shell demo (Python 3.12 + Node 20+)"

  $py = Get-Command py -ErrorAction SilentlyContinue
  if (-not $py) { Die "py launcher not found. Install CPython 3.12 from python.org." }
  try { py -3.12 --version 2>$null | Out-Null } catch { Die "py -3.12 not found." }

  $venv = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
  if (-not (Test-Path $venv)) {
    Info "Creating backend\.venv with py -3.12..."
    py -3.12 -m venv (Join-Path $RepoRoot "backend\.venv")
  }

  $pyVer = (& $venv -c "import sys; print(sys.version_info[:2])").Trim()
  if ($pyVer -ne '(3, 12)') { Die "backend\.venv is not Python 3.12. Delete it and re-run." }

  Info "Installing Python dependencies..."
  $env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
  & $venv -m pip install -q -U pip
  & $venv -m pip install -q -e "backend\.[dev,raster]"

  $env:AEROBIM_ALLOW_ANONYMOUS_DEV = 'true'
  if (-not $env:AEROBIM_SIGNOFF_PROFILE) { $env:AEROBIM_SIGNOFF_PROFILE = 'customer_pilot_demo' }

  Info "Starting review shell..."
  Ok "API => http://127.0.0.1:8080   UI => http://127.0.0.1:5173"
  & $venv -m aerobim.tools.run_review_stand
  exit $LASTEXITCODE
}

# ---------------------------------------------------------------------------
# Режим C: Docker
# ---------------------------------------------------------------------------
if ($Mode -eq 'docker') {
  Info "Mode C: Docker demo (anonymous API on 127.0.0.1:8080)"
  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Die "docker not found. Install Docker Desktop." }
  try { docker info 2>$null | Out-Null } catch { Die "Docker not running. Start Docker Desktop." }

  Info "Building and starting demo backend..."
  docker compose -f docker-compose.demo.yml up --build -d
  if ($LASTEXITCODE -ne 0) { Die "docker compose failed." }

  Info "Waiting for health check..."
  $tries = 0
  while ($tries -lt 30) {
    try {
      $r = Invoke-WebRequest -Uri http://127.0.0.1:8080/health -UseBasicParsing -TimeoutSec 3
      if ($r.StatusCode -eq 200) {
        Ok "API ready: http://127.0.0.1:8080"
        Ok "Health:    http://127.0.0.1:8080/health"
        Ok "Caps:      http://127.0.0.1:8080/v1/system/capabilities"
        Info "To stop:  docker compose -f docker-compose.demo.yml down"
        Info "To reset: docker compose -f docker-compose.demo.yml down -v"
        exit 0
      }
    } catch {}
    $tries++
    Start-Sleep -Seconds 2
  }
  Die "Health check timed out. Run: docker compose -f docker-compose.demo.yml logs"
}

# ---------------------------------------------------------------------------
# Режим C+: Docker API + Vite UI
# ---------------------------------------------------------------------------
if ($Mode -eq 'docker-full') {
  Info "Mode C+: Docker API + Vite UI on host"
  if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Die "node not found. Install Node 20+." }
  $nodeVer = [int]((node --version) -replace 'v','').Split('.')[0]
  if ($nodeVer -lt 20) { Die "Node $nodeVer found, need 20+." }

  # Запуск Docker backend
  & "$PSCommandPath" -Mode docker

  $frontend = Join-Path $RepoRoot 'frontend'
  $lock = Join-Path $frontend 'package-lock.json'
  if (-not (Test-Path $lock)) { Die "frontend/package-lock.json is missing." }
  $compose = Join-Path $RepoRoot 'docker-compose.demo.yml'
  Info "Installing frontend dependencies from the lockfile..."
  Push-Location $frontend
  try {
    npm ci
    if ($LASTEXITCODE -ne 0) { Die "npm ci failed." }
    $env:VITE_API_BASE_URL = 'http://127.0.0.1:8080'
    Info "Starting Vite frontend... UI => http://127.0.0.1:5173"
    $vite = Start-Process -FilePath 'npm' -ArgumentList 'run','dev' -PassThru -NoNewWindow
    Ok "Frontend started (PID $($vite.Id)). Ctrl+C stops Vite and the demo container."
    Ok "UI  => http://127.0.0.1:5173"
    Ok "API => http://127.0.0.1:8080"
    Wait-Process -Id $vite.Id
  } finally {
    Info "Stopping Vite and the demo container..."
    if ($vite -and -not $vite.HasExited) {
      Stop-Process -Id $vite.Id -Force -ErrorAction SilentlyContinue
    }
    docker compose -f $compose down
    Pop-Location
  }
  exit 0
}

# ---------------------------------------------------------------------------
# Режим D: Air-gap
# ---------------------------------------------------------------------------
if ($Mode -eq 'airgap') {
  Info "Mode D: offline image track. This is not customer_pilot_demo."
  Warn "install_offline.ps1 starts the closed-contour image. It does not set AEROBIM_SIGNOFF_PROFILE=customer_pilot_demo."
  Warn "Clash/MEP honesty of the demo profile applies to modes cli, ui, and docker only."
  $bundle = Join-Path $RepoRoot 'artifacts\offline-bundle'
  if (-not (Test-Path $bundle)) {
    Die "Bundle not found at $bundle. Run first (online): cd backend; python -m aerobim.tools.offline_bundle build"
  }
  $installer = Join-Path $bundle 'install_offline.ps1'
  if (-not (Test-Path $installer)) { Die "install_offline.ps1 not found in bundle. Rebuild." }
  Info "Running offline installer..."
  & powershell -ExecutionPolicy Bypass -File $installer
  exit $LASTEXITCODE
}
