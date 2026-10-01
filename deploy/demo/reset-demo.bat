@echo off
rem ==========================================================================
rem AeroBIM -- Demo Reset Script (Windows)
rem Сбрасывает отчёты для чистого старта между демо-сессиями.
rem ==========================================================================
rem Использование:
rem   deploy\demo\reset-demo.bat           # сброс venv-режима
rem   deploy\demo\reset-demo.bat docker    # сброс Docker-режима
rem   deploy\demo\reset-demo.bat all       # полный сброс
rem ==========================================================================
setlocal
cd /d "%~dp0\..\.."
title AeroBIM Demo Reset
chcp 65001 >nul

set MODE=%~1
if "%MODE%"=="" set MODE=venv

if /i "%MODE%"=="venv"   goto :reset_venv
if /i "%MODE%"=="docker" goto :reset_docker
if /i "%MODE%"=="all"    goto :reset_all
echo FAIL: Unknown mode '%MODE%'. Use: venv docker all
pause
exit /b 1

:reset_venv
echo [AeroBIM reset] Clearing venv-mode reports (backend\var\reports)...
if exist "backend\var\reports\*" (
  del /q /s "backend\var\reports\*" >nul 2>&1
  for /d %%d in ("backend\var\reports\*") do rd /s /q "%%d" >nul 2>&1
  echo   OK  Cleared: backend\var\reports
) else (
  echo   --  Nothing to clear.
)
goto :done

:reset_docker
echo [AeroBIM reset] Resetting Docker-mode reports (volume aerobim_demo_reports)...
docker info >nul 2>&1 || (
  echo FAIL: Docker not running.
  pause
  exit /b 1
)
echo Stopping demo stack (if running)...
docker compose -f docker-compose.demo.yml down >nul 2>&1
echo Removing volume aerobim_demo_reports (if exists)...
docker volume rm aerobim_demo_reports >nul 2>&1
if errorlevel 1 (
  echo   --  Volume not found, nothing removed.
) else (
  echo   OK  Volume aerobim_demo_reports removed.
)
goto :done

:reset_all
call :reset_venv
call :reset_docker
goto :done

:done
echo.
echo Demo reset complete. Run setup-demo.bat to start a fresh demo.
pause
exit /b 0
