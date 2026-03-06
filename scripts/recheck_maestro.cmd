@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0recheck_maestro.ps1" %*
exit /b %ERRORLEVEL%
