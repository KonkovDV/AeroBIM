@echo off
rem ==========================================================================
rem AeroBIM -- Universal Demo Setup Script (Windows CMD / Explorer)
rem ==========================================================================
rem
rem Использование:
rem   Explorer: двойной щелчок.
rem   CMD:      deploy\demo\setup-demo.bat [cli|ui|docker|airgap]
rem   PowerShell: .\deploy\demo\setup-demo.bat [cli|ui|docker|airgap]
rem
rem Режимы:
rem   cli    -- Режим A: CLI жюри (только Python 3.12, без Node, без Docker)
rem   ui     -- Режим B: UI оболочка (Python 3.12 + Node 20+)
rem   docker -- Режим C: Docker demo (API, анонимный доступ)
rem   airgap -- Режим D: air-gap Docker из tar-бандла
rem   (не указан) -- авто-выбор
rem ==========================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0\..\.."
title AeroBIM Demo Setup
chcp 65001 >nul
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
set PIP_DISABLE_PIP_VERSION_CHECK=1

set MODE=%~1
if "%MODE%"=="" set MODE=auto

echo.
echo ============================================================
echo   AeroBIM Demo Setup  --  Mode: %MODE%
echo ============================================================
echo.

if /i "%MODE%"=="auto" goto :auto_detect
if /i "%MODE%"=="cli"  goto :mode_cli
if /i "%MODE%"=="ui"   goto :mode_ui
if /i "%MODE%"=="docker" goto :mode_docker
if /i "%MODE%"=="airgap" goto :mode_airgap
echo FAIL: Unknown mode '%MODE%'. Use: cli ui docker airgap
echo.
pause
exit /b 1

:auto_detect
echo Auto-detecting best demo mode...
docker info >nul 2>&1
if not errorlevel 1 (
  echo Docker found => Mode C (docker)
  set MODE=docker
  goto :mode_docker
)
where py >nul 2>&1
if not errorlevel 1 (
  py -3.12 --version >nul 2>&1
  if not errorlevel 1 (
    where node >nul 2>&1
    if not errorlevel 1 (
      echo Python 3.12 + Node found => Mode B (ui)
      set MODE=ui
      goto :mode_ui
    )
    echo Python 3.12 found (no Node) => Mode A (cli)
    set MODE=cli
    goto :mode_cli
  )
)
echo FAIL: No Docker, no py -3.12 found.
echo Install Docker Desktop or CPython 3.12 from python.org.
pause
exit /b 1

:: -----------------------------------------------------------------------
:: Режим A: CLI жюри
:: -----------------------------------------------------------------------
:mode_cli
echo [Mode A] CLI jury demo (Python 3.12 only).
call run-jury.bat
goto :end

:: -----------------------------------------------------------------------
:: Режим B: UI оболочка (Python 3.12 + Node 20+)
:: -----------------------------------------------------------------------
:mode_ui
echo [Mode B] Review shell demo.

where py >nul 2>&1 || goto :no_py
py -3.12 --version >nul 2>&1 || goto :no_py312

if not exist "backend\.venv\Scripts\python.exe" (
  echo Creating backend\.venv with py -3.12...
  py -3.12 -m venv backend\.venv
  if errorlevel 1 goto :fail
)

backend\.venv\Scripts\python.exe -c "import sys; raise SystemExit(0 if sys.version_info[:2]==(3,12) else 1)"
if errorlevel 1 (
  echo backend\.venv is not Python 3.12. Delete backend\.venv and re-run.
  goto :fail
)

echo Installing Python dependencies...
backend\.venv\Scripts\python.exe -m pip install -q -U pip
if errorlevel 1 goto :fail
backend\.venv\Scripts\python.exe -m pip install -q -e "backend\.[dev,raster]"
if errorlevel 1 goto :fail

set AEROBIM_ALLOW_ANONYMOUS_DEV=true
if "%AEROBIM_SIGNOFF_PROFILE%"=="" set AEROBIM_SIGNOFF_PROFILE=customer_pilot_demo

echo Starting review shell...
echo API => http://127.0.0.1:8080   UI => http://127.0.0.1:5173
backend\.venv\Scripts\python.exe -m aerobim.tools.run_review_stand
goto :end

:: -----------------------------------------------------------------------
:: Режим C: Docker
:: -----------------------------------------------------------------------
:mode_docker
echo [Mode C] Docker demo (anonymous API on 127.0.0.1:8080).

docker info >nul 2>&1 || (
  echo FAIL: Docker not running. Start Docker Desktop.
  goto :fail
)

echo Building and starting demo backend...
docker compose -f docker-compose.demo.yml up --build -d
if errorlevel 1 goto :fail

echo Waiting for health check...
set /a TRIES=0
:health_loop
set /a TRIES+=1
curl -sf http://127.0.0.1:8080/health >nul 2>&1
if not errorlevel 1 (
  echo   OK  API ready: http://127.0.0.1:8080
  echo   OK  Health:    http://127.0.0.1:8080/health
  echo   OK  Caps:      http://127.0.0.1:8080/v1/system/capabilities
  echo To stop:  docker compose -f docker-compose.demo.yml down
  echo To reset: docker compose -f docker-compose.demo.yml down -v
  goto :end
)
if %TRIES% GEQ 30 (
  echo FAIL: Health check timed out.
  echo Run: docker compose -f docker-compose.demo.yml logs
  goto :fail
)
timeout /t 2 /nobreak >nul
goto :health_loop

:: -----------------------------------------------------------------------
:: Режим D: Air-gap
:: -----------------------------------------------------------------------
:mode_airgap
echo [Mode D] Offline image track. This is not customer_pilot_demo.
echo install_offline.ps1 starts the closed-contour image.
echo It does not set AEROBIM_SIGNOFF_PROFILE=customer_pilot_demo.
echo Clash/MEP honesty of the demo profile applies to cli, ui, and docker only.

docker info >nul 2>&1 || (
  echo FAIL: Docker not running.
  goto :fail
)

set BUNDLE_DIR=%~dp0..\..\artifacts\offline-bundle
if not exist "%BUNDLE_DIR%" (
  echo FAIL: Bundle not found at %BUNDLE_DIR%
  echo Run first (online): cd backend ^&^& python -m aerobim.tools.offline_bundle build
  goto :fail
)

if not exist "%BUNDLE_DIR%\install_offline.ps1" (
  echo FAIL: install_offline.ps1 not found in bundle.
  goto :fail
)

echo Running offline installer (PowerShell)...
powershell -ExecutionPolicy Bypass -File "%BUNDLE_DIR%\install_offline.ps1"
if errorlevel 1 goto :fail
goto :end

:: -----------------------------------------------------------------------
:: Хелперы
:: -----------------------------------------------------------------------
:no_py
echo FAIL: py launcher not found. Install CPython 3.12 from python.org.
goto :fail

:no_py312
echo FAIL: py -3.12 not found. Install CPython 3.12. Do not use Microsoft Store Python.
goto :fail

:fail
echo.
echo Demo setup FAILED. See messages above.
pause
exit /b 1

:end
echo.
echo Done.
pause
exit /b 0
