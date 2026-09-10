@echo off
rem IT-mentor review shell (API + Vite). Not the jury CLI.
rem In Explorer: double-click. In PowerShell: .\start.bat
rem In cmd.exe type start.bat — the word "start" alone is a Windows builtin.
setlocal
cd /d "%~dp0"
title AeroBIM review shell
chcp 65001 >nul
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8

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
