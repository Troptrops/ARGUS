@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
echo =========================================================
echo ARGUS 0.4 - FROZEN 24-CELL HELD-OUT AUDIT
 echo No Colab. No Codex. Python built-in downloader only.
echo Full original prediction volume is NOT downloaded.
echo =========================================================
where py >nul 2>&1
if not errorlevel 1 (
    py -3 --version >nul 2>&1
    if not errorlevel 1 goto USING_PY
)
where python >nul 2>&1
if not errorlevel 1 goto USING_PYTHON
echo ERROR: Python 3 not found. No program started.
pause
exit /b 1
:USING_PY
py -3 -u tools\heldout_capture.py --root "%CD%" --output "%CD%\ARGUS_04_HELDOUT_CAPTURE.zip"
goto FINISH
:USING_PYTHON
python -u tools\heldout_capture.py --root "%CD%" --output "%CD%\ARGUS_04_HELDOUT_CAPTURE.zip"
:FINISH
echo.
echo Send ARGUS_04_HELDOUT_CAPTURE.zip here even if status was PARTIAL or ERROR.
pause
endlocal
