@echo off
rem Clone/laptop preflight using backend\.venv. Not the jury CLI itself.
rem Explorer: double-click. PowerShell: .\check-launch.bat
setlocal
cd /d "%~dp0"
title AeroBIM launch check
chcp 65001 >nul
if not exist "backend\.venv\Scripts\python.exe" (
  echo backend\.venv not found. Double-click run-jury.bat, or from AeroBIM\backend:
  echo   py -3.12 -m venv .venv
  echo   .venv\Scripts\python.exe -m pip install -e ".[dev,raster]"
  echo Do not use system python -m aerobim.tools.check_local_launch
  pause
  exit /b 1
)
backend\.venv\Scripts\python.exe -m aerobim.tools.check_local_launch %*
set "EXITCODE=%ERRORLEVEL%"
echo.
echo JSON above: exit 0 even on warnings. Fatal problems print FATAL and exit 2.
pause
exit /b %EXITCODE%
