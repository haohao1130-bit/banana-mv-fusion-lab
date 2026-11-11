@echo off
setlocal
for %%I in ("%~dp0..") do set "FUSION_REPO=%%~fI"
git -C "%FUSION_REPO%" pull --ff-only
if errorlevel 1 goto failed
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_fusion_local.ps1"
if errorlevel 1 goto failed
exit /b 0
:failed
echo Fusion Lab did not start. Read the error above. Existing data was kept.
pause
exit /b 1
