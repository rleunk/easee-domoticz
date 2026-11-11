@echo off
set "PATCH=%~dp0"
set "TARGET=%USERPROFILE%\Projects\ha-sessy-economics\LXC249"
if not exist "%TARGET%" (
  echo Doelmap ontbreekt: %TARGET%
  exit /b 1
)
for %%D in (vendor sessy_economics_engine sessy_factuur_web) do (
  if exist "%PATCH%%%D" (
    echo Copy %%D ...
    xcopy "%PATCH%%%D\*" "%TARGET%\%%D\" /E /Y /I
  )
)
echo Klaar. Upload %TARGET% naar LXC /opt/sessy-economics-engine
pause
