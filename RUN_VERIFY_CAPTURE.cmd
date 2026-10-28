@echo off
setlocal EnableExtensions DisableDelayedExpansion
if not "%~1"=="" set "ARGUS_CAPTURE=%~f1"
pushd "%~dp0"
if not defined ARGUS_CAPTURE set "ARGUS_CAPTURE=%CD%\ARGUS_04_HELDOUT_CAPTURE.zip"
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
%ARGUS_LAUNCH% tools\heldout_verify.py "%ARGUS_CAPTURE%" --out "%CD%\ROWWISE_REPLAY_%RANDOM%_%RANDOM%"
set "ARGUS_EXIT=%ERRORLEVEL%"
echo Exit code: %ARGUS_EXIT%
popd
if not defined ARGUS_NO_PAUSE pause
exit /b %ARGUS_EXIT%
