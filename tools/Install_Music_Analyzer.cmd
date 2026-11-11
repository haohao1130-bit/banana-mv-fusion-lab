@echo off
setlocal
cd /d "%~dp0.."
echo BANANAMV Fusion Lab - Installing CPU music structure analyzer
echo The installer uses a separate Python environment; H3 CUDA is unchanged.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_music_analyzer.ps1"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
  echo.
  echo Music analyzer installation failed. Check the music_structure_install.log in BananaMVFusionLab data.
) else (
  echo.
  echo Music analyzer ready. Restart the Fusion Lab application.
)
pause
exit /b %RESULT%
