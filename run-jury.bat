@echo off
rem One-click jury CLI from the clone root. Not the review shell. Not Next.js.
rem Explorer: double-click. PowerShell: .\run-jury.bat
rem Quotes around .[dev,raster] stay inside this file (PowerShell glob-safe).
setlocal
cd /d "%~dp0"
title AeroBIM jury CLI
chcp 65001 >nul
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
set PIP_DISABLE_PIP_VERSION_CHECK=1
echo AeroBIM jury CLI. Node is not required. customer_go false.
echo summary.passed=false on the fixture pack is expected.

cd /d "%~dp0backend"

if exist ".venv\Scripts\python.exe" goto :have_venv

where py >nul 2>&1
if errorlevel 1 goto :no_py_launcher
echo Creating backend\.venv with py -3.12 ...
py -3.12 -m venv .venv
if errorlevel 1 goto :nopy312
goto :have_venv

:no_py_launcher
echo py launcher not found. Trying python if it is CPython 3.12 ...
python -c "import sys; raise SystemExit(0 if sys.version_info[:2]==(3,12) else 1)"
if errorlevel 1 goto :nopy312
python -m venv .venv
if errorlevel 1 goto :nopy312

:have_venv
".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info[:2]==(3,12) else 1)"
if errorlevel 1 (
  echo backend\.venv is not CPython 3.12. Delete backend\.venv and re-run.
  echo Keep py -3.12; bare py may pick 3.13. Do not use the Microsoft Store stub.
  goto :fail
)

echo Installing ".[dev,raster]" into the venv ...
".venv\Scripts\python.exe" -m pip install -U pip
if errorlevel 1 goto :fail
".venv\Scripts\python.exe" -m pip install -e ".[dev,raster]"
if errorlevel 1 goto :fail
".venv\Scripts\python.exe" -m aerobim.tools.check_local_launch
if errorlevel 2 goto :fail
".venv\Scripts\python.exe" -m aerobim.tools.run_kt3_jury
set "EXITCODE=%ERRORLEVEL%"
echo.
echo Done. expected summary.passed=false. customer_go false.
if not "%EXITCODE%"=="0" goto :fail
pause
exit /b 0

:nopy312
echo Install CPython 3.12 from python.org, not Microsoft Store. Keep py -3.12.
goto :fail

:fail
echo run-jury.bat failed.
pause
exit /b 1
