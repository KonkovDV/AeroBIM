@echo off
rem IT-mentor review shell (API + Vite). Not the jury CLI.
rem PowerShell:  .\start.bat     (the leading .\ is required)
rem Do not type: start           (PowerShell alias for Start-Process)
rem Do not type: start.bat       (PowerShell does not run cwd .bat without .\)
rem Explorer: double-click. CMD: start.bat  (CMD builtin "start" is different)
setlocal
cd /d "%~dp0"
title AeroBIM review shell
chcp 65001 >nul
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
echo AeroBIM review shell. PowerShell: .\start.bat  (not "start")

if not exist "backend\.venv\Scripts\python.exe" (
  echo backend\.venv not found. From AeroBIM\backend:
  echo   py -3.12 -m venv .venv
  echo   pip install -e ".[dev,raster]"
  echo Not the jury CLI. customer_go false.
  pause
  exit /b 1
)

backend\.venv\Scripts\python.exe -m aerobim.tools.run_it_mentor_stand %*
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo start.bat failed, exit %EXITCODE%
  pause
)
exit /b %EXITCODE%
