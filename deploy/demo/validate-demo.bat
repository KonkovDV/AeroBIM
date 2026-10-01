@echo off
rem ==========================================================================
rem AeroBIM -- Demo Validation / Smoke Test (Windows)
rem Проверяет ключевые эндпойнты запущенного демо.
rem ==========================================================================
rem Использование:
rem   deploy\demo\validate-demo.bat
rem ==========================================================================
setlocal
cd /d "%~dp0\..\.."
title AeroBIM Demo Validate
chcp 65001 >nul

set BASE_URL=http://127.0.0.1:8080
set FAILURES=0

echo.
echo ============================================================
echo   AeroBIM Demo Validation  --  %BASE_URL%
echo ============================================================
echo.

:: Используем curl если есть, иначе PowerShell Invoke-WebRequest
where curl >nul 2>&1
if not errorlevel 1 (
  set HTTP_CLIENT=curl
) else (
  set HTTP_CLIENT=ps
)

:check_health
echo Checking /health ...
if "%HTTP_CLIENT%"=="curl" (
  curl -sf --max-time 5 "%BASE_URL%/health" >nul 2>&1
  if errorlevel 1 (
    echo   FAIL  /health -- not reachable
    set /a FAILURES+=1
  ) else (
    echo   PASS  /health
  )
) else (
  powershell -Command "try { $r=(Invoke-WebRequest -Uri '%BASE_URL%/health' -UseBasicParsing -TimeoutSec 5); if($r.StatusCode -eq 200){Write-Host '  PASS  /health'}else{Write-Host '  FAIL  /health HTTP '+$r.StatusCode; exit 1} } catch { Write-Host '  FAIL  /health not reachable'; exit 1 }"
  if errorlevel 1 set /a FAILURES+=1
)

:check_caps
echo Checking /v1/system/capabilities ...
if "%HTTP_CLIENT%"=="curl" (
  curl -sf --max-time 5 "%BASE_URL%/v1/system/capabilities" >nul 2>&1
  if errorlevel 1 (
    echo   FAIL  /v1/system/capabilities
    set /a FAILURES+=1
  ) else (
    echo   PASS  /v1/system/capabilities
  )
) else (
  powershell -Command "try { $r=(Invoke-WebRequest -Uri '%BASE_URL%/v1/system/capabilities' -UseBasicParsing -TimeoutSec 5); if($r.StatusCode -eq 200){Write-Host '  PASS  /v1/system/capabilities'}else{exit 1} } catch { Write-Host '  FAIL  /v1/system/capabilities'; exit 1 }"
  if errorlevel 1 set /a FAILURES+=1
)

:check_reports
echo Checking /v1/reports ...
if "%HTTP_CLIENT%"=="curl" (
  curl -sf --max-time 5 "%BASE_URL%/v1/reports" >nul 2>&1
  if errorlevel 1 (
    echo   FAIL  /v1/reports
    set /a FAILURES+=1
  ) else (
    echo   PASS  /v1/reports
  )
) else (
  powershell -Command "try { $r=(Invoke-WebRequest -Uri '%BASE_URL%/v1/reports' -UseBasicParsing -TimeoutSec 5); if($r.StatusCode -eq 200){Write-Host '  PASS  /v1/reports'}else{exit 1} } catch { Write-Host '  FAIL  /v1/reports'; exit 1 }"
  if errorlevel 1 set /a FAILURES+=1
)

echo.
if %FAILURES%==0 (
  echo All checks PASSED. Demo API is healthy.
) else (
  echo %FAILURES% check(s) FAILED. See messages above.
)
echo.
pause
if %FAILURES%==0 (exit /b 0) else (exit /b 1)
