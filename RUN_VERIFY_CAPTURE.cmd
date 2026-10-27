@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
echo ARGUS 0.4 - OPTIONAL INDEPENDENT POST-CAPTURE VERIFICATION
if not exist "ARGUS_04_HELDOUT_CAPTURE.zip" (
  echo Capture ZIP not found. Run RUN_HELDOUT_24.cmd first.
  pause
  exit /b 1
)
where py >nul 2>&1
if not errorlevel 1 (
   py -3 --version >nul 2>&1
   if not errorlevel 1 goto USE_PY
)
where python >nul 2>&1
if not errorlevel 1 goto USE_PYTHON
echo No Python installed. Upload ARGUS_04_HELDOUT_CAPTURE.zip here instead.
pause
exit /b 1
:USE_PY
py -3 -m pip install blosc2 numpy
if errorlevel 1 goto FAILED
py -3 tools\heldout_verify.py ARGUS_04_HELDOUT_CAPTURE.zip --out HELDOUT_ANALYSIS
goto DONE
:USE_PYTHON
python -m pip install blosc2 numpy
if errorlevel 1 goto FAILED
python tools\heldout_verify.py ARGUS_04_HELDOUT_CAPTURE.zip --out HELDOUT_ANALYSIS
goto DONE
:FAILED
echo Could not install optional decoder. Just upload capture ZIP to ChatGPT.
:DONE
pause
endlocal
