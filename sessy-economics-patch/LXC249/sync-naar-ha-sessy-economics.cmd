@echo off
set "PATCH=%~dp0"
set "TARGET=%USERPROFILE%\Projects\ha-sessy-economics\LXC249"
if not exist "%TARGET%" (
  echo Doelmap ontbreekt: %TARGET%
  exit /b 1
)
for %%F in (
  vendor\sessy_economics\economics.py
  vendor\sessy_economics\pricing.py
  vendor\sessy_economics\p1_accounting.py
  vendor\sessy_economics\p1_registers.py
  vendor\sessy_economics\api.py
  sessy_economics_engine\runner.py
  sessy_factuur_web\pdf_parser.py
  sessy_factuur_web\p1_month.py
) do (
  if exist "%PATCH%%%F" (
    echo OK %%F
    copy /Y "%PATCH%%%F" "%TARGET%\%%F"
  ) else (
    echo ONTBREEKT in patch: %%F
  )
)
echo Klaar. Upload vendor + engine naar LXC als nodig.
pause
