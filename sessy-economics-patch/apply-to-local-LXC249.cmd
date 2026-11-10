@echo off
REM Dubbelklik of run vanuit easee-domoticz — geen ExecutionPolicy nodig.
cd /d "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0apply-to-local-LXC249.ps1"
pause
