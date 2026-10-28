@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0"
if defined ARGUS_PYTHON goto CUSTOM
py -3 --version >nul 2>&1
if errorlevel 1 goto FALLBACK
set "ARGUS_LAUNCH=py -3"
goto RUN
:FALLBACK
set "ARGUS_LAUNCH=python"
goto RUN
:CUSTOM
set ARGUS_LAUNCH="%ARGUS_PYTHON%"
:RUN
if not defined ARGUS_CAPTURE set "ARGUS_CAPTURE=%CD%\ARGUS_04_HELDOUT_CAPTURE_NEW_%RANDOM%_%RANDOM%.zip"
%ARGUS_LAUNCH% tools\heldout_capture.py --root "%CD%" --output "%ARGUS_CAPTURE%"
set "ARGUS_EXIT=%ERRORLEVEL%"
echo Exit code: %ARGUS_EXIT%
popd
if not defined ARGUS_NO_PAUSE pause
exit /b %ARGUS_EXIT%
